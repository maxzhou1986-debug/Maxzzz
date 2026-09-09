const vm=require('node:vm'),fs=require('node:fs'),assert=require('node:assert/strict');
function harness(kind,request,opts={}){
 const els=new Map();function el(id){if(!els.has(id))els.set(id,{innerHTML:'',classList:{add(){},remove(){}},appendChild(){},insertBefore(){},querySelector(){return null}});return els.get(id)}
 const ctx={console,window:{},document:{createElement(){return el('created'+els.size)},head:el('head'),querySelector(s){return el(s)},getElementById:el},market:'A',currentTab:kind,state:{A:{live:true,sectorLive:true,stocks:[],sectors:[{code:'BK001',name:'行业',pct:1,score:80}]},HK:{live:true,sectors:[]}},showTab(){},render(){},cap:s=>s[0].toUpperCase()+s.slice(1),EM:'https://example.test/list',jsonp:request,n:v=>Number(v)||0,bn:v=>(Number(v)||0)/1e8,clamp:(v,a,b)=>Math.max(a,Math.min(b,v)),nearestSnapshot:()=>null,accelForStock:()=>null,normalizeStocks:xs=>xs.filter(x=>x.f2>0).map(x=>({code:x.f12,name:x.f14,price:x.f2,pct:x.f3,score:80,amount:1,vr:1.5,turn:2})),fmtAmt:()=>'',isWatched:()=>false,...opts};
 vm.createContext(ctx);vm.runInContext(fs.readFileSync(__dirname+'/../fund-radar/'+(kind==='build'?'build':'rebound')+'-addon.js','utf8'),ctx);return {ctx,el,async scan(){ctx.showTab(kind);for(let i=0;i<20;i++)await new Promise(r=>setImmediate(r));return el(kind+'List').innerHTML}};
}
const stock={f12:'600001',f14:'测试',f2:10,f3:1,f6:1e8};
const list={rc:0,data:{diff:[stock]}};
(async()=>{
 let h=harness('rebound',async u=>{if(u.includes('kline'))throw Error('offline');return list});assert.match(await h.scan(),/日K数据不可用/);assert.match(h.el('reboundList').innerHTML,/请求失败 1/);
 h=harness('rebound',async u=>u.includes('kline')?{data:{klines:[]}}:list);assert.match(await h.scan(),/日K不足 1/);
 h=harness('rebound',async()=>({rc:0,data:null}));assert.match(await h.scan(),/接口暂时/);
 const klines=Array.from({length:25},(_,i)=>`2026-08-${String(i+1).padStart(2,'0')},10,${i===24?10.1:10},12,9.9,100,1000,0,0,0,2`);
 h=harness('rebound',async u=>u.includes('kline')?{data:{klines}}:{data:{diff:{0:stock}}});assert.match(await h.scan(),/日K有效 1/);
 h=harness('build',async()=>{throw Error('offline')});assert.match(await h.scan(),/成分股数据读取失败/);
 h=harness('build',async()=>({data:{diff:{0:stock}}}));const html=await h.scan();assert.match(html,/历史不足 · 待观察/);assert.match(html,/有效样本 1/);assert.doesNotMatch(html,/持续吸筹|明显建仓/);
 h=harness('build',async()=>list);h.ctx.state.A.sectorLive=false;assert.match(await h.scan(),/板块数据缺失/);
 h=harness('build',async()=>list,{market:'HK'});assert.match(await h.scan(),/映射尚未接通/);
 for(const kind of ['build','rebound']){h=harness(kind,async()=>list);h.ctx.state.A.stale=true;assert.match(await h.scan(),/行情已过期/)}
 h=harness('build',async()=>{h.ctx.market='HK';return list});assert.doesNotMatch(await h.scan(),/测试|暂无达到/);
 console.log('11 scanner regression scenarios passed');
})().catch(e=>{console.error(e);process.exitCode=1});
