// V2.19: A-share fallback is last-resort only and never overrides a high-coverage server snapshot.
(function(){
'use strict';
let busy=false,last=null,serverReady=false;
const U='https://push2.eastmoney.com/api/qt/ulist.np/get';
const IDS='1.600519,1.601318,1.600036,0.000001,0.000333,0.300750,0.300308,0.300502,1.688981,1.688041,1.688012,1.600309,1.601899,0.002594,0.002475,0.002371,0.300476,0.300394,1.688318,0.002463,0.002837,0.300274,0.300124,0.000858,1.600030,1.601688,1.600276,0.000725,0.002230,0.002241';
function esc(v){return String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
function n(v){v=Number(v);return Number.isFinite(v)?v:0}
function money(v){return (n(v)/1e8).toFixed(1)+'亿'}
function hasServerSnapshot(){
  const s=document.getElementById('reviewStatus')?.textContent||'';
  const b=document.getElementById('reviewBody')?.textContent||'';
  const m=s.match(/(\d{4,})只/)||b.match(/覆盖\s*(\d{4,})\s*\//);
  if(m&&Number(m[1])>=1000){serverReady=true;return true}
  return serverReady;
}
function req(url,timeout=10000){return new Promise((ok,fail)=>{const cb='arf_'+Date.now()+'_'+Math.random().toString(36).slice(2),s=document.createElement('script');let t;const done=(e,d)=>{clearTimeout(t);s.remove();delete window[cb];e?fail(e):ok(d)};window[cb]=d=>done(null,d);s.onerror=()=>done(new Error('A股备用行情连接失败'));t=setTimeout(()=>done(new Error('A股备用行情超时')),timeout);s.src=url+'&cb='+cb+'&_='+Date.now();document.body.appendChild(s)})}
function fromState(){const d=state&&state.A;if(!d||!d.live||!Array.isArray(d.stocks)||d.stocks.length<5)return null;return d.stocks.map(x=>({f12:x.code,f14:x.name,f3:x.pct,f6:n(x.amount)*1e8,f8:x.turn,f10:x.vr,f62:x.flow,f184:x.flowPct}));}
async function fromUlist(){const url=U+'?fltt=2&invt=2&secids='+encodeURIComponent(IDS)+'&fields=f12,f14,f3,f6,f8,f10,f62,f184,f124';const r=await req(url);const rows=Array.isArray(r?.data?.diff)?r.data.diff:Object.values(r?.data?.diff||{});if(rows.length<5)throw new Error('A股备用行情样本不足');return rows;}
function renderA(rows,source){
  if(hasServerSnapshot())return;
  const box=document.getElementById('reviewBody'),status=document.getElementById('reviewStatus');if(!box||currentTab!=='review'||market!=='A')return;
  const valid=rows.filter(x=>x&&x.f14&&Number.isFinite(Number(x.f3))&&n(x.f6)>0),up=valid.filter(x=>n(x.f3)>0).length,down=valid.filter(x=>n(x.f3)<0).length,flat=valid.length-up-down,amt=valid.reduce((s,x)=>s+n(x.f6),0),ratio=up/Math.max(1,valid.length);const emotion=ratio>=.6?'偏强':ratio<=.4?'偏弱':'分歧';const leaders=valid.slice().sort((a,b)=>((n(b.f3)*2+Math.log10(Math.max(1,n(b.f6)))+(n(b.f62)>0?1:0))-(n(a.f3)*2+Math.log10(Math.max(1,n(a.f6)))+(n(a.f62)>0?1:0)))).slice(0,8),strong=valid.slice().sort((a,b)=>n(b.f3)-n(a.f3)).slice(0,8),weak=valid.slice().sort((a,b)=>n(a.f3)-n(b.f3)).slice(0,8);const mkRows=arr=>'<div class="list">'+arr.map((x,i)=>'<div class="reviewRow"><div><b>'+(i+1)+'. '+esc(x.f14)+'</b><div class="meta">'+esc(x.f12)+' · 成交 '+money(x.f6)+'</div></div><div class="right '+(n(x.f3)>=0?'up':'down')+'">'+(n(x.f3)>=0?'+':'')+n(x.f3).toFixed(2)+'%</div></div>').join('')+'</div>';
  box.innerHTML='<div class="card"><strong>A股 · 实盘代表池快照</strong><div class="mini">来源：'+source+'。覆盖 '+valid.length+' 只真实 A 股行情；仅在全市场服务器快照不可用时兜底。</div></div><section class="section"><div class="st"><h2>市场概览</h2></div><div class="reviewMetrics"><div class="metric"><b>'+up+'</b><span>上涨</span></div><div class="metric"><b>'+down+'</b><span>下跌</span></div><div class="metric"><b>'+flat+'</b><span>平盘</span></div><div class="metric"><b>'+money(amt)+'</b><span>样本成交额</span></div></div></section><section class="section"><div class="st"><h2>市场情绪：'+emotion+'</h2></div><div class="card mini">代表池上涨占比 '+(ratio*100).toFixed(1)+'%。这不是全市场涨跌家数。</div></section><section class="section"><div class="st"><h2>涨幅前列</h2></div>'+mkRows(strong)+'</section><section class="section"><div class="st"><h2>跌幅前列</h2></div>'+mkRows(weak)+'</section><section class="section"><div class="st"><h2>核心强势候选</h2></div>'+mkRows(leaders)+'</section>';
  if(status)status.textContent='A股备用实盘快照 · '+valid.length+'只';
}
async function fallback(){
  if(busy||market!=='A'||currentTab!=='review'||hasServerSnapshot())return;
  busy=true;const status=document.getElementById('reviewStatus');if(status)status.textContent='A股全市场快照未取到，正在读取备用实盘…';
  try{const local=fromState();if(local){last=local;renderA(local,'雷达实盘行情');return}last=await fromUlist();renderA(last,'独立备用行情接口')}catch(e){if(status&&!hasServerSnapshot())status.textContent=e.message+'；A股暂无可用实盘快照'}finally{busy=false}
}
const oldShow=showTab;showTab=function(t){oldShow(t);if(t==='review'&&market==='A')setTimeout(()=>{if(!hasServerSnapshot())fallback()},1800)};
const oldSwitch=switchMarket;switchMarket=function(m){oldSwitch(m);if(currentTab==='review'&&m==='A')setTimeout(()=>{if(!hasServerSnapshot())fallback()},1800)};
const btn=document.getElementById('reviewRefresh');if(btn)btn.addEventListener('click',()=>{if(market==='A')setTimeout(()=>{if(!hasServerSnapshot())fallback()},1800)});
const status=document.getElementById('reviewStatus');if(status)new MutationObserver(()=>{const txt=status.textContent||'';if(/(\d{4,})只/.test(txt))serverReady=true;if(market==='A'&&currentTab==='review'&&!hasServerSnapshot()&&/失败|暂无可用|无法核实|没有可核实|尚未生成/.test(txt))setTimeout(fallback,600)}).observe(status,{childList:true,characterData:true,subtree:true});
})();