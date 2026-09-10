#!/usr/bin/env python3
import json, math, os, time, urllib.parse, urllib.request
from datetime import datetime, timezone, timedelta

BASE_PATH='/api/qt/clist/get'
ULIST_PATH='/api/qt/ulist.np/get'
HOSTS=['https://82.push2.eastmoney.com','https://20.push2.eastmoney.com','https://push2.eastmoney.com','http://82.push2.eastmoney.com']
SINA='https://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/Market_Center.getHQNodeData'
OUT=os.path.join(os.path.dirname(os.path.dirname(__file__)),'data')
TZ=timezone(timedelta(hours=8))
HEAD={'User-Agent':'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/140 Safari/537.36','Referer':'https://vip.stock.finance.sina.com.cn/mkt/','Accept':'application/json,text/plain,*/*','Accept-Language':'zh-CN,zh;q=0.9,en;q=0.7'}
UT='bd1d9ddb04089700cf9c27f6f7426281'

def raw_get(url, headers=None, timeout=20):
    req=urllib.request.Request(url,headers=headers or HEAD)
    with urllib.request.urlopen(req,timeout=timeout) as r:
        return r.read().decode('utf-8','ignore').strip()

def get_path(path, params, tries=1):
    errors=[]; query=urllib.parse.urlencode(params)
    for host in HOSTS:
        for i in range(tries):
            try:
                raw=raw_get(host+path+'?'+query)
                if not raw: raise RuntimeError('empty response')
                if raw.startswith(('jQuery','callback')) and '(' in raw: raw=raw[raw.find('(')+1:raw.rfind(')')]
                return json.loads(raw)
            except Exception as e:
                errors.append(f'{host}: {type(e).__name__}: {e}'); time.sleep(.5)
    raise RuntimeError(' | '.join(errors[-6:]))

def em_clist(filter_, fields, pz=200):
    rows=[]; seen=set(); total=None
    for page in range(1,60):
        q={'pn':page,'pz':pz,'po':1,'np':1,'fltt':2,'invt':2,'fid':'f12','fs':filter_,'fields':fields,'ut':UT}
        d=get_path(BASE_PATH,q); data=(d or {}).get('data') or {}; batch=data.get('diff') or []
        if isinstance(batch,dict): batch=list(batch.values())
        if total is None: total=int(data.get('total') or 0)
        added=0
        for x in batch:
            key=f"{x.get('f13','')}:{x.get('f12','')}"
            if x.get('f12') and key not in seen: seen.add(key); rows.append(x); added+=1
        if total and len(rows)>=total: break
        if not batch or not added: break
        time.sleep(.05)
    return rows,total

def em_ulist(secids):
    q={'fltt':2,'invt':2,'secids':secids,'fields':'f12,f13,f14,f3,f6,f124','ut':UT}
    d=get_path(ULIST_PATH,q); diff=((d or {}).get('data') or {}).get('diff') or []
    return list(diff.values()) if isinstance(diff,dict) else diff

def num(v, default=0.0):
    try:
        if v in (None,'','-'): return default
        return float(v)
    except: return default

def money_row(code,name,pct,amount,turn=0,flow=0,vr=0):
    return {'code':str(code or ''),'name':str(name or ''),'pct':num(pct),'amount':num(amount),'flow':num(flow),'turn':num(turn),'vr':num(vr)}

def sina_a_rows():
    rows=[]; seen=set()
    for page in range(1,90):
        q={'page':page,'num':100,'sort':'symbol','asc':1,'node':'hs_a','_s_r_a':'page'}
        url=SINA+'?'+urllib.parse.urlencode(q)
        raw=raw_get(url,{'User-Agent':HEAD['User-Agent'],'Referer':'https://vip.stock.finance.sina.com.cn/mkt/#hs_a'})
        if not raw or raw in ('null','[]'): break
        batch=json.loads(raw)
        if not isinstance(batch,list) or not batch: break
        for x in batch:
            code=str(x.get('code') or '').zfill(6)
            if code and code not in seen:
                seen.add(code)
                rows.append(money_row(code,x.get('name'),x.get('changepercent'),x.get('amount'),x.get('turnoverratio')))
        if len(batch)<100: break
        time.sleep(.06)
    return rows

def compact_em(x): return money_row(x.get('f12'),x.get('f14'),x.get('f3'),x.get('f6'),x.get('f8'),x.get('f62'),x.get('f10'))

