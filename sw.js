const CACHE_NAME = 'safar360-v2';
const ASSETS = [
  '/',
  '/index.html',
  '/styles.css',
  '/app.js',
  '/characters-public.json',
  '/manifest.json'
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
  // Do not intercept or cache API calls to ensure live interactions
  if (e.request.url.includes('/api/')) {
    return;
  }
  
  const requestUrl = new URL(e.request.url);
  const isKhizanaPage = /^\/khizana(?:\/|\.html)?$/.test(requestUrl.pathname);
  const isKhizanaCatalog = /^\/(?:khizana\/)?products\.json$/.test(requestUrl.pathname);
  if (isKhizanaPage || isKhizanaCatalog) {
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
