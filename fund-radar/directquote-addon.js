// V2.12: direct per-symbol fallback when Eastmoney clist JSONP is blocked/unstable on iOS.
(function(){
'use strict';
const U='https://push2.eastmoney.com/api/qt/ulist.np/get';
const UT='fa5fd1943c7b386f172d6893dbfba10b';
const ids={A:'1.600519,1.601318,1.600036,0.000001,0.000333,0.300750,0.300308,0.300502,1.688981,1.688041,1.688012,1.600309,1.601899,0.002594,0.002475,0.002371,0.300476,0.300394,1.688318,0.002463,0.002837,0.300274,0.300124,0.000858,1.600030,1.601688,1.600276,0.000725,0.002230,0.002241',HK:'116.00700,116.09988,116.03690,116.01024,116.00981,116.01347,116.01810,116.09999,116.09618,116.09868,116.02015,116.01211,116.02318,116.00388,116.00883,116.00939,116.03988,116.02331,116.06618,116.09866'};
function url(m){return U+'?fltt=2&invt=2&ut='+UT+'&secids='+encodeURIComponent(ids[m])+'&fields=f2,f3,f5,f6,f8,f10,f12,f14,f62,f184'}
function norm(items){return (items||[]).filter(x=>x&&x.f14&&n(x.f2)>0).map(x=>({code:String(x.f12),name:x.f14,price:n(x.f2),pct:n(x.f3),amount:bn(x.f6),turn:n(x.f8),vr:n(x.f10),flow:n(x.f62),flowPct:n(x.f184),score:scoreStock(x)})).sort((a,b)=>b.score-a.score)}
const prev=loadMarket;
loadMarket=async function(m){const ok=await prev(m);if(state[m]&&state[m].live)return ok;try{const r=await jsonp(url(m),10000),stocks=norm(r&&r.data&&r.data.diff);if(stocks.length>=5){const old=state[m]||{};state[m]={stocks,sectors:old.sectors&&old.sectors.length&&old.sectors[0].code?old.sectors:[],live:true,sectorLive:false,stale:false,directFallback:true};try{const k='fundRadarLastLiveV211',a=JSON.parse(localStorage.getItem(k)||'{}');a[m]={t:Date.now(),stocks:state[m].stocks,sectors:state[m].sectors};localStorage.setItem(k,JSON.stringify(a))}catch(e){}return true}}catch(e){}return false};
const rr=render;render=function(){rr();const d=state[market]||{},b=document.getElementById('liveBadge');if(d.directFallback&&b){b.textContent='实盘行情 · 精选池';b.className='live'}};
setTimeout(async()=>{for(const m of ['A','HK'])if(!state[m].live)await loadMarket(m);saveHist();render()},1200);
})();