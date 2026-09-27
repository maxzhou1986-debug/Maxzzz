import json, urllib.request, datetime, time
SYMS={"^NDX":"^NDX","^SOX":"^SOX","000688.SS":"000688.SS","399006.SZ":"399006.SZ","^HSTECH":"^HSTECH","^IXIC":"^IXIC","ANET":"ANET","MU":"MU","3308.HK":"3308.HK","300308.SZ":"300308.SZ","CSCO":"CSCO","HPE":"HPE","AVGO":"AVGO","WDC":"WDC","STX":"STX","000988.SZ":"000988.SZ","300502.SZ":"300502.SZ","300394.SZ":"300394.SZ","000660.KS":"000660.KS","005930.KS":"005930.KS","SKHY":"SKHY","NVDA":"NVDA","AMD":"AMD","MRVL":"MRVL","VRT":"VRT","DELL":"DELL","SMCI":"SMCI","LLY":"LLY","VRTX":"VRTX","JPM":"JPM","GS":"GS","XOM":"XOM","COP":"COP","FCX":"FCX","SCCO":"SCCO","CAT":"CAT","GE":"GE","COST":"COST","WMT":"WMT","600519.SS":"600519.SS","601318.SS":"601318.SS","601899.SS":"601899.SS","603993.SS":"603993.SS","300750.SZ":"300750.SZ","600276.SS":"600276.SS","3690.HK":"3690.HK","0700.HK":"0700.HK","1810.HK":"1810.HK","2269.HK":"2269.HK","2899.HK":"2899.HK","600036.SS":"600036.SS","601688.SS":"601688.SS","600309.SS":"600309.SS","002594.SZ":"002594.SZ","300124.SZ":"300124.SZ","002050.SZ":"002050.SZ","600031.SS":"600031.SS","601088.SS":"601088.SS","000333.SZ":"000333.SZ","002475.SZ":"002475.SZ","688981.SS":"688981.SS","9988.HK":"9988.HK","9999.HK":"9999.HK","1024.HK":"1024.HK","1211.HK":"1211.HK","2382.HK":"2382.HK","1177.HK":"1177.HK","PLTR":"PLTR","CRWD":"CRWD","CEG":"CEG","VST":"VST","GEV":"GEV","RTX":"RTX","LMT":"LMT","AMZN":"AMZN","META":"META","GOOGL":"GOOGL"}
# 基本面硬门槛：动态趋势池只允许经过基本面初筛的经营型公司。
# 指数/海外参照不进入池；新增标的必须先加入此白名单，避免纯题材/无经营支撑股票自动混入。
FUNDAMENTAL_OK=set(SYMS)-{"^NDX","^SOX","000688.SS","399006.SZ","^HSTECH","^IXIC","000660.KS","005930.KS"}

def fundamental_ok(sym):
    return sym in FUNDAMENTAL_OK

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
    dist20=(p/m20-1)*100
    accel=r5-r20/4
    # 静默转强优先：趋势成立、短期加速、温和放量、尚未远离MA20。
    base=(30 if p>=m20 else -25)+(25 if p>=m60 else -15)+(12 if m20>=m60 else 0)
    momentum=max(-12,min(18,r5*2))+max(-10,min(18,accel*2))
    volume=max(-5,min(10,(vr-1)*15))
    position=12 if -1<=dist20<=5 else 5 if 5<dist20<=9 else -15 if dist20>12 else 0
    return round(base+momentum+volume+position,1)

out={"updatedAt":datetime.datetime.now(datetime.timezone.utc).isoformat()}
for key,sym in SYMS.items():
    try: out[key]=get(sym)
    except Exception as e: out[key]={"error":str(e),"closes":[],"bars":[]}
    time.sleep(0.2)
with open("trend-radar/data/quotes.json","w",encoding="utf-8") as f: json.dump(out,f,ensure_ascii=False,separators=(",",":"))
exclude={"^NDX","^SOX","000688.SS","399006.SZ","^HSTECH","^IXIC","000660.KS","005930.KS"}
pool=[]
for s,d in out.items():
    if s=="updatedAt" or s in exclude or not fundamental_ok(s) or not isinstance(d,dict) or d.get("error"):
        continue
    sc=trend_score(d)
    if sc>=35:
        m20=ma(d.get("closes",[]),20)
        p=d.get("price") or d["closes"][-1]
        dist=round((p/m20-1)*100,1) if m20 else None
        stage="静默转强" if dist is not None and -1<=dist<=6 else "强趋势" if dist is not None and dist<=12 else "高乖离"
        pool.append({"symbol":s,"score":sc,"stage":stage,"distMA20":dist})
pool=sorted(pool,key=lambda x:x["score"],reverse=True)[:24]
with open("trend-radar/data/dynamic_pool.json","w",encoding="utf-8") as f: json.dump({"updatedAt":out["updatedAt"],"method":"基本面硬过滤 → MA20/60趋势 + 5/20日动量加速 + 量能 + MA20位置；优先静默转强，惩罚高乖离","stocks":pool},f,ensure_ascii=False,indent=2)
