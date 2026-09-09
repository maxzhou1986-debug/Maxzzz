// V2.18: poll same-origin/raw full-market snapshots and show freshness instead of holding a stale in-memory copy.
(function(){
'use strict';
const mem={};
const min={A:1000,HK:100};
const RAW='https://raw.githubusercontent.com/maxzhou1986-debug/Maxzzz/main/fund-radar/data/';
const POLL_MS=75000;
function esc(v){return String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot',"'":'&#39;'}[c]))}
function pct(v){v=Number(v)||0;return (v>=0?'+':'')+v.toFixed(2)+'%'}
function money(v,m){v=Number(v)||0;return (v/1e8).toFixed(v>=1e10?0:1)+'亿'+(m==='A'?'元':'港元')}
function ageMin(d){const t=Date.parse(d||'');return Number.isFinite(t)?Math.max(0,Math.round((Date.now()-t)/60000)):9999}
function freshness(d){const a=ageMin(d.generatedAt);if(a<=10)return '近实时 · '+a+'分钟前';if(a<=25)return '轻微延迟 · '+a+'分钟前';return '数据偏旧 · '+a+'分钟前'}
function list(items,m,flow=false){if(!items||!items.length)return '<div class="empty">暂无数据</div>';return '<div class="list">'+items.map((x,i)=>'<div class="reviewRow"><div><b>'+(i+1)+'. '+esc(x.name)+'</b><div class="meta">'+esc(x.code||'')+' · 成交 '+money(x.amount,m)+'</div></div><div class="right '+((flow?x.flow:x.pct)>=0?'up':'down')+'">'+(flow?money(x.flow,m):pct(x.pct))+'</div></div>').join('')+'</div>'}
function section(t,b){return '<section class="section"><div class="st"><h2>'+t+'</h2></div>'+b+'</section>'}
async function readJson(url){const r=await fetch(url+(url.includes('?')?'&':'?')+'ts='+Date.now(),{cache:'no-store'});if(!r.ok)throw new Error('snapshot '+r.status);return r.json()}
async function get(m){
  const urls=['./data/review-'+m+'.json',RAW+'review-'+m+'.json'];
  let best=null;
  for(const url of urls){
    try{
      const d=await readJson(url);
      if(!d||d.market!==m||Number(d.coverage||0)<min[m])continue;
      d._via=url.startsWith('http')?'仓库直读':'Pages同源';
      if(!best || Date.parse(d.generatedAt||0)>Date.parse(best.generatedAt||0))best=d;
    }catch(e){}
  }
  if(best)mem[m]=best;
  return best;
}
function render(d){if(!d||currentTab!=='review'||market!==d.market)return false;const m=d.market,b=d.breadth||{},box=document.getElementById('reviewBody'),status=document.getElementById('reviewStatus');if(!box)return false;const full=!!d.complete;const fresh=freshness(d);const liveish=ageMin(d.generatedAt)<=15;box.innerHTML='<div class="card"><strong>'+esc(d.date)+' · '+(m==='A'?'A股':'港股')+' · '+(liveish?'盘中高覆盖快照':(full?'完整市场快照':'高覆盖市场快照'))+'</strong><div class="mini">覆盖 '+Number(d.coverage||0)+' / '+Number(d.total||0)+' 只 · 生成 '+esc(d.generatedAt||'')+' · '+esc(d._via||'服务器快照')+' · '+fresh+'。盘中后台约每5分钟尝试更新；GitHub 调度可能有数分钟延迟。</div></div>'+section('市场概览','<div class="reviewMetrics"><div class="metric"><b>'+Number(b.up||0)+'</b><span>上涨</span></div><div class="metric"><b>'+Number(b.down||0)+'</b><span>下跌</span></div><div class="metric"><b>'+Number(b.flat||0)+'</b><span>平盘</span></div><div class="metric"><b>'+money(b.amount,m)+'</b><span>成交额</span></div></div>'+list(d.indices||[],m,false))+section('最强板块 Top 5',list(d.strong||[],m,false))+section('最弱板块 Top 5',list(d.weak||[],m,false))+section('板块资金净流入 Top 5',list(d.inflow||[],m,true))+section('板块资金净流出 Top 5',list(d.outflow||[],m,true))+section('当日龙头与核心强势候选',list(d.leaders||[],m,false))+section('市场情绪：'+esc(d.emotion||'数据不足'),'<div class="card mini">当前全市场广度来自高覆盖快照。新浪备用源缺少主力净流入字段时，资金榜不会伪造，继续显示“暂无数据”。</div>')+'<p class="notice">复盘页现在会自动轮询最新服务器快照，不再把第一次打开时的数据永久缓存。盘中目标是约5分钟级，不是逐秒行情。</p>';if(status){status.textContent=fresh+' · '+d.coverage+'只';status.classList.toggle('warn',!liveish)}return true}
async function prefer(m=market,force=false){if(currentTab!=='review')return false;const status=document.getElementById('reviewStatus');if(status&&force)status.textContent='正在拉取最新市场快照…';const d=force?await get(m):(mem[m]||await get(m));if(!d){if(status)status.textContent='服务器快照尚未生成';return false}return render(d)}
const oldShow=showTab;showTab=function(t){oldShow(t);if(t==='review')setTimeout(()=>prefer(market,true),60)};
const oldSwitch=switchMarket;switchMarket=function(m){oldSwitch(m);if(currentTab==='review')setTimeout(()=>prefer(m,true),60)};
document.getElementById('reviewRefresh')?.addEventListener('click',()=>{if(currentTab==='review')setTimeout(()=>prefer(market,true),80)});
setInterval(()=>{if(currentTab==='review')prefer(market,true)},POLL_MS);
setTimeout(()=>{if(currentTab==='review')prefer(market,true)},500);
})();
