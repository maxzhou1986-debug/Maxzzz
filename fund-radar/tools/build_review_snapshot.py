#!/usr/bin/env python3
import json, math, os, time, urllib.parse, urllib.request
from datetime import datetime, timezone, timedelta
BASE='/api/qt/clist/get'; UL='/api/qt/ulist.np/get'; KH='/api/qt/stock/kline/get'
HOSTS=['https://82.push2.eastmoney.com','https://20.push2.eastmoney.com','https://push2.eastmoney.com']
HISHOST='https://push2his.eastmoney.com'; SINA='https://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/Market_Center.getHQNodeData'
OUT=os.path.join(os.path.dirname(os.path.dirname(__file__)),'data'); TZ=timezone(timedelta(hours=8)); UT='bd1d9ddb04089700cf9c27f6f7426281'
HEAD={'User-Agent':'Mozilla/5.0 AppleWebKit/537.36 Chrome/140 Safari/537.36','Referer':'https://vip.stock.finance.sina.com.cn/mkt/','Accept':'application/json,text/plain,*/*'}
def raw(url,headers=None,timeout=20):
 req=urllib.request.Request(url,headers=headers or HEAD)
 with urllib.request.urlopen(req,timeout=timeout) as r:return r.read().decode('utf-8','ignore').strip()
def getpath(path,p):
 q=urllib.parse.urlencode(p); err=[]
 for h in HOSTS:
  try:
   s=raw(h+path+'?'+q); s=s[s.find('(')+1:s.rfind(')')] if s.startswith(('jQuery','callback')) and '(' in s else s
   return json.loads(s)
  except Exception as e:err.append(str(e));time.sleep(.3)
 raise RuntimeError(' | '.join(err[-3:]))
def clist(fs,fields,pz=200):
 out=[];seen=set();total=0
 for pn in range(1,60):
  d=getpath(BASE,{'pn':pn,'pz':pz,'po':1,'np':1,'fltt':2,'invt':2,'fid':'f12','fs':fs,'fields':fields,'ut':UT}); z=(d or {}).get('data') or {}; a=z.get('diff') or []
  if isinstance(a,dict):a=list(a.values())
  total=total or int(z.get('total') or 0); add=0
  for x in a:
   k=f"{x.get('f13','')}:{x.get('f12','')}"
   if x.get('f12') and k not in seen:seen.add(k);out.append(x);add+=1
  if (total and len(out)>=total) or not a or not add:break
 return out,total
def n(v,d=0.0):
 try:return d if v in (None,'','-') else float(v)
 except:return d
def row(code,name,pct,amt,turn=0,flow=0,vr=0,flowpct=0):return {'code':str(code or ''),'name':str(name or ''),'pct':n(pct),'amount':n(amt),'turn':n(turn),'flow':n(flow),'vr':n(vr),'flowPct':n(flowpct)}
def compact(x):return row(x.get('f12'),x.get('f14'),x.get('f3'),x.get('f6'),x.get('f8'),x.get('f62'),x.get('f10'),x.get('f184'))
def sina():
 out=[];seen=set()
 for page in range(1,90):
  u=SINA+'?'+urllib.parse.urlencode({'page':page,'num':100,'sort':'symbol','asc':1,'node':'hs_a','_s_r_a':'page'}); s=raw(u,{'User-Agent':HEAD['User-Agent'],'Referer':'https://vip.stock.finance.sina.com.cn/mkt/#hs_a'}); a=json.loads(s) if s and s not in ('null','[]') else []
  if not isinstance(a,list) or not a:break
  for x in a:
   c=str(x.get('code') or '').zfill(6)
   if c and c not in seen:seen.add(c);out.append(row(c,x.get('name'),x.get('changepercent'),x.get('amount'),x.get('turnoverratio')))
  if len(a)<100:break
 return out
def secid(c):return ('1.' if str(c).startswith(('5','6','7','9')) else '0.')+str(c)
def enrich(pool):
 ids=','.join(secid(x['code']) for x in pool)
 try:
  d=getpath(UL,{'fltt':2,'invt':2,'secids':ids,'fields':'f12,f14,f3,f6,f8,f10,f62,f184,f124','ut':UT}); a=((d or {}).get('data') or {}).get('diff') or []
  if isinstance(a,dict):a=list(a.values())
  em={str(x.get('f12')):compact(x) for x in a}
  return [{**x,**{k:v for k,v in em.get(x['code'],{}).items() if k not in ('code','name') or v}} for x in pool]
 except Exception as e:print('WARN enrich',repr(e));return pool
