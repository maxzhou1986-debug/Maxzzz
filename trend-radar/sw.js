const C="radar-v42";
const CORE=["./","./index.html","./style.css?v=42","./charts.js?v=42","./app.js?v=42"];
self.addEventListener("install",e=>{self.skipWaiting();e.waitUntil(caches.open(C).then(c=>c.addAll(CORE)))});
self.addEventListener("activate",e=>e.waitUntil(Promise.all([caches.keys().then(keys=>Promise.all(keys.filter(k=>k!==C).map(k=>caches.delete(k)))),self.clients.claim()])));
self.addEventListener("fetch",e=>{
 const u=new URL(e.request.url);
 if(u.pathname.includes("/data/")&&u.pathname.endsWith(".json")){e.respondWith(fetch(e.request,{cache:"no-store"}));return}
 if(e.request.mode==="navigate"){e.respondWith(fetch(e.request,{cache:"no-store"}).then(r=>{const copy=r.clone();caches.open(C).then(c=>c.put("./index.html",copy));return r}).catch(()=>caches.match("./index.html")));return}
 e.respondWith(fetch(e.request).then(r=>{const copy=r.clone();caches.open(C).then(c=>c.put(e.request,copy));return r}).catch(()=>caches.match(e.request)))
});
