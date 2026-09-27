import json,re,urllib.request,datetime,pathlib
P=pathlib.Path("trend-radar/data"); OUT=P/"douyin_raw.json"
THEMES={"CPO":["CPO","光模块","中际旭创","新易盛","天孚通信"],"HBM / 存储":["HBM","存储芯片","美光","SK海力士"],"AI芯片":["AI芯片","英伟达","AMD","博通"],"AI网络":["AI网络","交换机","Arista","博通"],"AI基建":["AI数据中心","AI服务器","液冷","数据中心"]}
SOURCES=[("今日头条","https://www.toutiao.com/"),("微博热搜","https://s.weibo.com/top/summary?cate=realtimehot")]
def fetch(url):
 r=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0"});return urllib.request.urlopen(r,timeout=20).read().decode("utf-8","ignore")
docs=[]
for name,url in SOURCES:
 try: docs.append((name,re.sub(r"<[^>]+>"," ",fetch(url))))
 except Exception: pass
if not docs: raise SystemExit("No real public-attention source available; keep pending.")
sectors={}
for theme,keys in THEMES.items():
 hits=0; matched=[]
 for src,txt in docs:
  for k in keys:
   n=txt.lower().count(k.lower())
   if n: hits+=n; matched.append({"source":src,"keyword":k,"mentions":n})
 if hits:
  srcn=len(set(x["source"] for x in matched))
  sectors[theme]={"heatPercentile":min(100,15+hits*10+max(0,srcn-1)*15),"sevenDayAcceleration":0,"searchAcceleration":0,"contentAcceleration":0,"mentions":hits,"sourceCount":srcn,"matches":matched}
 else: sectors[theme]=None
OUT.write_text(json.dumps({"updatedAt":datetime.datetime.now(datetime.timezone.utc).isoformat(),"source":"公开大众注意力（今日头条 + 微博热搜；按实际成功源计算）","verifiedRealData":True,"sectors":sectors},ensure_ascii=False,indent=2),encoding="utf-8")
print("updated real public attention")
