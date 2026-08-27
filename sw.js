self.addEventListener('install', (e) => {
  console.log('Service Worker installed');
});

self.addEventListener('fetch', (e) => {
  // מאפשר לאפליקציה לרוץ חלק
  e.respondWith(fetch(e.request).catch(() => caches.match(e.request)));
});
