self.addEventListener('install', (event) => {
    console.log('Service Worker instalado');
    self.skipWaiting(); // Força a ativação imediata do Service Worker
});

self.addEventListener('activate', (event) => {
    console.log('Service Worker ativado');
});

self.addEventListener('fetch', (event) => {
    event.respondWith(
        fetch(event.request).catch(() => {
            return new Response('Você está offline. Por favor, conecte-se à internet para acessar esta página.');
        })
    );
});
