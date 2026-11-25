"""Nasdaq prices with explicitly estimated QQQ dollar turnover."""
import json,gzip,time,math,urllib.request
from pathlib import Path
from datetime import datetime,timezone,timedelta
from zoneinfo import ZoneInfo
ROOT=Path(__file__).resolve().parent
NY=ZoneInfo('America/New_York')
def fetch(interval,symbol='^IXIC'):
 query=('interval=5m&period1='+str(int(time.time()-58*86400))+'&period2='+str(int(time.time()))) if interval=='5m' else 'interval=1d&range=6mo'
 for attempt in range(4):
  host=['query1','query2'][attempt%2]
  try:
   from urllib.parse import quote
   u='https://'+host+'.finance.yahoo.com/v8/finance/chart/'+quote(symbol,safe='')+'?'+query+'&includePrePost=false'
   req=urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0'})
   payload=json.load(urllib.request.urlopen(req,timeout=30))
   if payload['chart']['error']:raise ValueError(payload['chart']['error'])
   d=payload['chart']['result'][0]
   assert d['meta']['symbol']==symbol
   assert d['meta']['exchangeTimezoneName']=='America/New_York'
   q=d['indicators']['quote'][0];rows=[]
   for i,stamp in enumerate(d['timestamp']):
    t=datetime.fromtimestamp(stamp,NY)
    vals=[q[k][i] for k in ['open','high','low','close','volume']]
    if any(v is None or not math.isfinite(v) for v in vals):continue
    o,h,l,c,v=vals
    if min(o,h,l,c)<=0 or v<0 or not l<=min(o,c)<=max(o,c)<=h:continue
    if interval=='5m':
     if not ('09:30'<=t.strftime('%H:%M')<'16:00'):continue
     # Yahoo may append a zero-volume closing marker (including early-close sessions).
     if v==0 and (i==len(d['timestamp'])-1 or datetime.fromtimestamp(d['timestamp'][i+1],NY).date()!=t.date()):continue
    rows.append(dict(t=t.strftime('%Y-%m-%d %H:%M:%S') if interval=='5m' else t.date().isoformat(),o=o,h=h,l=l,c=c,a=v))
   if not rows:raise ValueError('No valid bars')
   return rows,d['meta']
  except Exception:
   if attempt==3:raise
   time.sleep(2**attempt)
def main():
 p=ROOT/'snapshot.json.gz';d={}
 if p.exists():d=json.loads(gzip.decompress(p.read_bytes()))
 stamp=datetime.now(timezone.utc).isoformat()
 try:
  bars,meta=fetch('5m');daily,_=fetch('1d');qqq,qqq_meta=fetch('5m','QQQ')
  assert qqq_meta['currency']=='USD'
  days=sorted({r['t'][:10] for r in bars})[-25:]
  bars=[r for r in bars if r['t'][:10] in days]
  assert len(days)>=20,'Less than 20 trading days returned'
  amount=[{'t':r['t'],'a':((r['o']+r['h']+r['l']+r['c'])/4)*r['a'],'v':r['a'],'p':(r['o']+r['h']+r['l']+r['c'])/4} for r in qqq if r['t'][:10] in days]
  assert len({r['t'][:10] for r in amount})>=20,'QQQ history incomplete'
  d={'series':{'nasdaq':bars},'daily':{'nasdaq':daily},'amount':amount,'updated':stamp,'busy':False,'errors':[], 'interval':'5m','timezone':'America/New_York','metric':'qqq_estimated_turnover','currency':'USD','amountSymbol':'QQQ','formula':'(open + high + low + close) / 4 * QQQ volume per 5-minute bar','source':'Yahoo Finance ^IXIC prices + QQQ OHLCV', 'quoteTime':datetime.fromtimestamp(meta['regularMarketTime'],NY).isoformat(),'qqqQuoteTime':datetime.fromtimestamp(qqq_meta['regularMarketTime'],NY).isoformat()}
 except Exception as e:
  if not d:raise
  if d.get('metric')!='qqq_estimated_turnover':d['amount']=[]
  d.update(errors=['云端取数失败，保留旧行情：'+str(e)],lastAttempt=stamp,busy=False)
 raw=json.dumps(d,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode()
 tmp=p.with_suffix('.tmp');tmp.write_bytes(gzip.compress(raw,mtime=0));tmp.replace(p)
 print(json.dumps({'lastBar':d['series']['nasdaq'][-1]['t'],'days':len({r['t'][:10] for r in d['series']['nasdaq']}),'updated':d['updated'],'errors':d['errors']},ensure_ascii=False))
 if d['errors']:raise SystemExit(1)
if __name__=='__main__':main()