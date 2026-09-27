import json, pathlib, datetime, math
P=pathlib.Path("trend-radar/data")
SRC=P/"douyin_search_raw.json"; OUT=P/"douyin_raw.json"
THEMES={"CPO":["CPO","光模块","中际旭创","新易盛","天孚通信"],"HBM / 存储":["HBM","存储芯片","美光","SK海力士"],"AI芯片":["AI芯片","英伟达","AMD","博通"],"AI网络":["AI网络","交换机","Arista","博通"],"AI基建":["AI数据中心","AI服务器","液冷","Vertiv"]}
if not SRC.exists(): raise SystemExit("No real Douyin search snapshot; keep public sentiment pending.")
raw=json.loads(SRC.read_text(encoding="utf-8"))
if not raw.get("verifiedRealData"): raise SystemExit("Unverified Douyin data rejected.")
sectors={}
for theme,keys in THEMES.items():
    items=[]
    for k in keys: items += raw.get("keywords",{}).get(k,[]) or []
    if not items: sectors[theme]=None; continue
    likes=sum(max(0,float(x.get("digg",0) or 0)) for x in items)
    comments=sum(max(0,float(x.get("comment",0) or 0)) for x in items)
    shares=sum(max(0,float(x.get("share",0) or 0)) for x in items)
    fresh=sum(1 for x in items if float(x.get("ageHours",9999) or 9999)<=72)/len(items)
    engagement=math.log10(1+likes+2*comments+3*shares)
    sectors[theme]={"heatPercentile":min(100,engagement*16),"sevenDayAcceleration":0,"searchAcceleration":0,"contentAcceleration":round((fresh-.5)*100,1),"sampleCount":len(items)}
OUT.write_text(json.dumps({"updatedAt":datetime.datetime.now(datetime.timezone.utc).isoformat(),"source":raw.get("source","抖音公开搜索真实快照"),"sectors":sectors},ensure_ascii=False,indent=2),encoding="utf-8")
print("normalized real Douyin search snapshot")
