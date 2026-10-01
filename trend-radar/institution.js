(function(){
'use strict';
function esc(s){return String(s==null?'—':s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}
function cls(x){return x==='回流'?'green':x==='流出'?'red':'amber';}
async function render(){
 const root=document.querySelector('#institutional'); if(!root)return;
 try{
  const r=await fetch('./data/institutional.json?ts='+Date.now(),{cache:'no-store'}); if(!r.ok)throw 0;
  const d=await r.json(), x=d.stocks&&d.stocks['300308.SZ']; if(!x)throw 0;
  root.innerHTML='<article class="holding"><div><b>机构筹码 · 中际旭创A</b><small>公募/公开机构披露 · '+esc(x.asOf)+'</small><small class="holdingActionNote">'+esc(x.note)+'</small></div><div class="holdingNums"><b class="'+cls(x.state)+'">'+esc(x.state)+'</b><small>公募持股 '+esc(x.fundShares)+' · 环比 '+esc(x.qoq)+'</small><small>流通占比 '+esc(x.floatPct)+' · 股东户数 '+esc(x.holders)+'</small></div><div class="holdingSignals"><span class="pill '+cls(x.state)+'">机构 '+esc(x.state)+'</span><span class="pill '+(x.retailState==='下降'?'green':'amber')+'">散户 '+esc(x.retailState)+'</span></div></article>';
 }catch(e){root.innerHTML='<article class="holding"><div><b>机构筹码</b><small>等待最新公开披露数据</small></div><div class="holdingSignals"><span class="pill amber">数据待更新</span></div></article>';}
}
document.addEventListener('DOMContentLoaded',render);
})();