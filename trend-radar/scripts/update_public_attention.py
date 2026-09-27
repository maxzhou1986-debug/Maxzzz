import json,urllib.request,datetime,pathlib
OUT=pathlib.Path("trend-radar/data/douyin_raw.json")
BASE="https://emappdata.eastmoney.com/stockrank/"
COMMON={"appId":"appId01","globalId":"786e4c21-70dc-435a-93bb-38"}
TRACK={"SZ300308":("CPO","中际旭创"),"SZ300502":("CPO","新易盛"),"SZ300394":("CPO","天孚通信"),"SZ000977":("HBM / 存储","浪潮信息"),"SZ300274":("AI基建","阳光电源"),"SH600519":("消费","贵州茅台"),"SH601318":("金融","中国平安"),"SH601899":("有色 / 铜","紫金矿业"),"SH603993":("有色 / 铜","洛阳钼业"),"SZ300750":("新能源","宁德时代"),"SH600276":("创新药","恒瑞医药"),"SH600036":("金融","招商银行"),"SH601688":("金融","华泰证券"),"SH600309":("化工","万华化学"),"SZ002594":("新能源","比亚迪"),"SZ300124":("机器人","汇川技术"),"SZ002050":("机器人","三花智控"),"SH600031":("工业","三一重工"),"SH601088":("能源","中国神华"),"SZ000333":("消费","美的集团"),"SZ002475":("消费","立讯精密"),"SH688981":("半导体","中芯国际")}
def post(path,payload):
 data=json.dumps(payload).encode()
 req=urllib.request.Request(BASE+path,data=data,headers={"User-Agent":"Mozilla/5.0","Content-Type":"application/json","Accept":"application/json"})
 with urllib.request.urlopen(req,timeout=25) as r:return json.loads(r.read().decode())
def score_rank(rank):
 # Smooth popularity score; rank 1≈100, 100≈50, 500≈17.
 return round(max(5,min(100,100/(1+(max(1,int(rank))-1)/100))),1)
stocks={}
# This list endpoint is proven to work on GitHub Actions. Request a wide page so tracked leaders need not be Top100.
a=post("getAllCurrentList",{**COMMON,"marketType":"","pageNo":1,"pageSize":5000}).get("data") or []
for x in a:
 code=x.get("sc"); rank=x.get("rk")
 if code in TRACK and rank is not None:
  th,name=TRACK[code];stocks[code]={"name":name,"market":"A股","rank":int(rank),"score":score_rank(rank),"source":"东方财富A股人气榜"}
hk=post("getAllCurrHkUsList",{**COMMON,"marketType":"000003","pageNo":1,"pageSize":2000}).get("data") or []
for x in hk:
 sc=str(x.get("sc",""));rank=x.get("rk")
 if ("03308" in sc or sc.endswith("|3308") or sc.endswith("|03308")) and rank is not None:
  stocks["3308.HK"]={"name":"中际旭创H","market":"港股","rank":int(rank),"score":score_rank(rank),"source":"东方财富港股人气榜"}
sectors={}
for th in sorted(set(v[0] for v in TRACK.values())):
 vals=[v for k,v in stocks.items() if k in TRACK and TRACK[k][0]==th]
 sectors[th]=({"heatPercentile":max(v["score"] for v in vals),"sourceCount":1,"matches":vals} if vals else None)
if not stocks:raise SystemExit("Eastmoney rank JSON returned no tracked A/H leaders")
out={"updatedAt":datetime.datetime.now(datetime.timezone.utc).isoformat(),"source":"东方财富A/H个股人气榜 JSON","verifiedRealData":True,"scope":"A/H跨行业龙头个股；宽榜匹配，未返回则待接，不伪造0","stocks":stocks,"sectors":sectors}
OUT.write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding="utf-8")
print(json.dumps(out,ensure_ascii=False))
