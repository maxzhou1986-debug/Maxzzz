import json,re,urllib.request,datetime,pathlib
URL="https://ai.xueqiu.com/hot/stock"
OUT=pathlib.Path("trend-radar/data/investor_sentiment.json"); HIST=pathlib.Path("trend-radar/data/investor_sentiment_history.json")
THEMES={"CPO":["SZ300308","SZ300502","SZ300394","SH601869"],"HBM / 存储":["MU","SKHY","SZ000977"],"AI芯片":["NVDA","AMD","AVGO","SH688795","SH688801"],"AI网络":["ANET","CSCO","AVGO"],"AI基建":["SZ000977","SZ300274","VRT","DELL","SMCI"]}
req=urllib.request.Request(URL,headers={"User-Agent":"Mozilla/5.0","Accept":"text/html"})
html=urllib.request.urlopen(req,timeout=20).read().decode("utf-8","ignore")
text=re.sub(r"<[^>]+>"," ",html); text=re.sub(r"\s+"," ",text)
pairs={}
for m in re.finditer(r"([A-Z]{1,5}\d{0,6}|\d{5})\s+(\d+(?:\.\d+)?)\s*热度",text):
    pairs[m.group(1)]=float(m.group(2))
if not pairs: raise SystemExit("No code+heat pairs from Xueqiu AI hot page; keep prior sentiment.")
mx=max(pairs.values())
hist=json.loads(HIST.read_text(encoding="utf-8")) if HIST.exists() else {"snapshots":[]}
sectors={}
for theme,codes in THEMES.items():
    vals=[pairs[x] for x in codes if x in pairs]
    if vals:
        score=round(min(100,max(vals)/mx*100),1); past=[x for x in hist["snapshots"] if x.get("sector")==theme]
        prev=past[-1]["score"] if past else None; old3=past[-3]["score"] if len(past)>=3 else None
        sectors[theme]={"score":score,"heatChange1d":None if prev is None else round(score-prev,1),"heatChange3d":None if old3 is None else round(score-old3,1),"sampleCount":len(vals),"rawMaxHeat":max(vals),"matchedCodes":[x for x in codes if x in pairs]}
    else: sectors[theme]=None
out={"updatedAt":datetime.datetime.now(datetime.timezone.utc).isoformat(),"source":"雪球AI公开热股1小时热度","method":"按股票代码匹配板块代表股；板块最高热度/全榜最高热度归一化","sectors":sectors}
if not any(sectors.values()): raise SystemExit("Xueqiu parsed but no tracked symbols matched; keep prior sentiment.")
OUT.write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding="utf-8")
now=out["updatedAt"]
for k,v in sectors.items():
    if v: hist["snapshots"].append({"time":now,"sector":k,"score":v["score"]})
hist["snapshots"]=hist["snapshots"][-500:]; HIST.write_text(json.dumps(hist,ensure_ascii=False,indent=2),encoding="utf-8")
print(json.dumps(out,ensure_ascii=False))
