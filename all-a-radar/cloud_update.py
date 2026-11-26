"""GitHub Actions updater: public, read-only Tonghuashun feeds; no OpenD access."""
import json,gzip,time,urllib.request,unicodedata
from pathlib import Path
from datetime import datetime,timezone,timedelta
ROOT=Path(__file__).resolve().parent
def csi_history():
 url='https://push2his.eastmoney.com/api/qt/stock/trends2/get?secid=1.000985&fields1=f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f11&fields2=f51,f52,f53,f54,f55,f56,f57,f58&ndays=5&iscr=0'
 for attempt in range(3):
  try:
   req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0','Referer':'https://quote.eastmoney.com/'})
   d=json.load(urllib.request.urlopen(req,timeout=20))['data']
   assert d['code']=='000985' and d['name']=='中证全指','中证全指标识不匹配'
   rows=[]
   for s in d['trends']:
    a=s.split(',');c=float(a[2])
    if c>0:rows.append({'t':a[0]+':00','c':c})
   assert rows
   return rows
  except Exception:
   if attempt==2:raise
   time.sleep(2)
def csi_daily():
 req=urllib.request.Request('https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh000985,day,,,160,qfq',headers={'User-Agent':'Mozilla/5.0'})
 d=json.load(urllib.request.urlopen(req,timeout=20))['data']['sh000985']
 assert '中证全指' in d['qt']['sh000985'][1]
 return [{'t':r[0],'o':float(r[1]),'c':float(r[2]),'h':float(r[3]),'l':float(r[4])} for r in d['day']]
def get(path):
 for attempt in range(4):
  try:
   req=urllib.request.Request('https://d.10jqka.com.cn/'+('v6/' if attempt%2==0 else 'v4/')+path,headers={'Referer':'https://q.10jqka.com.cn/','User-Agent':'Mozilla/5.0'})
   raw=urllib.request.urlopen(req,timeout=25).read().decode()
   return json.loads(raw[raw.index('(')+1:raw.rindex(')')])
  except Exception:
   if attempt==3:raise
   time.sleep(2**attempt)
def minutes(code,expected):
 d=get('time/'+code+'/last.js')[code]
 assert expected in unicodedata.normalize('NFKC',d['name']),d['name']
 date=datetime.strptime(d['date'],'%Y%m%d').date().isoformat()
 rows=[]
 for s in d['data'].split(';'):
  a=s.split(',')
  if len(a)<3 or not a[1] or not a[2]:continue
  # THS emits a duplicate 13:00 point with the same amount as 13:01. It is not a trading minute.
  if not ('0930'<=a[0]<='1130' or '1301'<=a[0]<='1500'):continue
  r={'t':date+' '+a[0][:2]+':'+a[0][2:]+':00','c':float(a[1]),'a':float(a[2])}
  assert r['c']>0 and r['a']>=0
  rows.append(r)
 assert rows
 return rows
def merge(old,new,days=40):
 d={r['t']:r for r in old}
 for r in new:d[r['t']]=r
 dates=sorted({t[:10] for t in d})[-days:]
 return [d[t] for t in sorted(d) if t[:10] in dates]
def main():
 p=ROOT/'snapshot.json.gz'
 d=json.loads(gzip.decompress(p.read_bytes()))
 errors=[]
 try:
  d['series']['csi']=merge(d['series'].get('csi',[]),csi_history())
  d['csiSource']='中证全指000985：初始OpenD历史，新增及近5日由东方财富同一指数分钟线覆盖；日K为腾讯行情原始OHLC'
 except Exception as e:errors.append('中证全指历史更新失败：'+str(e))
 try:d['daily']['csi']=csi_daily()
 except Exception as e:errors.append('中证全指日K更新失败：'+str(e))
 try:
  th=minutes('bk_883957','同花顺全A')
  d['series']['ths']=merge(d['series'].get('ths',[]),th)
  k=get('line/bk_883957/01/last.js');daily=[]
  assert '同花顺全A' in k['name']
  for s in k['data'].split(';'):
   a=s.split(',')
   if len(a)>=7:daily.append(dict(t=datetime.strptime(a[0],'%Y%m%d').date().isoformat(),o=float(a[1]),h=float(a[2]),l=float(a[3]),c=float(a[4]),a=float(a[6])))
  d['daily']['ths']=daily
 except Exception as e:errors.append('同花顺指数更新失败：'+str(e))
 try:
  sh=minutes('hs_1A0002','A股指数');sz=minutes('hs_399107','深证A指')
  assert sh[-1]['t'][:10]==sz[-1]['t'][:10],'沪深日期不一致'
  left={r['t']:r for r in sh};right={r['t']:r for r in sz}
  common=sorted(left.keys()&right.keys());assert common,'无共同分钟'
  rows=[{'t':t,'a':left[t]['a']+right[t]['a']} for t in common]
  d['amount']=merge(d['amount'],rows)
  d['amountSource']='同花顺官方沪市A股+深证A指逐分钟成交额（已排除13:00重复点）；历史初始来自OpenD'
 except Exception as e:errors.append('沪深成交额更新失败：'+str(e))
 d.update(busy=False,errors=errors,updated=datetime.now(timezone(timedelta(hours=8))).isoformat(),cloud=True)
 raw=json.dumps(d,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode()
 p.write_bytes(gzip.compress(raw,mtime=0))
 print(json.dumps({'updated':d['updated'],'thsLast':d['series']['ths'][-1]['t'],'amountLast':d['amount'][-1]['t'],'errors':errors},ensure_ascii=False))
 if errors:raise SystemExit(1)
if __name__=='__main__':main()