def kline(c):
 p={'secid':secid(c),'fields1':'f1,f2,f3','fields2':'f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61','klt':101,'fqt':1,'end':'20500101','lmt':35,'ut':'fa5fd1943c7b386f172d6893dbbd1d0c'}
 try:
  d=json.loads(raw(HISHOST+KH+'?'+urllib.parse.urlencode(p),timeout=12)); a=((d or {}).get('data') or {}).get('klines') or []
  return [{'c':n(z.split(',')[2]),'h':n(z.split(',')[3]),'l':n(z.split(',')[4]),'v':n(z.split(',')[5]),'pct':n(z.split(',')[8])} for z in a]
 except:return []
def rsi14(c):
 if len(c)<15:return 50
 g=l=0
 for i in range(len(c)-14,len(c)):
  d=c[i]-c[i-1];g+=max(d,0);l+=max(-d,0)
 return 100 if l==0 else 100-100/(1+g/l)
def rebound_eval(x,k):
 if len(k)<21:return None
 c=[z['c'] for z in k]; v=[z['v'] for z in k]; last=k[-1];prev=k[-2];w=k[-20:];r=rsi14(c);hi=max(z['h'] for z in w);lo=min(z['l'] for z in w);draw=(last['c']/hi-1)*100;near=(last['c']/lo-1)*100;ret5=(last['c']/c[-6]-1)*100;vl=(sum(v[-3:])/3)/(sum(v[-20:])/20 or 1)
 s=34;s+=24 if 24<=r<=36 else 15 if 36<r<=43 else 9 if r<24 else -12 if r>50 else 0;dd=-draw;s+=20 if 10<=dd<=26 else 11 if dd>=6 else 8 if dd>26 else 0;s+=10 if near<=5 else 6 if near<=10 else 0;s+=9 if -6<=ret5<=3 else -15 if ret5>6 else 0;s+=9 if .85<=vl<=2.2 else -12 if vl>3.5 else 0;s+=8 if -2<=x['pct']<=3.2 else -22 if x['pct']>5 else 0;s+=6 if x.get('flowPct',0)>0 else -6 if x.get('flowPct',0)<-5 else 0;s+=6 if last['c']>prev['c'] else 0;s-=18 if last['pct']<-5 else 0
 return {**x,'rebound':max(0,min(99,round(s))),'rsi':r,'draw':draw,'nearLow':near,'ret5':ret5,'volLift':vl,'turning':last['c']>prev['c']}
def signals(valid):
 active=sorted([x for x in valid if x['amount']>8e7 and 'ST' not in x['name'] and '退' not in x['name']],key=lambda x:x['amount'],reverse=True)[:140]; active=enrich(active)
 builds=[]
 for x in active:
  s=45
  if -.8<=x['pct']<=3.5:s+=16
  elif x['pct']>6:s-=20
  if .7<=x['turn']<=12:s+=10
  if .8<=x.get('vr',0)<=2.5:s+=10
  if x.get('flow',0)>0:s+=14
  elif x.get('flow',0)<-2e8:s-=12
  s+=min(10,max(0,math.log10(max(x['amount'],1))-8)*5);s=max(0,min(99,round(s)))
  if s>=62:builds.append({**x,'build':s,'phase':'温和增强' if s>=80 else '早期观察'})
 builds=sorted(builds,key=lambda x:x['build'],reverse=True)[:20]
 rp=[x for x in active if -7<x['pct']<4][:36]; rebounds=[]
 for x in rp:
  z=rebound_eval(x,kline(x['code']))
  if z and z['rebound']>=60:rebounds.append(z)
 rebounds=sorted(rebounds,key=lambda x:x['rebound'],reverse=True)[:20]
 return {'schema':1,'market':'A','generatedAt':datetime.now(TZ).isoformat(timespec='seconds'),'build':builds,'rebound':rebounds,'sample':len(active),'note':'服务器实盘量价筛选；建仓为观察信号，不等同机构持仓证明'}
