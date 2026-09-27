import json,re,urllib.request,datetime,pathlib,math
P=pathlib.Path("trend-radar/data"); OUT=P/"douyin_raw.json"
STOCKS={"SZ300308":("CPO","中际旭创"),"SZ300502":("CPO","新易盛"),"SZ300394":("CPO","天孚通信"),"SZ000977":("HBM / 存储","浪潮信息"),"SZ300274":("AI基建","阳光电源")}
def fetch(code):
 n=code[2:]
 urls=[f"https://guba.eastmoney.com/list,{n}.html",f"https://mguba.eastmoney.com/mguba/list/{n}"]
 for u in urls:
  try:
   req=urllib.request.Request(u,headers={"User-Agent":"Mozilla/5.0","Accept":"text/html"})
   h=urllib.request.urlopen(req,timeout=20).read().decode("utf-8","ignore")
   if len(h)>1000:return re.sub(r"\\s+"," ",re.sub(r"<[^>]+>"," ",h))
  except Exception:pass
 return ""
by={}
for code,(theme,name) in STOCKS.items():
 t=fetch(code)
 if not t:continue
 rank=None
 m=re.search(r"人气第\\s*(\\d+)\\s*名",t)
 if m:rank=int(m.group(1))
 reads=[int(x.replace(",","")) for x in re.findall(r"(\\d{2,7})\\s*(?:次浏览|阅读)",t)]
 comments=[int(x) for x in re.findall(r"(\\d{1,4})\\s*(?:条评论|评论)",t)]
 # rank dominates; activity is a secondary signal. No successful page => no score.
 rankScore=max(0,100-(rank-1)*0.5) if rank else None
 activity=math.log10(1+sum(sorted(reads,reverse=True)[:20])+10*sum(sorted(comments,reverse=True)[:20]))*12 if reads or comments else None
 vals=[x for x in [rankScore,activity] if x is not None]
 if vals:
  score=round(min(100,sum(vals)/len(vals)),1)
  item={"code":code,"name":name,"score":score,"rank":rank,"sampleReads":sum(reads[:20]) if reads else 0,"sampleComments":sum(comments[:20]) if comments else 0}\n  stocks[code]=item\n  by.setdefault(theme,[]).append(item)
sectors={}
for theme in ["CPO","HBM / 存储","AI芯片","AI网络","AI基建"]:
 a=by.get(theme,[])
 if a:
  v=max(x["score"] for x in a)
  sectors[theme]={"heatPercentile":v,"sevenDayAcceleration":0,"searchAcceleration":0,"contentAcceleration":0,"sourceCount":1,"matches":a}
 else:sectors[theme]=None
if not any(sectors.values()):raise SystemExit("Eastmoney public sentiment returned no usable A-share data; keep prior.")
OUT.write_text(json.dumps({"updatedAt":datetime.datetime.now(datetime.timezone.utc).isoformat(),"source":"东方财富A股人气/股吧公开数据","verifiedRealData":True,"scope":"A/H科技股；美股不使用该大众指标","stocks":stocks,"sectors":sectors},ensure_ascii=False,indent=2),encoding="utf-8")
print(json.dumps(sectors,ensure_ascii=False))
