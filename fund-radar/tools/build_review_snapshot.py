#!/usr/bin/env python3
import json, math, os, time, urllib.parse, urllib.request
from datetime import datetime, timezone, timedelta

BASE='https://push2.eastmoney.com/api/qt/clist/get'
ULIST='https://push2.eastmoney.com/api/qt/ulist.np/get'
OUT=os.path.join(os.path.dirname(os.path.dirname(__file__)),'data')
TZ=timezone(timedelta(hours=8))
HEAD={'User-Agent':'Mozilla/5.0','Referer':'https://quote.eastmoney.com/'}
MARKETS={
 'A':{
  'stocks':'m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23',
  'sectors':'m:90+t:2',
  'indices':'1.000001,0.399001,0.399006',
  'index_names':{'000001':'上证指数','399001':'深证成指','399006':'创业板指'},
  'min_coverage':1000,
 },
 'HK':{
  'stocks':'m:128+t:3,m:128+t:4,m:128+t:1,m:128+t:2',
  'sectors':'m:124',
  'indices':'100.HSI,100.HSCEI,100.HSTECH',
  'index_names':{'HSI':'恒生指数','HSCEI':'恒生国企','HSTECH':'恒生科技'},
  'min_coverage':100,
 }
}

def get(url, tries=4):
    err=None
    for i in range(tries):
        try:
            req=urllib.request.Request(url,headers=HEAD)
            with urllib.request.urlopen(req,timeout=25) as r:
                return json.loads(r.read().decode('utf-8','ignore'))
        except Exception as e:
            err=e; time.sleep(1+i)
    raise err

def clist(filter_, fields, pz=200):
    rows=[]; seen=set(); total=None
    for page in range(1,60):
        q={'pn':page,'pz':pz,'po':0,'np':1,'fltt':2,'invt':2,'fid':'f12','fs':filter_,'fields':fields}
        d=get(BASE+'?'+urllib.parse.urlencode(q))
        data=(d or {}).get('data') or {}
        batch=data.get('diff') or []
        if isinstance(batch,dict): batch=list(batch.values())
        if total is None: total=int(data.get('total') or 0)
        added=0
        for x in batch:
            key=f"{x.get('f13','')}:{x.get('f12','')}"
            if x.get('f12') and key not in seen:
                seen.add(key); rows.append(x); added+=1
        if total and len(rows)>=total: break
        if not batch or not added: break
        time.sleep(.12)
    return rows,total

def ulist(secids):
    q={'fltt':2,'invt':2,'secids':secids,'fields':'f12,f13,f14,f3,f6,f124'}
    d=get(ULIST+'?'+urllib.parse.urlencode(q))
    diff=((d or {}).get('data') or {}).get('diff') or []
    return list(diff.values()) if isinstance(diff,dict) else diff

def num(v, default=0.0):
    try:
        if v in (None,'','-'): return default
        return float(v)
    except: return default

def day_from_ts(v):
    try:return datetime.fromtimestamp(int(v),TZ).strftime('%Y-%m-%d')
    except:return None

def compact(x):
    return {'code':str(x.get('f12') or ''),'name':str(x.get('f14') or ''),'pct':num(x.get('f3')),'amount':num(x.get('f6')),'flow':num(x.get('f62')),'turn':num(x.get('f8')),'vr':num(x.get('f10'))}

def build(m):
    cfg=MARKETS[m]
    fields='f12,f13,f14,f3,f6,f8,f10,f62,f184,f100,f124'
    stocks,total=clist(cfg['stocks'],fields)
    boards,btotal=clist(cfg['sectors'],fields)
    indices=ulist(cfg['indices'])
    dates=[day_from_ts(x.get('f124')) for x in indices if x.get('f124')]
    date=max([d for d in dates if d],default=datetime.now(TZ).strftime('%Y-%m-%d'))
    valid=[x for x in stocks if x.get('f14') and num(x.get('f6'))>0 and x.get('f3') not in (None,'-')]
    up=sum(num(x.get('f3'))>0 for x in valid); down=sum(num(x.get('f3'))<0 for x in valid); flat=len(valid)-up-down
    amount=sum(num(x.get('f6')) for x in valid)
    sectors=[compact(x) for x in boards if x.get('f14') and x.get('f3') not in (None,'-')]
    strong=sorted(sectors,key=lambda x:x['pct'],reverse=True)[:5]
    weak=sorted(sectors,key=lambda x:x['pct'])[:5]
    inflow=sorted([x for x in sectors if x['flow']>0],key=lambda x:x['flow'],reverse=True)[:5]
    outflow=sorted([x for x in sectors if x['flow']<0],key=lambda x:x['flow'])[:5]
    liquid=sorted(valid,key=lambda x:num(x.get('f6')),reverse=True)[:150]
    def score(x):
        a=max(1,num(x.get('f6')))
        return num(x.get('f3'))*2 + math.log10(a) + (1 if num(x.get('f62'))>0 else 0)
    leaders=[compact(x) for x in sorted([x for x in liquid if num(x.get('f3'))>0],key=score,reverse=True)[:8]]
    idx=[]
    for x in indices:
        c=compact(x); c['name']=cfg['index_names'].get(c['code'],c['name']); idx.append(c)
    ratio=up/max(1,len(valid))
    emotion='高潮' if ratio>=.75 else '偏强' if ratio>=.60 else '退潮' if ratio<=.25 else '偏弱' if ratio<=.40 else '分歧'
    return {
      'schema':2,'market':m,'date':date,'generatedAt':datetime.now(TZ).isoformat(timespec='seconds'),
      'source':'Eastmoney via GitHub Actions','coverage':len(valid),'total':total or len(stocks),'complete':bool(total and len(stocks)>=total and len(valid)>=cfg['min_coverage']),
      'breadth':{'up':up,'down':down,'flat':flat,'amount':amount,'count':len(valid)},'indices':idx,
      'strong':strong,'weak':weak,'inflow':inflow,'outflow':outflow,'leaders':leaders,'emotion':emotion,
      'sectorCount':len(sectors),'sectorTotal':btotal or len(boards)
    }

def main():
    os.makedirs(OUT,exist_ok=True)
    failures=[]
    for m in ('A','HK'):
        try:
            data=build(m)
            with open(os.path.join(OUT,f'review-{m}.json'),'w',encoding='utf-8') as f: json.dump(data,f,ensure_ascii=False,separators=(',',':'))
            print(m,'coverage',data['coverage'],'complete',data['complete'],'date',data['date'])
        except Exception as e:
            failures.append(f'{m}: {e}')
    if failures:
        raise SystemExit('; '.join(failures))
if __name__=='__main__': main()
