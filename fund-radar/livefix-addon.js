// V2.11 live quote resilience: stock and sector requests are independent, with retries.
(function(){
'use strict';
const LAST_KEY='fundRadarLastLiveV211';
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
function readLast(){try{return JSON.parse(localStorage.getItem(LAST_KEY)||'{}')}catch(e){return {}}}
function writeLast(m){try{const all=readLast();const d=state[m];if(d&&d.stocks&&d.stocks.length){all[m]={t:Date.now(),stocks:d.stocks,sectors:d.sectors||[]};localStorage.setItem(LAST_KEY,JSON.stringify(all));}}catch(e){}}
async function retry(url,times,timeout){let err;for(let i=0;i<times;i++){try{return await jsonp(url,timeout)}catch(e){err=e;if(i<times-1)await sleep(250+250*i)}}throw err||new Error('network')}
const originalLoad=loadMarket;
loadMarket=async function(m){
  const prev=state[m]||{stocks:[],sectors:[],live:false};
  const [sr,br]=await Promise.allSettled([
    retry(stockUrl(m),3,9000),
    retry(sectorUrl(m),2,9000)
  ]);
  const stocks=sr.status==='fulfilled'?normalizeStocks(sr.value?.data?.diff):[];
  const sectors=br.status==='fulfilled'?normalizeSectors(br.value?.data?.diff):[];
  if(stocks.length){
    state[m]={stocks,sectors:sectors.length?sectors:(prev.sectors||[]),live:true,sectorLive:!!sectors.length,stale:false};
    writeLast(m);
    return true;
  }
  // Do not turn the whole app into demo data just because one public request failed.
  if(prev.live&&prev.stocks&&prev.stocks.length){state[m]={...prev,stale:true};return false}
  const last=readLast()[m];
  if(last&&Array.isArray(last.stocks)&&last.stocks.length){state[m]={stocks:last.stocks,sectors:Array.isArray(last.sectors)?last.sectors:[],live:true,sectorLive:false,stale:true,lastLiveAt:last.t||0};return false}
  // Only use demo when there has never been a real snapshot on this device and all stock retries failed.
  const f=fallback(m);state[m]={...f,live:false,sectorLive:false,stale:false};return false;
};
const baseRender=render;
render=function(){
  baseRender();
  const d=state[market]||{};
  const badge=document.getElementById('liveBadge');
  if(!badge)return;
  if(d.live&&d.stale){badge.textContent='行情暂断 · 上次实盘';badge.className='live off'}
  else if(d.live&&d.sectorLive===false){badge.textContent='个股实时 · 板块重试中';badge.className='live'}
};
// Core starts loading before add-ons execute. Re-run once with the resilient loader so a sector timeout cannot leave the page in demo mode.
setTimeout(async()=>{try{await Promise.all([loadMarket('A'),loadMarket('HK')]);saveHist();render()}catch(e){}},350);
})();