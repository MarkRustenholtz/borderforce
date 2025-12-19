const CACHE_NAME = 'bf-suite-v24';
const URLS_TO_CACHE = [
  './',
  './index.html',
  './borderforce/index.html',
  './images/fond-tech.jpg',
  './manifest.json', 
  './compteur/index.html'
  // tu peux ajouter d'autres fichiers si tu veux du full offline
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => cache.addAll(URLS_TO_CACHE))
  );
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(
        keys
          .filter(k => k !== CACHE_NAME)
          .map(k => caches.delete(k))
      )
    )
  );
});

self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request).then(resp => resp || fetch(event.request))
  );
});
