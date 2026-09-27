import json, urllib.request, datetime, time
SYMS={"^NDX":"^NDX","^SOX":"^SOX","000688.SS":"000688.SS","399006.SZ":"399006.SZ","^HSTECH":"^HSTECH","^IXIC":"^IXIC","ANET":"ANET","MU":"MU","3308.HK":"3308.HK","300308.SZ":"300308.SZ","CSCO":"CSCO","HPE":"HPE","AVGO":"AVGO","WDC":"WDC","STX":"STX","000988.SZ":"000988.SZ","300502.SZ":"300502.SZ","300394.SZ":"300394.SZ","000660.KS":"000660.KS","005930.KS":"005930.KS","SKHY":"SKHY","NVDA":"NVDA","AMD":"AMD","MRVL":"MRVL","VRT":"VRT","DELL":"DELL","SMCI":"SMCI"}
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
out={"updatedAt":datetime.datetime.now(datetime.timezone.utc).isoformat()}
for key,sym in SYMS.items():
    try: out[key]=get(sym)
    except Exception as e: out[key]={"error":str(e),"closes":[],"bars":[]}
    time.sleep(1)
with open("trend-radar/data/quotes.json","w",encoding="utf-8") as f: json.dump(out,f,ensure_ascii=False,separators=(",",":"))
