// V2.16: prefer server-generated full-market review snapshots; fall back to raw repo JSON so Pages rebuild lag cannot hide fresh data.
(function(){
'use strict';
const mem={};
const min={A:1000,HK:100};
const RAW='https://raw.githubusercontent.com/maxzhou1986-debug/Maxzzz/main/fund-radar/data/';
function esc(v){return String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
function pct(v){v=Number(v)||0;return (v>=0?'+':'')+v.toFixed(2)+'%'}
function money(v,m){v=Number(v)||0;return (v/1e8).toFixed(v>=1e10?0:1)+'亿'+(m==='A'?'元':'港元')}
function list(items,m,flow=false){if(!items||!items.length)return '<div class="empty">暂无数据</div>';return '<div class="list">'+items.map((x,i)=>'<div class="reviewRow"><div><b>'+(i+1)+'. '+esc(x.name)+'</b><div class="meta">'+esc(x.code||'')+' · 成交 '+money(x.amount,m)+'</div></div><div class="right '+((flow?x.flow:x.pct)>=0?'up':'down')+'">'+(flow?money(x.flow,m):pct(x.pct))+'</div></div>').join('')+'</div>'}
function section(t,b){return '<section class="section"><div class="st"><h2>'+t+'</h2></div>'+b+'</section>'}
async function readJson(url){const r=await fetch(url+(url.includes('?')?'&':'?')+'ts='+Date.now(),{cache:'no-store'});if(!r.ok)throw new Error('snapshot '+r.status);return r.json()}
async function get(m){
  const urls=['./data/review-'+m+'.json',RAW+'review-'+m+'.json'];
  for(const url of urls){
    try{
      const d=await readJson(url);
      if(!d||d.market!==m||Number(d.coverage||0)<min[m])throw new Error('coverage');
      d._via=url.startsWith('http')?'仓库直读':'Pages同源';
      mem[m]=d;return d;
    }catch(e){}
  }
  return null;
}
function render(d){if(!d||currentTab!=='review'||market!==d.market)return false;const m=d.market,b=d.breadth||{},box=document.getElementById('reviewBody'),status=document.getElementById('reviewStatus');if(!box)return false;const full=!!d.complete;box.innerHTML='<div class="card"><strong>'+esc(d.date)+' · '+(m==='A'?'A股':'港股')+' · '+(full?'完整收盘快照':'高覆盖收盘快照')+'</strong><div class="mini">服务器收盘后自动保存 · 覆盖 '+Number(d.coverage||0)+' / '+Number(d.total||0)+' 只 · 生成 '+esc(d.generatedAt||'')+' · '+esc(d._via||'服务器快照')+'。盘前/休市直接读取上一交易日结果，不依赖 iPhone 临时连接行情接口。</div></div>'+section('市场概览','<div class="reviewMetrics"><div class="metric"><b>'+Number(b.up||0)+'</b><span>上涨</span></div><div class="metric"><b>'+Number(b.down||0)+'</b><span>下跌</span></div><div class="metric"><b>'+Number(b.flat||0)+'</b><span>平盘</span></div><div class="metric"><b>'+money(b.amount,m)+'</b><span>成交额</span></div></div>'+list(d.indices||[],m,false))+section('最强板块 Top 5',list(d.strong||[],m,false))+section('最弱板块 Top 5',list(d.weak||[],m,false))+section('板块资金净流入 Top 5',list(d.inflow||[],m,true))+section('板块资金净流出 Top 5',list(d.outflow||[],m,true))+section('当日龙头与核心强势候选',list(d.leaders||[],m,false))+section('市场情绪：'+esc(d.emotion||'数据不足'),'<div class="card mini">基于全市场上涨/下跌广度判断。收盘快照优先用于第二天盘前复盘；盘中实时雷达仍走实时行情。</div>')+'<p class="notice">如果 GitHub Pages 更新稍慢，本页会直接读取仓库里的最新 JSON，因此不会再因为 Pages 部署延迟而退回 8 只代表池。</p>';if(status)status.textContent=(full?'完整':'高覆盖')+'市场快照 · '+d.coverage+'只 · '+(d._via||'服务器');return true}
async function prefer(m=market){if(currentTab!=='review')return false;const status=document.getElementById('reviewStatus');if(status)status.textContent='正在读取收盘全市场快照…';const d=mem[m]||await get(m);if(!d){if(status)status.textContent='服务器快照尚未生成';return false}return render(d)}
const oldShow=showTab;showTab=function(t){oldShow(t);if(t==='review')setTimeout(()=>prefer(market),60)};
const oldSwitch=switchMarket;switchMarket=function(m){oldSwitch(m);if(currentTab==='review')setTimeout(()=>prefer(m),60)};
document.getElementById('reviewRefresh')?.addEventListener('click',()=>{if(currentTab==='review'){delete mem[market];setTimeout(()=>prefer(market),80)}});
setTimeout(()=>{if(currentTab==='review')prefer(market)},500);
})();