import json,urllib.request,datetime,pathlib
OUT=pathlib.Path("trend-radar/data/douyin_raw.json")
BASE="https://emappdata.eastmoney.com/stockrank/"
COMMON={"appId":"appId01","globalId":"786e4c21-70dc-435a-93bb-38"}
TRACK={"SZ300308":("CPO","中际旭创"),"SZ300502":("CPO","新易盛"),"SZ300394":("CPO","天孚通信"),"SZ000977":("HBM / 存储","浪潮信息"),"SZ300274":("AI基建","阳光电源")}
def post(path,payload):
 data=json.dumps(payload).encode()
 headers={"User-Agent":"Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15","Content-Type":"application/json;charset=UTF-8","Accept":"application/json, text/plain, */*","Origin":"https://guba.eastmoney.com","Referer":"https://guba.eastmoney.com/rank/"}
 req=urllib.request.Request(BASE+path,data=data,headers=headers,method="POST")
 with urllib.request.urlopen(req,timeout=25) as r:return json.loads(r.read().decode("utf-8","ignore"))
def rank_from(data):
 if not isinstance(data,dict):return None
 # Eastmoney currently exposes rk/rank in latest payloads; tolerate nested variants.
 for k in ("rk","rank","currentRank","current_rank"):
  v=data.get(k)
  if v not in (None,""):
   try:return int(v)
   except:pass
 for v in data.values():
  if isinstance(v,dict):
   x=rank_from(v)
   if x:return x
 return None
def score_rank(rank):
 # Percentile-like attention: rank 1=100, 100=50, 500≈20, 1000≈10.
 return round(max(5,min(100,100/(1+(max(1,rank)-1)/100))),1)
stocks={}
errors=[]
for code,(theme,name) in TRACK.items():
 try:
  j=post("getCurrentLatest",{**COMMON,"marketType":"","srcSecurityCode":code})
  rank=rank_from(j.get("data"))
  if rank:
   stocks[code]={"name":name,"market":"A股","rank":rank,"score":score_rank(rank),"source":"东方财富个股最新人气排名"}
 except Exception as e:errors.append(code+":"+type(e).__name__)
try:
 j=post("getCurrentHkUsLatest",{**COMMON,"marketType":"000003","srcSecurityCode":"HK|03308"})
 rank=rank_from(j.get("data"))
 if rank:stocks["3308.HK"]={"name":"中际旭创H","market":"港股","rank":rank,"score":score_rank(rank),"source":"东方财富港股最新人气排名"}
except Exception as e:errors.append("3308.HK:"+type(e).__name__)
# Fallback: top lists if latest response schema changes.
if not stocks:
 try:
  for x in post("getAllCurrentList",{**COMMON,"marketType":"","pageNo":1,"pageSize":100}).get("data") or []:
   code=x.get("sc"); rank=x.get("rk")
   if code in TRACK and rank:
    th,name=TRACK[code];stocks[code]={"name":name,"market":"A股","rank":int(rank),"score":score_rank(int(rank)),"source":"东方财富A股Top100人气榜"}
 except Exception as e:errors.append("top100:"+type(e).__name__)
sectors={}
for th in ["CPO","HBM / 存储","AI芯片","AI网络","AI基建"]:
 vals=[v for k,v in stocks.items() if k in TRACK and TRACK[k][0]==th]
 sectors[th]=({"heatPercentile":max(v["score"] for v in vals),"sourceCount":1,"matches":vals} if vals else None)
if not stocks:raise SystemExit("No Eastmoney tracked-stock popularity. "+",".join(errors))
out={"updatedAt":datetime.datetime.now(datetime.timezone.utc).isoformat(),"source":"东方财富A/H个股最新人气排名","verifiedRealData":True,"scope":"A/H科技个股；逐股查询，失败显示待接，不伪造0","stocks":stocks,"sectors":sectors,"errors":errors}
OUT.write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding="utf-8")
print(json.dumps(out,ensure_ascii=False))
