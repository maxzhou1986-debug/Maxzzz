const cacheName = 'anwen-offline-v1';
const home = new URL('./', self.location.href).href;
self.addEventListener('install', event => {
  event.waitUntil(self.skipWaiting());
});
self.addEventListener('activate', event => {
  event.waitUntil(self.clients.claim());
});
self.addEventListener('fetch', event => {
  if (event.request.mode !== 'navigate' || event.request.url !== home) return;
  event.respondWith((async () => {
    let response;
    try {
      response = await fetch(event.request);
    } catch {
      return (await caches.match(home, { cacheName })) || Response.error();
    }
    if (response.ok && !response.redirected && (response.headers.get('Content-Type') || '').includes('text/html')) {
      try {
        const candidate = response.clone();
        if ((await candidate.text()).includes('anwen-reminders-v1')) {
          await (await caches.open(cacheName)).put(home, response.clone());
        }
      } catch {}
    }
    return response;
  })());
});
