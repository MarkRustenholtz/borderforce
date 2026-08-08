const CACHE_NAME = 'bf-suite-v65-sncf-hors-ligne';
const URLS_TO_CACHE = [
  './',
  './index.html',
  './borderforce/index.html',
  './compteur/index.html',
  './manifest.json',
  './trains-sncf-roya.js',
  './trains-trenitalia-roya.js',
  './borderforce/trains-sncf-roya.js',
  './borderforce/trains-trenitalia-roya.js',
  './html/index.html',
  './html/trains-sncf-roya.js',
  './html/trains-trenitalia-roya.js',
  './borderforce/html/index.html',
  './borderforce/html/trains-sncf-roya.js',
  './borderforce/html/trains-trenitalia-roya.js'
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => Promise.allSettled(URLS_TO_CACHE.map(url => cache.add(url))))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys()
      .then(keys => Promise.all(keys.filter(key => key !== CACHE_NAME).map(key => caches.delete(key))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', event => {
  if (event.request.method !== 'GET') return;

  if (event.request.mode === 'navigate') {
    event.respondWith(
      fetch(event.request)
        .then(response => {
          const copy = response.clone();
          caches.open(CACHE_NAME).then(cache => cache.put(event.request, copy));
          return response;
        })
        .catch(() => caches.match(event.request).then(cached => cached || caches.match('./index.html')))
    );
    return;
  }

  event.respondWith(
    caches.match(event.request).then(cached => cached || fetch(event.request).then(response => {
      const copy = response.clone();
      caches.open(CACHE_NAME).then(cache => cache.put(event.request, copy));
      return response;
    }))
  );
});
