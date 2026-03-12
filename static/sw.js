const CACHE_NAME = 'ministry-v1.4.0';
const CACHE_ASSETS = [
    '/',
    '/static/styles.css',
    '/static/manifest.json',
    '/static/js/script.js',
    '/static/icon.svg',
    'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css'
];

// Install Service Worker
self.addEventListener('install', event => {
    console.log('[SW] Instalando Service Worker v1.3.0...');
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => {
                console.log('[SW] Cache aberto, adicionando assets...');
                return cache.addAll(CACHE_ASSETS);
            })
            .then(() => {
                console.log('[SW] Assets cacheados com sucesso!');
                return self.skipWaiting();
            })
            .catch(error => {
                console.error('[SW] Erro ao cachear assets:', error);
            })
    );
});

// Activate Service Worker
self.addEventListener('activate', event => {
    console.log('[SW] Ativando Service Worker v1.3.0...');
    event.waitUntil(
        caches.keys().then(cacheNames => {
            return Promise.all(
                cacheNames.map(cache => {
                    if (cache !== CACHE_NAME) {
                        console.log('[SW] Removendo cache antigo:', cache);
                        return caches.delete(cache);
                    }
                })
            );
        }).then(() => {
            console.log('[SW] Service Worker ativado!');
            return self.clients.claim();
        })
    );
});

// Fetch Strategy: Network First for HTML/API, Cache First for assets
self.addEventListener('fetch', event => {
    if (event.request.method !== 'GET') return;
    
    const url = new URL(event.request.url);
    
    // Cache First para assets estáticos (CSS, JS, imagens, fonts)
    if (url.pathname.match(/\.(css|js|png|jpg|jpeg|gif|svg|woff|woff2|ttf|eot|ico)$/)) {
        event.respondWith(
            caches.match(event.request).then(cachedResponse => {
                if (cachedResponse) {
                    return cachedResponse;
                }
                
                return fetch(event.request).then(response => {
                    // Cachear nova resposta
                    return caches.open(CACHE_NAME).then(cache => {
                        cache.put(event.request, response.clone());
                        return response;
                    });
                });
            }).catch(() => {
                // Fallback para offline
                if (url.pathname.match(/\.(png|jpg|jpeg|gif|svg)$/)) {
                    return caches.match('/static/icon.svg');
                }
            })
        );
        return;
    }
    
    // Network First para HTML e API
    event.respondWith(
        fetch(event.request)
            .then(response => {
                // Clone da resposta
                const responseClone = response.clone();
                
                // Cachear resposta HTML
                if (response.headers.get('content-type')?.includes('text/html')) {
                    caches.open(CACHE_NAME).then(cache => {
                        cache.put(event.request, responseClone);
                    });
                }
                
                return response;
            })
            .catch(() => {
                // Fallback para cache se offline
                return caches.match(event.request).then(cachedResponse => {
                    if (cachedResponse) {
                        return cachedResponse;
                    }
                    
                    // Se for navegação, retornar página offline
                    if (event.request.mode === 'navigate') {
                        return caches.match('/');
                    }
                });
            })
    );
});
                caches.open(CACHE_NAME)
                    .then(cache => {
                        cache.put(event.request, responseClone);
                    });
                
                return response;
            })
            .catch(() => {
                // Network failed, try cache
                return caches.match(event.request)
                    .then(response => {
                        if (response) {
                            return response;
                        }
                        
                        // If no cache, return offline page
                        if (event.request.mode === 'navigate') {
                            return caches.match('/');
                        }
                    });
            })
    );
});

// Background Sync
self.addEventListener('sync', event => {
    console.log('[SW] Background sync:', event.tag);
});

// Push Notifications (preparado para futuro)
self.addEventListener('push', event => {
    console.log('[SW] Push notification recebida');
    const options = {
        body: event.data ? event.data.text() : 'Nova notificação',
        icon: '/static/manifest.json',
        badge: '/static/manifest.json',
        vibrate: [200, 100, 200]
    };
    
    event.waitUntil(
        self.registration.showNotification('Ministério de Louvor', options)
    );
});