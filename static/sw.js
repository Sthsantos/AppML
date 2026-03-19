const CACHE_NAME = 'ministry-v5.0.8-20260319';
const CACHE_ASSETS = [
    '/',
    '/static/styles.css',
    '/static/manifest.json',
    '/static/js/script.js',
    '/static/icon.png',
    '/static/icon-72x72.png',
    '/static/icon-96x96.png',
    '/static/icon-128x128.png',
    '/static/icon-144x144.png',
    '/static/icon-152x152.png',
    '/static/icon-180x180.png',
    '/static/icon-192x192.png',
    '/static/icon-384x384.png',
    '/static/icon-512x512.png',
    'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css'
];

// Install Service Worker
self.addEventListener('install', event => {
    console.log('[SW] Instalando Service Worker v5.0.0...');
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
    console.log('[SW] Ativando Service Worker v5.0.0...');
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
            console.log('[SW] Service Worker ativado e assumindo controle!');
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
    
    // Network First para HTML e API (não cachear cookies de sessão)
    event.respondWith(
        fetch(event.request, {
            credentials: 'same-origin'  // Garante envio de cookies
        })
            .then(response => {
                // Clone da resposta
                const responseClone = response.clone();
                
                // Cachear resposta HTML apenas se não for login/logout
                if (response.headers.get('content-type')?.includes('text/html') && 
                    !url.pathname.includes('/login') && 
                    !url.pathname.includes('/logout')) {
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

// Background Sync
self.addEventListener('sync', event => {
    console.log('[SW] Background sync:', event.tag);
});

// Push Notifications
self.addEventListener('push', event => {
    console.log('[SW] Push notification recebida:', event);
    
    try {
        let notification = {
            title: 'Ministério de Louvor',
            body: 'Nova notificação',
            icon: '/static/icon-192x192.png',
            badge: '/static/icon-72x72.png',
            vibrate: [200, 100, 200],
            data: {
                url: '/',
                timestamp: Date.now()
            },
            actions: []
        };
        
        // Parse data se disponível
        if (event.data) {
            const data = event.data.json();
            notification = {
                ...notification,
                ...data
            };
        }
        
        event.waitUntil(
            self.registration.showNotification(notification.title, {
                body: notification.body,
                icon: notification.icon,
                badge: notification.badge,
                vibrate: notification.vibrate,
                data: notification.data,
                actions: notification.actions,
                tag: notification.data.type || 'general',
                requireInteraction: notification.data.requireInteraction || false,
                timestamp: notification.data.timestamp || Date.now()
            })
        );
    } catch (error) {
        console.error('[SW] Erro ao processar push:', error);
        // Fallback: mostrar notificação básica
        event.waitUntil(
            self.registration.showNotification('Ministério de Louvor', {
                body: 'Você tem uma nova notificação',
                icon: '/static/icon-192x192.png',
                badge: '/static/icon-72x72.png'
            })
        );
    }
});

// Notification Click Handler
self.addEventListener('notificationclick', event => {
    console.log('[SW] Notification click:', event.notification.tag, event.action);
    
    event.notification.close();
    
    // Determinar URL baseada na action
    let targetUrl = '/';
    
    if (event.notification.data) {
        const data = event.notification.data;
        
        // Se tem URL específica
        if (data.url) {
            targetUrl = data.url;
        }
        
        // Se tem action específica
        if (event.action === 'view') {
            targetUrl = data.url || '/';
        } else if (event.action === 'confirm') {
            targetUrl = '/minhas_escalas';
        } else if (event.action === 'deny') {
            targetUrl = '/minhas_escalas';
        }
        
        // Adicionar parâmetros se necessário
        if (data.escala_id) {
            targetUrl += `?escala_id=${data.escala_id}`;
        }
    }
    
    // Abrir ou focar na janela
    event.waitUntil(
        clients.matchAll({ type: 'window', includeUncontrolled: true })
            .then(clientList => {
                // Tentar focar em janela existente
                for (const client of clientList) {
                    if (client.url.includes(self.registration.scope) && 'focus' in client) {
                        return client.focus().then(() => {
                            // Navigate to target URL
                            return client.navigate(targetUrl);
                        });
                    }
                }
                // Se não encontrou janela, abrir nova
                if (clients.openWindow) {
                    return clients.openWindow(targetUrl);
                }
            })
    );
});