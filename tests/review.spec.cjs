const assert=require('node:assert/strict');
const http=require('node:http');
const fs=require('node:fs');
const path=require('node:path');
const playwright=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const engine=process.env.TEST_BROWSER||'webkit';
const root=path.resolve(__dirname,'../fund-radar');
const stamp=Date.parse('2026-09-08T08:15:00Z')/1000;
const server=http.createServer((req,res)=>{const p=path.join(root,new URL(req.url,'http://localhost').pathname.replace(/^\/fund-radar\//,''));try{res.setHeader('Content-Type',p.endsWith('.js')?'application/javascript':'text/html');res.end(fs.readFileSync(p));}catch(e){res.writeHead(404);res.end();}});
(async()=>{await new Promise(r=>server.listen(0,'127.0.0.1',r));const browser=await playwright[engine].launch({headless:true});try{
const page=await browser.newPage({viewport:{width:375,height:812},isMobile:true,hasTouch:true,serviceWorkers:'block'});const errors=[];page.on('pageerror',e=>errors.push(e.message));let mode='normal';
await page.addInitScript(()=>{window.__REVIEW_TEST__={};Date.now=()=>Date.parse('2026-09-08T09:00:00Z');});
await page.route('https://**eastmoney.com/**',async route=>{const u=new URL(route.request().url()),isReview=(u.searchParams.get('cb')||'').startsWith('review_');if(mode==='offline'&&isReview)return route.abort();const filter=u.searchParams.get('fs')||'',pn=+u.searchParams.get('pn')||1,pz=+u.searchParams.get('pz')||100;let diff=[],total=205;
if(u.pathname.includes('ulist')){diff=(u.searchParams.get('secids')||'').split(',').map(id=>({f12:id.split('.')[1],f13:100,f14:id,f3:1.2,f6:500000000,f124:stamp}));total=diff.length;}
else if(filter==='m:124'||filter==='m:90+t:2'){total=12;diff=Array.from({length:12},(_,i)=>({f12:filter==='m:124'?'H'+i:'BK'+i,f13:filter==='m:124'?124:90,f14:'行业'+i,f3:i-5,f6:1e9,f62:(i-5)*1e8,f124:stamp}));}
else if(filter.startsWith('b:')){total=0;}
else {let offset=(pn-1)*pz;if(mode==='repeat'&&isReview)offset=0;diff=Array.from({length:Math.max(0,Math.min(pz,total-offset))},(_,j)=>{const i=offset+j;return {f12:String(100000+i),f13:filter.includes('128')?128:0,f14:'测试股'+i,f2:10,f3:i%5===0?-2:2,f6:1e8+i*1e6,f62:i%2?'-':1e7,f10:1.2,f100:'行业'+i%12,f124:stamp};});}
const data={rc:0,data:{total,diff}};const cb=u.searchParams.get('cb');await route.fulfill({contentType:cb?'application/javascript':'application/json',body:cb?cb+'('+JSON.stringify(data)+')':JSON.stringify(data)});});
await page.goto('http://127.0.0.1:'+server.address().port+'/fund-radar/v2.html');await page.waitForFunction(()=>window.__REVIEW_TEST__.api);await page.waitForFunction(()=>document.querySelector('#reviewStatus').textContent==='复盘已更新');
for(const t of ['review','radar','flow','night','build','rebound','watch','review']){await page.evaluate(t=>showTab(t),t);assert.equal(await page.locator('#panel'+t[0].toUpperCase()+t.slice(1)).isVisible(),true,t);assert.equal(await page.locator('.subtabs .active').count(),1);assert.equal(await page.locator('.nav .active').count(),1);}
await page.waitForFunction(()=>document.querySelector('#reviewBody').textContent.includes('收盘后复盘'));
assert(await page.locator('#reviewBody').textContent().then(t=>t.includes('205 / 205')&&t.includes('高潮')));
await page.evaluate(()=>switchMarket('HK'));await page.waitForFunction(()=>document.querySelector('#reviewBody').textContent.includes('港股 · 收盘后复盘'));assert((await page.locator('#reviewBody').textContent()).includes('港元'));
assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true,'375px no page overflow');
await page.setViewportSize({width:320,height:700});assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true,'320px no page overflow');
const unit=await page.evaluate(async()=>{const a=window.__REVIEW_TEST__.api;return {missing:[a.num('-'),a.num(null),a.num('')],zero:a.num(0),negative:a.num('-10'),emotion:a.emotion({up:50,count:100},true).label,incomplete:a.emotion({up:80,count:100},false).label,rollover:a.clock(Date.parse('2026-09-08T16:00:00Z')).date,saved:!!a.latest('HK'),stockCount:(await a.all('m:128+t:1')).rows.length};});assert.deepEqual(unit,{missing:[null,null,null],zero:0,negative:-10,emotion:'分歧',incomplete:'数据不足',rollover:'2026-09-09',saved:true,stockCount:205});
mode='repeat';const repeated=await page.evaluate(()=>window.__REVIEW_TEST__.api.all('m:128+t:1'));assert.equal(repeated.complete,false);assert.equal(repeated.rows.length,100);
mode='offline';await page.evaluate(()=>window.__REVIEW_TEST__.api.refresh('HK'));assert((await page.locator('#reviewStatus').textContent()).includes('保留上次快照'));assert((await page.locator('#reviewBody').textContent()).includes('本机历史快照'));
assert.deepEqual(errors,[]);console.log('PASS '+engine+': seven tabs, A/HK switching, full pagination, duplicates, null fields, timezone, sentiment, local snapshots, offline fallback, 320/375px layout, no script errors.');
await page.screenshot({path:path.resolve(__dirname,'../../review-browser.png'),fullPage:true});
}finally{await browser.close();server.close();}})().catch(e=>{console.error(e);server.close();process.exitCode=1;});
