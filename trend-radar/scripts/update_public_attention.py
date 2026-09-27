import json,re,urllib.request,datetime,pathlib
P=pathlib.Path("trend-radar/data"); OUT=P/"douyin_raw.json"
URL="https://top.baidu.com/board?tab=realtime"
THEMES={"CPO":["CPO","光模块","中际旭创","新易盛","天孚通信"],"HBM / 存储":["HBM","存储芯片","美光","SK海力士"],"AI芯片":["AI芯片","英伟达","AMD","博通","GPU"],"AI网络":["AI网络","交换机","Arista","博通"],"AI基建":["AI数据中心","AI服务器","液冷","数据中心","算力"]}
req=urllib.request.Request(URL,headers={"User-Agent":"Mozilla/5.0","Accept":"text/html"})
html=urllib.request.urlopen(req,timeout=20).read().decode("utf-8","ignore")
if "热搜指数" not in html: raise SystemExit("Baidu hot board unavailable; keep prior public sentiment.")
text=re.sub(r"<[^>]+>"," ",html); text=re.sub(r"\\s+"," ",text)
nums=[float(x) for x in re.findall(r"(\\d{5,})\\s*热搜指数",text)]
if not nums: raise SystemExit("Baidu hot board parsed no heat index; keep prior public sentiment.")
mx=max(nums); sectors={}
for theme,keys in THEMES.items():
    matches=[]
    for k in keys:
        for m in re.finditer(re.escape(k),text,re.I):
            window=text[max(0,m.start()-120):min(len(text),m.end()+120)]
            vals=[float(x) for x in re.findall(r"(\\d{5,})",window)]
            if vals: matches.append({"keyword":k,"heat":max(vals)})
    raw=max([x["heat"] for x in matches],default=0)
    sectors[theme]={"heatPercentile":round(min(100,raw/mx*100),1) if raw else 0.0,"sevenDayAcceleration":0,"searchAcceleration":0,"contentAcceleration":0,"mentions":len(matches),"sourceCount":1,"matches":matches}
OUT.write_text(json.dumps({"updatedAt":datetime.datetime.now(datetime.timezone.utc).isoformat(),"source":"百度公开实时热搜榜","verifiedRealData":True,"sectors":sectors},ensure_ascii=False,indent=2),encoding="utf-8")
print(json.dumps(sectors,ensure_ascii=False))
