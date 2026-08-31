const CACHE_NAME = 'sync-tracker-v1';
const ASSETS = [
	'/sync',
	'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@500;700&display=swap'
];

self.addEventListener('install', (e) => {
	e.waitUntil(
		caches.open(CACHE_NAME).then((cache) => cache.addAll(ASSETS)).then(() => self.skipWaiting())
	);
});

self.addEventListener('activate', (e) => {
	e.waitUntil(
		caches.keys().then((keys) =>
			Promise.all(keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k)))
		).then(() => self.clients.claim())
	);
});

self.addEventListener('fetch', (e) => {
	if (e.request.method !== 'GET') return;
	// For API requests, use network only
	if (e.request.url.includes('/api/method/')) return;

	e.respondWith(
		fetch(e.request).then((res) => {
			const resClone = res.clone();
			caches.open(CACHE_NAME).then((cache) => cache.put(e.request, resClone));
			return res;
		}).catch(() => caches.match(e.request))
	);
});
