// V2.21: full-market review via Pages + CDN + raw GitHub; pin valid full snapshots so late legacy renders cannot overwrite them.
(function(){
'use strict';
const mem={};
const min={A:1000,HK:100};
const RAW='https://raw.githubusercontent.com/maxzhou1986-debug/Maxzzz/main/fund-radar/data/';
const CDN='https://cdn.jsdelivr.net/gh/maxzhou1986-debug/Maxzzz@main/fund-radar/data/';
const POLL_MS=75000;
let restoring=false;
function esc(v){return String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
function pct(v){v=Number(v)||0;return (v>=0?'+':'')+v.toFixed(2)+'%'}
function money(v,m){v=Number(v)||0;return (v/1e8).toFixed(v>=1e10?0:1)+'亿'+(m==='A'?'元':'港元')}
function ageMin(d){const t=Date.parse(d||'');return Number.isFinite(t)?Math.max(0,Math.round((Date.now()-t)/60000)):9999}
function freshness(d){const a=ageMin(d.generatedAt);if(a<=10)return '近实时 · '+a+'分钟前';if(a<=25)return '轻微延迟 · '+a+'分钟前';if(a<1440)return '数据偏旧 · '+a+'分钟前';return '上一交易日快照'}
function list(items,m,flow=false){if(!items||!items.length)return '<div class="empty">暂无数据</div>';return '<div class="list">'+items.map((x,i)=>'<div class="reviewRow"><div><b>'+(i+1)+'. '+esc(x.name)+'</b><div class="meta">'+esc(x.code||'')+' · 成交 '+money(x.amount,m)+'</div></div><div class="right '+((flow?x.flow:x.pct)>=0?'up':'down')+'">'+(flow?money(x.flow,m):pct(x.pct))+'</div></div>').join('')+'</div>'}
function section(t,b){return '<section class="section"><div class="st"><h2>'+t+'</h2></div>'+b+'</section>'}
async function readJson(url){const r=await fetch(url+(url.includes('?')?'&':'?')+'ts='+Date.now(),{cache:'no-store',mode:'cors'});if(!r.ok)throw new Error('snapshot '+r.status);return r.json()}
async function get(m){const name='review-'+m+'.json';const urls=[['Pages同源','./data/'+name],['CDN直读',CDN+name],['仓库直读',RAW+name]];let best=null;for(const [via,url] of urls){try{const d=await readJson(url);if(!d||d.market!==m||Number(d.coverage||0)<min[m])continue;d._via=via;if(!best||Date.parse(d.generatedAt||0)>Date.parse(best.generatedAt||0))best=d}catch(e){}}if(best)mem[m]=best;return best}
function render(d){if(!d||currentTab!=='review'||market!==d.market)return false;const m=d.market,b=d.breadth||{},box=document.getElementById('reviewBody'),status=document.getElementById('reviewStatus');if(!box)return false;const fresh=freshness(d),liveish=ageMin(d.generatedAt)<=15;window.__FULL_REVIEW_LOCK__=window.__FULL_REVIEW_LOCK__||{};window.__FULL_REVIEW_LOCK__[m]={coverage:Number(d.coverage||0),generatedAt:d.generatedAt};restoring=true;box.innerHTML='<div data-full-review="'+m+'" class="card"><strong>'+esc(d.date)+' · '+(m==='A'?'A股':'港股')+' · 全市场复盘</strong><div class="mini">覆盖 '+Number(d.coverage||0)+' / '+Number(d.total||0)+' 只 · '+esc(d._via||'服务器快照')+' · '+fresh+'<br>生成：'+esc(d.generatedAt||'')+'</div></div>'+section('市场概览','<div class="reviewMetrics"><div class="metric"><b>'+Number(b.up||0)+'</b><span>上涨</span></div><div class="metric"><b>'+Number(b.down||0)+'</b><span>下跌</span></div><div class="metric"><b>'+Number(b.flat||0)+'</b><span>平盘</span></div><div class="metric"><b>'+money(b.amount,m)+'</b><span>成交额</span></div></div>'+list(d.indices||[],m,false))+section('最强板块 Top 5',list(d.strong||[],m,false))+section('最弱板块 Top 5',list(d.weak||[],m,false))+section('板块资金净流入 Top 5',list(d.inflow||[],m,true))+section('板块资金净流出 Top 5',list(d.outflow||[],m,true))+section('当日龙头与核心强势候选',list(d.leaders||[],m,false))+section('市场情绪：'+esc(d.emotion||'数据不足'),'<div class="card mini">涨跌家数来自全市场高覆盖快照；数据源没有的资金字段不会模拟。</div>')+'<p class="notice">V2.21：全市场快照一旦成功读取就固定显示；旧复盘异步请求即使稍后返回，也不会再把5000+只结果覆盖掉。</p>';if(status){status.textContent=(m==='A'?'A股':'港股')+'完整复盘 · '+d.coverage+' / '+d.total+'只 · '+fresh;status.classList.toggle('warn',!liveish)}setTimeout(()=>{restoring=false},0);return true}
async function prefer(m=market){if(currentTab!=='review')return false;const status=document.getElementById('reviewStatus');if(status&&!mem[m])status.textContent='正在读取全市场快照…';const d=await get(m);if(!d){if(status&&!mem[m])status.textContent='全市场快照线路暂不可达';return false}return render(d)}
function repin(){if(restoring||currentTab!=='review')return;const d=mem[market];if(!d||Number(d.coverage||0)<min[market])return;const box=document.getElementById('reviewBody');if(!box)return;const marker=box.querySelector('[data-full-review="'+market+'"]');if(!marker)setTimeout(()=>{if(currentTab==='review'&&market===d.market)render(d)},0)}
window.__preferFullReview=prefer;
const oldShow=showTab;showTab=function(t){oldShow(t);if(t==='review')setTimeout(()=>prefer(market),40)};
const oldSwitch=switchMarket;switchMarket=function(m){oldSwitch(m);if(currentTab==='review')setTimeout(()=>prefer(m),40)};
document.getElementById('reviewRefresh')?.addEventListener('click',()=>{if(currentTab==='review')setTimeout(()=>prefer(market),40)});
const box=document.getElementById('reviewBody');if(box)new MutationObserver(repin).observe(box,{childList:true,subtree:true,characterData:true});
const status=document.getElementById('reviewStatus');if(status)new MutationObserver(repin).observe(status,{childList:true,subtree:true,characterData:true});
setInterval(()=>{if(currentTab==='review')prefer(market)},POLL_MS);
setTimeout(()=>{if(currentTab==='review')prefer(market)},250);
})();
