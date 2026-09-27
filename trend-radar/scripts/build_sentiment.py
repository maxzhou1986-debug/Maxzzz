import json, pathlib, datetime
P=pathlib.Path("trend-radar/data"); SRC=P/"douyin_raw.json"; OUT=P/"douyin_sentiment.json"; HIST=P/"douyin_history.json"
def clamp(x,a=0,b=100): return max(a,min(b,x))
def score(d,source=""):
    hp=float(d.get("heatPercentile",0))
    if "百度" in source: return round(clamp(hp),1)
    a7=clamp(50+float(d.get("sevenDayAcceleration",0)))
    sa=clamp(50+float(d.get("searchAcceleration",0))); ca=clamp(50+float(d.get("contentAcceleration",0)))
    return round(clamp(.35*hp+.35*a7+.20*sa+.10*ca),1)
if not SRC.exists(): raise SystemExit("No douyin_raw.json: keep sentiment pending; never fabricate data.")
raw=json.loads(SRC.read_text(encoding="utf-8")); now=datetime.datetime.now(datetime.timezone.utc); day=now.date().isoformat()
hist=json.loads(HIST.read_text(encoding="utf-8")) if HIST.exists() else {"days":[]}
out={"updatedAt":now.isoformat(),"source":raw.get("source","真实抖音/巨量算数数据"),"sectors":{}}
snap={"date":day,"sectors":{}}
for k,d in raw.get("sectors",{}).items():
    if d and d.get("heatPercentile") is not None:
        v=score(d,raw.get("source","")); snap["sectors"][k]=v
        past=[x for x in hist["days"] if k in x.get("sectors",{})]
        def chg(n):
            if len(past)<n:return None
            return round(v-past[-n]["sectors"][k],1)
        out["sectors"][k]={**d,"score":v,"heatChange1d":chg(1),"heatChange3d":chg(3),"heatChange7d":chg(7)}
hist["days"]=[x for x in hist["days"] if x.get("date")!=day]+[snap]; hist["days"]=hist["days"][-90:]
HIST.write_text(json.dumps(hist,ensure_ascii=False,indent=2),encoding="utf-8")
OUT.write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding="utf-8")
print(json.dumps(out,ensure_ascii=False))
