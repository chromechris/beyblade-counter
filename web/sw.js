/* Service worker: makes the app installable and usable offline.
 * Bump SHELL_VERSION whenever index.html / app.js / style.css / the database change.
 * Photos are immutable, so they live in their own cache that survives shell updates. */
const SHELL_VERSION = 'beytelligence-shell-v3';
const IMG_CACHE = 'beycounter-img-v1';
const SHELL = ['./', './index.html', './style.css', './app.js', './manifest.webmanifest', './data/beyblade_x.json',
  './icons/icon-192.png', './icons/icon-512.png', './icons/apple-touch-icon.png', './icons/favicon.png'];

self.addEventListener('install', e => {
  e.waitUntil(caches.open(SHELL_VERSION).then(c => c.addAll(SHELL)).then(() => self.skipWaiting()));
});

self.addEventListener('activate', e => {
  e.waitUntil(caches.keys()
    .then(keys => Promise.all(keys.filter(k => k !== SHELL_VERSION && k !== IMG_CACHE).map(k => caches.delete(k))))
    .then(() => self.clients.claim()));
});

self.addEventListener('fetch', e => {
  const req = e.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);
  if (url.origin !== location.origin) return;
  if (url.pathname.includes('/img/')) {
    // photos: cache first, fetch once
    e.respondWith(caches.open(IMG_CACHE).then(async c => {
      const hit = await c.match(req);
      if (hit) return hit;
      const res = await fetch(req);
      if (res.ok) c.put(req, res.clone());
      return res;
    }));
    return;
  }
  // app shell + data: network first, fall back to the cache when offline
  e.respondWith(fetch(req).then(res => {
    if (res.ok) caches.open(SHELL_VERSION).then(c => c.put(req, res.clone()));
    return res;
  }).catch(() => caches.match(req, { ignoreSearch: true }).then(hit => hit || caches.match('./index.html'))));
});

/* The page sends the list of every photo after the database loads; we fetch the
 * ones we do not have yet, a few at a time, so the whole app works offline
 * (not just the photos that were already looked at). */
self.addEventListener('message', e => {
  const msg = e.data || {};
  if (msg.type !== 'precache-images' || !Array.isArray(msg.urls)) return;
  const reply = (type, extra) => e.source && e.source.postMessage({ type, ...extra });
  e.waitUntil(caches.open(IMG_CACHE).then(async c => {
    const have = new Set((await c.keys()).map(r => r.url));
    const todo = msg.urls.filter(u => !have.has(u));
    let done = 0, failed = 0;
    const worker = async () => {
      while (todo.length) {
        const u = todo.shift();
        try {
          const res = await fetch(u);
          if (res.ok) { await c.put(u, res); done++; } else failed++;
        } catch (err) { failed++; }
      }
    };
    await Promise.all([worker(), worker(), worker(), worker()]);
    reply('precache-done', { added: done, failed, total: msg.urls.length });
  }));
});
