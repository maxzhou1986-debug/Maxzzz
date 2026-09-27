import json, pathlib, datetime
P=pathlib.Path("trend-radar/data")
SRC=P/"douyin_raw.json"
OUT=P/"douyin_sentiment.json"
def clamp(x,a=0,b=100): return max(a,min(b,x))
def score(d):
    # Inputs are normalized 0-100 or percentage changes from a real provider/export.
    hp=float(d.get("heatPercentile",0))
    a7=clamp(50+float(d.get("sevenDayAcceleration",0)))
    sa=clamp(50+float(d.get("searchAcceleration",0)))
    ca=clamp(50+float(d.get("contentAcceleration",0)))
    return round(clamp(.35*hp+.35*a7+.20*sa+.10*ca),1)
if not SRC.exists():
    raise SystemExit("No douyin_raw.json: keep sentiment as pending; never fabricate data.")
raw=json.loads(SRC.read_text(encoding="utf-8"))
out={"updatedAt":datetime.datetime.now(datetime.timezone.utc).isoformat(),"source":raw.get("source","真实抖音/巨量算数数据"),"sectors":{}}
for k,d in raw.get("sectors",{}).items():
    if d and d.get("heatPercentile") is not None:
        out["sectors"][k]={**d,"score":score(d)}
OUT.write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding="utf-8")
print(json.dumps(out,ensure_ascii=False))
