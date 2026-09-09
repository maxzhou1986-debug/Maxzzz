const CACHE='fund-radar-v2.11';
const ASSETS=['./','./index.html','./v2.html','./app-v2.js?v=211','./livefix-addon.js?v=211','./sector-addon.js?v=211','./watch-addon.js?v=211','./build-addon.js?v=211','./rebound-addon.js?v=211','./review-addon.js?v=211','./manifest.webmanifest','./icon.svg'];
self.addEventListener('install',e=>e.waitUntil(caches.open(CACHE).then(c=>c.addAll(ASSETS)).then(()=>self.skipWaiting())));
self.addEventListener('activate',e=>e.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(k=>k.startsWith('fund-radar-')&&k!==CACHE).map(k=>caches.delete(k)))).then(()=>self.clients.claim())));
self.addEventListener('fetch',e=>{
 const u=new URL(e.request.url);
 if(e.request.method!=='GET'||u.origin!==self.location.origin||!u.pathname.startsWith(new URL('./',self.location.href).pathname))return;
 e.respondWith(fetch(e.request,{cache:'no-store'}).then(r=>{if(r.ok){const copy=r.clone();caches.open(CACHE).then(c=>c.put(e.request,copy)).catch(()=>{});}return r;}).catch(async()=>{const hit=await caches.match(e.request);if(hit)return hit;if(e.request.mode==='navigate')return (await caches.match('./v2.html'))||Response.error();return Response.error();}));
});
