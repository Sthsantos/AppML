self.addEventListener('install', (event) => {
    console.log('Service Worker instalado');
});

self.addEventListener('fetch', (event) => {
    event.respondWith(
        fetch(event.request).catch(() => {
            return new Response('Você está offline. Por favor, conecte-se à internet para acessar esta página.');
        })
    );
});
