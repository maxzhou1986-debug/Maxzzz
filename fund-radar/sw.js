const CACHE='fund-radar-v2.10';
const ASSETS=['./','./index.html','./v2.html','./app-v2.js?v=210','./sector-addon.js?v=210','./watch-addon.js?v=210','./build-addon.js?v=210','./rebound-addon.js?v=210','./review-addon.js?v=210','./manifest.webmanifest','./icon.svg'];
self.addEventListener('install',e=>e.waitUntil(caches.open(CACHE).then(c=>c.addAll(ASSETS)).then(()=>self.skipWaiting())));
self.addEventListener('activate',e=>e.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(k=>k.startsWith('fund-radar-')&&k!==CACHE).map(k=>caches.delete(k)))).then(()=>self.clients.claim())));
self.addEventListener('fetch',e=>{
 const u=new URL(e.request.url);
 if(e.request.method!=='GET'||u.origin!==self.location.origin||!u.pathname.startsWith(new URL('./',self.location.href).pathname))return;
 // Legacy V2.9 clients still expect concatenated add-ons. New HTML loads each explicitly.
 if(u.pathname.endsWith('/app-v2.js')&&!u.searchParams.has('v')){
  e.respondWith(caches.open(CACHE).then(async c=>{const parts=await Promise.all(ASSETS.filter(x=>x.includes('.js?')).map(x=>c.match(x)));if(parts.some(x=>!x))throw new Error('Missing app script');return new Response((await Promise.all(parts.map(x=>x.text()))).join('\n'),{headers:{'Content-Type':'application/javascript; charset=utf-8'}});}));return;
 }
 e.respondWith(fetch(e.request).then(r=>{if(r.ok){const copy=r.clone();caches.open(CACHE).then(c=>c.put(e.request,copy)).catch(()=>{});}return r;}).catch(async()=>{const hit=await caches.match(e.request);if(hit)return hit;if(e.request.mode==='navigate')return (await caches.match('./v2.html'))||Response.error();return Response.error();}));
});
