import json,pathlib,datetime
P=pathlib.Path("trend-radar/data");SRC=P/"douyin_raw.json";OUT=P/"douyin_sentiment.json";HIST=P/"douyin_history.json"
def clamp(x,a=0,b=100):return max(a,min(b,x))
def score(d,source=""):
 hp=float(d.get("heatPercentile",0))
 if "百度" in source or "东方财富" in source:return round(clamp(hp),1)
 return round(clamp(hp),1)
if not SRC.exists():raise SystemExit("No public sentiment source")
raw=json.loads(SRC.read_text(encoding="utf-8"));now=datetime.datetime.now(datetime.timezone.utc);day=now.date()
hist=json.loads(HIST.read_text(encoding="utf-8")) if HIST.exists() else {"days":[]}
# Keep one daily close-like snapshot; comparisons are calendar-day based, never previous-run based.
today={"date":day.isoformat(),"sectors":{}}
out={"updatedAt":now.isoformat(),"source":raw.get("source","public sentiment"),"scope":raw.get("scope"),"stocks":raw.get("stocks",{}),"sectors":{}}
def historical_value(sector,days):
 target=day-datetime.timedelta(days=days); candidates=[]
 for x in hist.get("days",[]):
  try:d=datetime.date.fromisoformat(x["date"])
  except:continue
  if d<=target and sector in x.get("sectors",{}):candidates.append((d,x["sectors"][sector]))
 return max(candidates,key=lambda z:z[0])[1] if candidates else None
for k,d in raw.get("sectors",{}).items():
 if d and d.get("heatPercentile") is not None:
  v=score(d,raw.get("source",""));today["sectors"][k]=v
  def chg(days):
   old=historical_value(k,days);return None if old is None else round(v-old,1)
  out["sectors"][k]={**d,"score":v,"heatChange1d":chg(1),"heatChange3d":chg(3),"heatChange7d":chg(7)}
hist["days"]=[x for x in hist.get("days",[]) if x.get("date")!=day.isoformat()]+[today]
hist["days"]=sorted(hist["days"],key=lambda x:x["date"])[-90:]
HIST.write_text(json.dumps(hist,ensure_ascii=False,indent=2),encoding="utf-8")
OUT.write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding="utf-8")
print(json.dumps(out,ensure_ascii=False))
