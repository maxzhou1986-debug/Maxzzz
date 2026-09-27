const C="radar-v30";
self.addEventListener("install",e=>{self.skipWaiting();e.waitUntil(caches.open(C).then(c=>c.addAll(["./","./index.html","./style.css?v=30","./charts.js?v=30","./app.js?v=30"])))});
self.addEventListener("activate",e=>e.waitUntil(Promise.all([caches.keys().then(keys=>Promise.all(keys.filter(k=>k!==C).map(k=>caches.delete(k)))),self.clients.claim()])));
self.addEventListener("fetch",e=>{const u=new URL(e.request.url);if(u.pathname.includes("/data/")&&u.pathname.endsWith(".json")){e.respondWith(fetch(e.request,{cache:"no-store"}));return}e.respondWith(fetch(e.request).then(r=>{const copy=r.clone();caches.open(C).then(c=>c.put(e.request,copy));return r}).catch(()=>caches.match(e.request)))});
