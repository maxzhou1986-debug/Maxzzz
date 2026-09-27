import json, re, urllib.request, datetime, pathlib
URL="https://xueqiu.com/hot/stock"
OUT=pathlib.Path("trend-radar/data/investor_sentiment.json")
HIST=pathlib.Path("trend-radar/data/investor_sentiment_history.json")
THEMES={"CPO":["中际旭创","新易盛","天孚通信","长飞光纤"],"HBM / 存储":["美光","SK海力士","浪潮信息"],"AI芯片":["英伟达","AMD","博通","摩尔线程","燧原"],"AI网络":["Arista","思科","博通"],"AI基建":["浪潮信息","阳光电源","Vertiv","Dell","Super Micro"]}
req=urllib.request.Request(URL,headers={"User-Agent":"Mozilla/5.0"})
html=urllib.request.urlopen(req,timeout=20).read().decode("utf-8","ignore")
text=re.sub(r"<[^>]+>"," ",html)
pairs=[]
for m in re.finditer(r"([A-Za-z0-9\-\u4e00-\u9fff]+)\s+(\d+(?:\.\d+)?)\s*热度",text):
    pairs.append((m.group(1),float(m.group(2))))
mx=max([v for _,v in pairs],default=0)
hist=json.loads(HIST.read_text(encoding="utf-8")) if HIST.exists() else {"snapshots":[]}
sectors={}
for theme,names in THEMES.items():
    vals=[v for n,v in pairs if any(k in n for k in names)]
    if vals and mx:
        score=round(min(100,max(vals)/mx*100),1)
        past=[x for x in hist["snapshots"] if x.get("sector")==theme]
        prev=past[-1]["score"] if past else None
        old3=past[-3]["score"] if len(past)>=3 else None
        sectors[theme]={"score":score,"heatChange1d":None if prev is None else round(score-prev,1),"heatChange3d":None if old3 is None else round(score-old3,1),"sampleCount":len(vals)}
    else: sectors[theme]=None
out={"updatedAt":datetime.datetime.now(datetime.timezone.utc).isoformat(),"source":"雪球公开热股1小时热度","method":"板块代表股热度相对当期榜首归一化；无匹配则保持空值，不模拟","sectors":sectors}
OUT.write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding="utf-8")
now=out["updatedAt"]
for k,v in sectors.items():
    if v: hist["snapshots"].append({"time":now,"sector":k,"score":v["score"]})
hist["snapshots"]=hist["snapshots"][-500:]
HIST.write_text(json.dumps(hist,ensure_ascii=False,indent=2),encoding="utf-8")
print(json.dumps(out,ensure_ascii=False))
