// const CACHE_NAME = 'v6';

// self.addEventListener('install', (event) => {
//   self.skipWaiting();
// });

// self.addEventListener('activate', (event) => {
//   event.waitUntil(
//     caches.keys().then((keys) =>
//       Promise.all(keys.filter((key) => key !== CACHE_NAME)
//         .map((key) => caches.delete(key))
//       )
//     )
//   );
// });

// self.addEventListener('fetch', (event) => {
//   event.respondWith(
//     caches.match(event.request)
//       .then((cachedResponse) => {
//         if (cachedResponse) {
//           return cachedResponse;
//         }
//         return fetch(event.request)
//           .then((response) => {
//             if (event.request.method === 'GET' && response.ok && !event.request.url.includes('/api/')) {
//               caches.open(CACHE_NAME).then((cache) => cache.put(event.request, response.clone()));
//             }
//             return response;
//           });
//       })
//   );
// });


// serviceworker.js
const CACHE_NAME = 'tutorial-haven-v7';

// Pre-cache home, login, and courses 1–9, plus static assets
const ASSETS = [
  '/',                // home page
  '/login/',          // login page
  // Courses 1–9
  '/courses/1/',
  '/courses/2/',
  '/courses/3/',
  '/courses/4/',
  '/courses/5/',
  '/courses/6/',
  '/courses/7/',
  '/courses/8/',
  '/courses/9/',
  // Static assets your pages depend on
  '/css/main.css',
  '/css/login.css',
  '/js/main.js',
  '/js/login.js',
  '/icons/192.png',
  '/icons/512.png',
  '/manifest.json',
];

// INSTALL: cache all assets
self.addEventListener('install', (event) => {
  console.log('[SW] Installing Service Worker and caching assets...');
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => cache.addAll(ASSETS))
      .then(() => self.skipWaiting())
  );
});

// ACTIVATE: clean up old caches
self.addEventListener('activate', (event) => {
  console.log('[SW] Activating Service Worker...');
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys.filter((key) => key !== CACHE_NAME)
            .map((key) => caches.delete(key))
      )
    )
  );
  self.clients.claim();
});

// FETCH: serve from cache first, then network, fallback offline page
self.addEventListener('fetch', (event) => {
  const { request } = event;

  // Only handle GET requests
  if (request.method !== 'GET') return;

  event.respondWith(
    caches.match(request).then((cachedResponse) => {
      if (cachedResponse) return cachedResponse;

      // Try network
      return fetch(request).then((response) => {
        // Cache GET requests (avoid API calls)
        if (response.status === 200 && !request.url.includes('/api/')) {
          caches.open(CACHE_NAME).then((cache) => cache.put(request, response.clone()));
        }
        return response;
      }).catch(() => {
        // Offline fallback for navigation requests
        if (request.mode === 'navigate') {
          // Serve home page or login page if offline
          return caches.match('/') || caches.match('/login/');
        }
      });
    })
  );
});