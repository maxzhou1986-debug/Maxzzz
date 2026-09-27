import json, urllib.request, datetime, time
SYMS={"ANET":"ANET","MU":"MU","3308.HK":"3308.HK","300308.SZ":"300308.SZ"}
def get(sym):
    u="https://query1.finance.yahoo.com/v8/finance/chart/"+sym+"?range=1y&interval=1d"
    req=urllib.request.Request(u,headers={"User-Agent":"Mozilla/5.0"})
    with urllib.request.urlopen(req,timeout=20) as r: x=json.load(r)["chart"]["result"][0]
    closes=[v for v in x["indicators"]["quote"][0]["close"] if v is not None]
    meta=x.get("meta",{})
    return {"price":meta.get("regularMarketPrice") or closes[-1],"currency":meta.get("currency",""),"closes":closes[-260:]}
out={"updatedAt":datetime.datetime.now(datetime.timezone.utc).isoformat()}
for key,sym in SYMS.items():
    try: out[key]=get(sym)
    except Exception as e: out[key]={"error":str(e),"closes":[]}
    time.sleep(1)
with open("trend-radar/data/quotes.json","w",encoding="utf-8") as f: json.dump(out,f,ensure_ascii=False,separators=(",",":"))