def build_a():
 rows=sina();valid=[x for x in rows if x['name'] and x['amount']>0]
 if len(valid)<1000:raise RuntimeError('A coverage low')
 fields='f12,f13,f14,f3,f6,f8,f10,f62,f184,f100,f124';sectors=[];indices=[];bt=0
 try:boards,bt=clist('m:90+t:2',fields);sectors=[compact(x) for x in boards if x.get('f14') and x.get('f3') not in (None,'-')]
 except Exception as e:print('WARN sectors',repr(e))
 try:
  d=getpath(UL,{'fltt':2,'invt':2,'secids':'1.000001,0.399001,0.399006','fields':'f12,f14,f3,f6,f124','ut':UT});a=((d or {}).get('data') or {}).get('diff') or [];a=list(a.values()) if isinstance(a,dict) else a;indices=[compact(x) for x in a]
 except:pass
 ts=max([int(n(x.get('f124'))) for x in a],default=0) if 'a' in locals() else 0; day=datetime.fromtimestamp(ts,TZ).strftime('%Y-%m-%d') if ts else datetime.now(TZ).strftime('%Y-%m-%d')
 up=sum(x['pct']>0 for x in valid);down=sum(x['pct']<0 for x in valid);flat=len(valid)-up-down;ratio=up/len(valid);emotion='高潮' if ratio>=.75 else '偏强' if ratio>=.60 else '退潮' if ratio<=.25 else '偏弱' if ratio<=.40 else '分歧';liq=sorted(valid,key=lambda x:x['amount'],reverse=True)[:240];leaders=sorted([x for x in liq if x['pct']>0],key=lambda x:x['pct']*2+math.log10(max(1,x['amount'])),reverse=True)[:10]
 return {'schema':6,'market':'A','date':day,'generatedAt':datetime.now(TZ).isoformat(timespec='seconds'),'source':'Sina full-market + Eastmoney sectors','coverage':len(valid),'total':len(rows),'complete':True,'breadth':{'up':up,'down':down,'flat':flat,'amount':sum(x['amount'] for x in valid),'count':len(valid)},'indices':indices,'strong':sorted(sectors,key=lambda x:x['pct'],reverse=True)[:5],'weak':sorted(sectors,key=lambda x:x['pct'])[:5],'inflow':sorted([x for x in sectors if x['flow']>0],key=lambda x:x['flow'],reverse=True)[:5],'outflow':sorted([x for x in sectors if x['flow']<0],key=lambda x:x['flow'])[:5],'leaders':leaders,'emotion':emotion,'sectorCount':len(sectors),'sectorTotal':bt or len(sectors)},valid
def build_hk():
 fields='f12,f13,f14,f3,f6,f8,f10,f62,f184,f100,f124';stocks,total=clist('m:128+t:3,m:128+t:4,m:128+t:1,m:128+t:2',fields);valid=[x for x in stocks if x.get('f14') and n(x.get('f6'))>0];boards,bt=clist('m:124',fields);secs=[compact(x) for x in boards if x.get('f14')];up=sum(n(x.get('f3'))>0 for x in valid);down=sum(n(x.get('f3'))<0 for x in valid);ratio=up/max(1,len(valid));emo='偏强' if ratio>=.6 else '偏弱' if ratio<=.4 else '分歧';liq=sorted(valid,key=lambda x:n(x.get('f6')),reverse=True)[:180]
 return {'schema':6,'market':'HK','date':datetime.now(TZ).strftime('%Y-%m-%d'),'generatedAt':datetime.now(TZ).isoformat(timespec='seconds'),'source':'Eastmoney','coverage':len(valid),'total':total or len(stocks),'complete':len(valid)>=100,'breadth':{'up':up,'down':down,'flat':len(valid)-up-down,'amount':sum(n(x.get('f6')) for x in valid),'count':len(valid)},'indices':[],'strong':sorted(secs,key=lambda x:x['pct'],reverse=True)[:5],'weak':sorted(secs,key=lambda x:x['pct'])[:5],'inflow':sorted([x for x in secs if x['flow']>0],key=lambda x:x['flow'],reverse=True)[:5],'outflow':sorted([x for x in secs if x['flow']<0],key=lambda x:x['flow'])[:5],'leaders':[compact(x) for x in liq[:10]],'emotion':emo,'sectorCount':len(secs),'sectorTotal':bt or len(secs)}
def save(name,d):
 with open(os.path.join(OUT,name),'w',encoding='utf-8') as f:json.dump(d,f,ensure_ascii=False,separators=(',',':'))
def main():
 os.makedirs(OUT,exist_ok=True);ok=0
 try:
  a,valid=build_a();save('review-A.json',a);save('signals-A.json',signals(valid));print('A',a['coverage'],'signals generated');ok+=1
 except Exception as e:print('ERROR A',repr(e))
 try:h=build_hk();save('review-HK.json',h);print('HK',h['coverage']);ok+=1
 except Exception as e:print('ERROR HK',repr(e))
 if not ok:raise SystemExit(1)
if __name__=='__main__':main()