def build_a():
    rows=sina_a_rows()
    valid=[x for x in rows if x['name'] and x['amount']>0]
    if len(valid)<1000: raise RuntimeError(f'A Sina coverage too low: {len(valid)}')
    up=sum(x['pct']>0 for x in valid); down=sum(x['pct']<0 for x in valid); flat=len(valid)-up-down
    amount=sum(x['amount'] for x in valid)
    liquid=sorted(valid,key=lambda x:x['amount'],reverse=True)[:240]
    def score(x): return x['pct']*2+math.log10(max(1,x['amount']))
    leaders=sorted([x for x in liquid if x['pct']>0],key=score,reverse=True)[:10]
    ratio=up/max(1,len(valid)); emotion='高潮' if ratio>=.75 else '偏强' if ratio>=.60 else '退潮' if ratio<=.25 else '偏弱' if ratio<=.40 else '分歧'

    sectors=[]; btotal=0; indices=[]
    try:
        fields='f12,f13,f14,f3,f6,f8,f10,f62,f184,f100,f124'
        boards,btotal=em_clist('m:90+t:2',fields)
        sectors=[compact_em(x) for x in boards if x.get('f14') and x.get('f3') not in (None,'-')]
    except Exception as e:
        print('WARN A sectors:',repr(e),flush=True)
    try:
        indices=[compact_em(x) for x in em_ulist('1.000001,0.399001,0.399006')]
    except Exception as e:
        print('WARN A indices:',repr(e),flush=True)

    strong=sorted(sectors,key=lambda x:x['pct'],reverse=True)[:5]
    weak=sorted(sectors,key=lambda x:x['pct'])[:5]
    inflow=sorted([x for x in sectors if x['flow']>0],key=lambda x:x['flow'],reverse=True)[:5]
    outflow=sorted([x for x in sectors if x['flow']<0],key=lambda x:x['flow'])[:5]

    return {'schema':5,'market':'A','date':datetime.now(TZ).strftime('%Y-%m-%d'),'generatedAt':datetime.now(TZ).isoformat(timespec='seconds'),'source':'Sina full-market + Eastmoney sectors via GitHub Actions','coverage':len(valid),'total':len(rows),'complete':len(valid)>=1000,'breadth':{'up':up,'down':down,'flat':flat,'amount':amount,'count':len(valid)},'indices':indices,'strong':strong,'weak':weak,'inflow':inflow,'outflow':outflow,'leaders':leaders,'emotion':emotion,'sectorCount':len(sectors),'sectorTotal':btotal or len(sectors)}

def build_hk():
    fields='f12,f13,f14,f3,f6,f8,f10,f62,f184,f100,f124'
    stocks,total=em_clist('m:128+t:3,m:128+t:4,m:128+t:1,m:128+t:2',fields)
    valid=[x for x in stocks if x.get('f14') and num(x.get('f6'))>0 and x.get('f3') not in (None,'-')]
    if len(valid)<100: raise RuntimeError(f'HK coverage too low: {len(valid)} / {total}')
    boards,btotal=em_clist('m:124',fields)
    sectors=[compact_em(x) for x in boards if x.get('f14') and x.get('f3') not in (None,'-')]
    up=sum(num(x.get('f3'))>0 for x in valid); down=sum(num(x.get('f3'))<0 for x in valid); flat=len(valid)-up-down; amount=sum(num(x.get('f6')) for x in valid)
    strong=sorted(sectors,key=lambda x:x['pct'],reverse=True)[:5]; weak=sorted(sectors,key=lambda x:x['pct'])[:5]
    inflow=sorted([x for x in sectors if x['flow']>0],key=lambda x:x['flow'],reverse=True)[:5]; outflow=sorted([x for x in sectors if x['flow']<0],key=lambda x:x['flow'])[:5]
    liquid=sorted(valid,key=lambda x:num(x.get('f6')),reverse=True)[:180]
    leaders=[compact_em(x) for x in sorted([x for x in liquid if num(x.get('f3'))>0],key=lambda x:num(x.get('f3'))*2+math.log10(max(1,num(x.get('f6')))),reverse=True)[:10]]
    ratio=up/max(1,len(valid)); emotion='高潮' if ratio>=.75 else '偏强' if ratio>=.60 else '退潮' if ratio<=.25 else '偏弱' if ratio<=.40 else '分歧'
    return {'schema':5,'market':'HK','date':datetime.now(TZ).strftime('%Y-%m-%d'),'generatedAt':datetime.now(TZ).isoformat(timespec='seconds'),'source':'Eastmoney via GitHub Actions','coverage':len(valid),'total':total or len(stocks),'complete':bool(total and len(stocks)>=total and len(valid)>=100),'breadth':{'up':up,'down':down,'flat':flat,'amount':amount,'count':len(valid)},'indices':[],'strong':strong,'weak':weak,'inflow':inflow,'outflow':outflow,'leaders':leaders,'emotion':emotion,'sectorCount':len(sectors),'sectorTotal':btotal or len(boards)}

def main():
    os.makedirs(OUT,exist_ok=True); failures=[]; success=0
    for m,builder in [('A',build_a),('HK',build_hk)]:
        try:
            data=builder();
            with open(os.path.join(OUT,f'review-{m}.json'),'w',encoding='utf-8') as f: json.dump(data,f,ensure_ascii=False,separators=(',',':'))
            print(m,'coverage',data['coverage'],'sectors',data['sectorCount'],'source',data['source']); success+=1
        except Exception as e:
            failures.append(f'{m}: {e}'); print('ERROR',m,repr(e),flush=True)
    if success==0: raise SystemExit('; '.join(failures))
    if failures: print('PARTIAL:', '; '.join(failures))
if __name__=='__main__': main()
