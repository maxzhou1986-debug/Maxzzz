import json, urllib.request, datetime, time
SYMS={"^NDX":"^NDX","^SOX":"^SOX","000688.SS":"000688.SS","399006.SZ":"399006.SZ","^HSTECH":"^HSTECH","^IXIC":"^IXIC","ANET":"ANET","MU":"MU","3308.HK":"3308.HK","300308.SZ":"300308.SZ","CSCO":"CSCO","HPE":"HPE","AVGO":"AVGO","WDC":"WDC","STX":"STX","000988.SZ":"000988.SZ","300502.SZ":"300502.SZ","300394.SZ":"300394.SZ","000660.KS":"000660.KS","005930.KS":"005930.KS","SKHY":"SKHY","NVDA":"NVDA","AMD":"AMD","MRVL":"MRVL","VRT":"VRT","DELL":"DELL","SMCI":"SMCI","LLY":"LLY","VRTX":"VRTX","JPM":"JPM","GS":"GS","XOM":"XOM","COP":"COP","FCX":"FCX","SCCO":"SCCO","CAT":"CAT","GE":"GE","COST":"COST","WMT":"WMT","600519.SS":"600519.SS","601318.SS":"601318.SS","601899.SS":"601899.SS","603993.SS":"603993.SS","300750.SZ":"300750.SZ","600276.SS":"600276.SS","3690.HK":"3690.HK","0700.HK":"0700.HK","1810.HK":"1810.HK","2269.HK":"2269.HK","2899.HK":"2899.HK"}
def get(sym):
    u="https://query1.finance.yahoo.com/v8/finance/chart/"+sym+"?range=1y&interval=1d"
    req=urllib.request.Request(u,headers={"User-Agent":"Mozilla/5.0"})
    with urllib.request.urlopen(req,timeout=20) as r: x=json.load(r)["chart"]["result"][0]
    q=x["indicators"]["quote"][0]; ts=x.get("timestamp",[])
    bars=[]
    for i,t in enumerate(ts):
        o=q["open"][i]; h=q["high"][i]; l=q["low"][i]; c=q["close"][i]; v=q["volume"][i]
        if None not in (o,h,l,c):
            bars.append({"t":t,"o":o,"h":h,"l":l,"c":c,"v":v or 0})
    closes=[b["c"] for b in bars]; meta=x.get("meta",{})
    return {"price":meta.get("regularMarketPrice") or closes[-1],"currency":meta.get("currency",""),"closes":closes[-260:],"bars":bars[-260:]}

def ma(a,n): return sum(a[-n:])/n if len(a)>=n else None
def trend_score(d):
    c=d.get("closes",[]); b=d.get("bars",[]); p=d.get("price") or (c[-1] if c else 0)
    if len(c)<60 or not p:return -999
    m20,m60=ma(c,20),ma(c,60); r5=(p/c[-6]-1)*100 if len(c)>=6 else 0; r20=(p/c[-21]-1)*100 if len(c)>=21 else 0
    vols=[x.get("v",0) for x in b[-25:] if x.get("v",0)>0]
    vr=1
    if len(vols)>=25:
        base=sum(vols[:20])/20; vr=(sum(vols[-5:])/5/base) if base else 1
    return round((35 if p>=m20 else -20)+(30 if p>=m60 else -15)+(15 if m20>=m60 else 0)+max(-15,min(20,r5*2))+max(-10,min(15,(r5-r20/4)*1.5))+max(-5,min(10,(vr-1)*15)),1)

out={"updatedAt":datetime.datetime.now(datetime.timezone.utc).isoformat()}
for key,sym in SYMS.items():
    try: out[key]=get(sym)
    except Exception as e: out[key]={"error":str(e),"closes":[],"bars":[]}
    time.sleep(1)
with open("trend-radar/data/quotes.json","w",encoding="utf-8") as f: json.dump(out,f,ensure_ascii=False,separators=(",",":"))\nexclude={"^NDX","^SOX","000688.SS","399006.SZ","^HSTECH","^IXIC","000660.KS","005930.KS"}\npool=[]\nfor s,d in out.items():\n    if s=="updatedAt" or s in exclude or not isinstance(d,dict) or d.get("error"): continue\n    sc=trend_score(d)\n    if sc>=35: pool.append({"symbol":s,"score":sc})\npool=sorted(pool,key=lambda x:x["score"],reverse=True)[:24]\nwith open("trend-radar/data/dynamic_pool.json","w",encoding="utf-8") as f: json.dump({"updatedAt":out["updatedAt"],"method":"MA20/60 + 5/20日动量 + 量能加速；跨行业候选自动晋级","stocks":pool},f,ensure_ascii=False,indent=2)
