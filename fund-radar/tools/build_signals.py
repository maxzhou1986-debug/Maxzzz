#!/usr/bin/env python3
import json, os, time, urllib.parse, urllib.request
from datetime import datetime, timezone, timedelta
TZ=timezone(timedelta(hours=8));OUT=os.path.join(os.path.dirname(os.path.dirname(__file__)),'data')
SPOT='https://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/Market_Center.getHQNodeData';KLINE='https://quotes.sina.cn/cn/api/json_v2.php/CN_MarketDataService.getKLineData'
HEAD={'User-Agent':'Mozilla/5.0 AppleWebKit/537.36 Chrome/140 Safari/537.36','Referer':'https://finance.sina.com.cn/','Accept':'application/json,text/plain,*/*'}
def raw(url,timeout=15):
 req=urllib.request.Request(url,headers=HEAD)
 with urllib.request.urlopen(req,timeout=timeout) as r:return r.read().decode('utf-8','ignore').strip()
def n(v,d=0.0):
 try:return d if v in (None,'','-') else float(v)
 except:return d
def clamp(v,a=0,b=99):return max(a,min(b,v))
def norm(a):
 out=[];seen=set()
 for x in a if isinstance(a,list) else []:
  c=str(x.get('code') or '').zfill(6)
  if not c or c in seen:continue
  seen.add(c);out.append({'code':c,'name':str(x.get('name') or ''),'pct':n(x.get('changepercent')),'amount':n(x.get('amount')),'turn':n(x.get('turnoverratio')),'vr':0,'flow':0,'flowPct':0})
 return out
def spot():
 # One request for the most liquid names; fallback to three 100-name pages. This avoids 50+ requests every refresh.
 try:
  q=urllib.parse.urlencode({'page':1,'num':300,'sort':'amount','asc':0,'node':'hs_a','_s_r_a':'page'})
  a=norm(json.loads(raw(SPOT+'?'+q)))
  if len(a)>=80:return a
 except Exception:pass
 out=[]
 for page in range(1,4):
  try:
   q=urllib.parse.urlencode({'page':page,'num':100,'sort':'amount','asc':0,'node':'hs_a','_s_r_a':'page'})
   out+=norm(json.loads(raw(SPOT+'?'+q)))
  except Exception:break
 return list({x['code']:x for x in out}.values())
def prefix(c):
 if str(c).startswith(('5','6','7','9')):return 'sh'+str(c)
 if str(c).startswith(('4','8')):return 'bj'+str(c)
 return 'sz'+str(c)
def kline(c):
 q=urllib.parse.urlencode({'symbol':prefix(c),'scale':240,'ma':'no','datalen':40})
 try:
  a=json.loads(raw(KLINE+'?'+q,8))
  if not isinstance(a,list):return []
  return [{'d':z.get('day',''),'c':n(z.get('close')),'h':n(z.get('high')),'l':n(z.get('low')),'v':n(z.get('volume'))} for z in a if n(z.get('close'))>0]
 except Exception:return []
def rsi14(c):
 if len(c)<15:return None
 g=l=0.0
 for i in range(len(c)-14,len(c)):
  d=c[i]-c[i-1];g+=max(d,0);l+=max(-d,0)
 return 100.0 if l==0 else 100-100/(1+g/l)
def rebound_eval(x,k):
 if len(k)<21:return None
 c=[z['c'] for z in k];v=[z['v'] for z in k];last=k[-1];prev=k[-2];w=k[-20:];r=rsi14(c);hi=max(z['h'] for z in w);lo=min(z['l'] for z in w)
 if r is None or hi<=0 or lo<=0:return None
 draw=(last['c']/hi-1)*100;near=(last['c']/lo-1)*100;ret5=(last['c']/c[-6]-1)*100;v3=sum(v[-3:])/3;v20=sum(v[-20:])/20;vl=v3/(v20 or 1);s=32
 if 22<=r<=36:s+=25
 elif 36<r<=44:s+=16
 elif r<22:s+=8
 elif r>52:s-=12
 dd=-draw
 if 10<=dd<=28:s+=22
 elif dd>=6:s+=12
 elif dd>28:s+=8
 if near<=5:s+=11
 elif near<=10:s+=6
 if -7<=ret5<=3:s+=10
 elif ret5>7:s-=16
 if .75<=vl<=2.4:s+=9
 elif vl>3.8:s-=12
 if -3<=x['pct']<=3.5:s+=8
 elif x['pct']>5:s-=20
 if last['c']>prev['c']:s+=7
 if len(k)>=3 and last['c']>=prev['c']>=k[-3]['c']:s+=5
 return {**x,'rebound':round(clamp(s)),'rsi':r,'draw':draw,'nearLow':near,'ret5':ret5,'volLift':vl,'turning':last['c']>prev['c']}
def build_score(x):
 s=38
 if -.8<=x['pct']<=3.2:s+=22
 elif -2.5<=x['pct']<-.8:s+=10
 elif x['pct']>5:s-=20
 if .5<=x['turn']<=8:s+=16
 elif 8<x['turn']<=15:s+=9
 elif x['turn']>20:s-=8
 if x['amount']>=2e9:s+=16
 elif x['amount']>=8e8:s+=13
 elif x['amount']>=3e8:s+=10
 elif x['amount']>=1e8:s+=6
 if 0<=x['pct']<=2.5:s+=8
 return round(clamp(s))
def main():
 os.makedirs(OUT,exist_ok=True);rows=spot();valid=[x for x in rows if x['name'] and x['amount']>0 and 'ST' not in x['name'] and '退' not in x['name']]
 if len(valid)<60:raise SystemExit('A-share liquid-pool coverage too low: '+str(len(valid)))
 active=sorted(valid,key=lambda x:x['amount'],reverse=True)[:220];builds=[]
 for x in active:
  s=build_score(x)
  if s>=64:builds.append({**x,'build':s,'phase':'温和增强' if s>=82 else '持续观察' if s>=74 else '早期观察'})
 builds=sorted(builds,key=lambda x:(x['build'],x['amount']),reverse=True)[:20]
 pool=[x for x in active if -9.5<x['pct']<4.5][:40];rebounds=[];kvalid=0
 for i,x in enumerate(pool):
  k=kline(x['code'])
  if len(k)>=21:
   kvalid+=1;z=rebound_eval(x,k)
   if z and z['rebound']>=58:rebounds.append(z)
  if i and i%10==0:time.sleep(.1)
 rebounds=sorted(rebounds,key=lambda x:(x['rebound'],x['amount']),reverse=True)[:20]
 d={'schema':3,'market':'A','generatedAt':datetime.now(TZ).isoformat(timespec='seconds'),'source':'Sina liquid-pool spot + Sina daily K-line','coverage':len(valid),'sample':len(active),'klineValid':kvalid,'build':builds,'rebound':rebounds,'note':'服务器实盘高流动性样本筛选；建仓为量价观察信号，不等同机构持仓证明；资金流字段缺失时不伪造。'}
 with open(os.path.join(OUT,'signals-A.json'),'w',encoding='utf-8') as f:json.dump(d,f,ensure_ascii=False,separators=(',',':'))
 print('signals A liquid pool',len(valid),'build',len(builds),'rebound',len(rebounds),'kline',kvalid)
if __name__=='__main__':main()
