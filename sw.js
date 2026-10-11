const CACHE_NAME = 'safar360-v8';
const ASSETS = [
  '/',
  '/index.html',
  '/styles.css',
  '/app.js',
  '/characters-public.json',
  '/manifest.json',
  '/cinema.html',
  '/cinema.json',
  '/khizana.html',
  '/products.json',
  '/assets/images/khizana-items/astrolabe-arabic-decorative.jpg',
  '/assets/images/khizana-items/journal-nomadcrafts.jpg',
  '/assets/images/khizana-items/meditations-deluxe-9781640956988.jpg',
  '/assets/images/khizana-items/hourglass-bellaware-black-sand.jpg',
  '/assets/images/khizana-items/pilot-metal-falcon-black.jpg',
  '/assets/images/khizana-items/globe-calif-international-vintage.jpg',
  '/assets/images/khizana-items/magnifier-brass-handle-5x.jpg',
  '/assets/images/khizana-items/candelabra-antique-brass-finish.jpg',
  '/assets/images/khizana-items/don-quixote-penguin-clothbound.jpg',
  '/assets/images/khizana-items/wax-seal-letter-a.jpg',
  '/assets/images/sard360-logo.png'
];

self.addEventListener('install', (e) => {
  e.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => cache.addAll(ASSETS))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys().then((keyList) => {
      return Promise.all(keyList.map((key) => {
        if (key !== CACHE_NAME) {
          return caches.delete(key);
        }
      }));
    })
  );
  return self.clients.claim();
});

self.addEventListener('fetch', (e) => {
  const requestUrl = new URL(e.request.url);
  // Let WordPress, YouTube, Google Fonts and other third-party APIs/assets use the network directly.
  if (requestUrl.origin !== self.location.origin) return;
  // Do not intercept or cache API calls to ensure live interactions
  if (requestUrl.pathname.includes('/api/')) {
    return;
  }

  const isKhizanaPage = /^\/khizana(?:\/|\.html)?$/.test(requestUrl.pathname);
  const isKhizanaCatalog = /^\/(?:khizana\/)?products\.json$/.test(requestUrl.pathname);
  const isCinemaPage = /^\/cinema(?:\/|\.html)?$/.test(requestUrl.pathname);
  const isCinemaCatalog = /^\/cinema\.json$/.test(requestUrl.pathname);
  if (isKhizanaPage || isKhizanaCatalog || isCinemaPage || isCinemaCatalog) {
    e.respondWith(
      fetch(e.request).then((fetchRes) => {
        if (e.request.method === 'GET' && fetchRes.status === 200) {
          return caches.open(CACHE_NAME).then((cache) => {
            return cache.put(e.request, fetchRes.clone()).then(() => fetchRes);
          });
        }
        return fetchRes;
      }).catch(() => caches.match(e.request).then((res) => {
        if (res) return res;
        if ((e.request.headers.get('accept') || '').includes('text/html')) {
          return caches.match('/index.html');
        }
      }))
    );
    return;
  }

  e.respondWith(
    caches.match(e.request).then((res) => {
      return res || fetch(e.request).then((fetchRes) => {
        return caches.open(CACHE_NAME).then((cache) => {
          // Cache successful GET responses only
          if (e.request.method === 'GET' && fetchRes.status === 200) {
            cache.put(e.request, fetchRes.clone());
          }
          return fetchRes;
        });
      });
    }).catch(() => {
      // Offline fallback
      if ((e.request.headers.get('accept') || '').includes('text/html')) {
        return caches.match('/index.html');
      }
    })
  );
});
