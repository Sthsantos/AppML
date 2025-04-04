importScripts('https://www.gstatic.com/firebasejs/11.4.0/firebase-app.js');
importScripts('https://www.gstatic.com/firebasejs/11.4.0/firebase-messaging.js');

const firebaseConfig = {
    apiKey: "AIzaSyCEL3aK4qVP6XTWjJqRs307-9TDxxr0ERs",
    authDomain: "ministerio-de-louvor-62fcf.firebaseapp.com",
    projectId: "ministerio-de-louvor-62fcf",
    storageBucket: "ministerio-de-louvor-62fcf.firebasestorage.app",
    messagingSenderId: "1029007412822",
    appId: "1:1029007412822:web:0001439d6dcc9d632bf5f7",
    measurementId: "G-0ML9TJDJGX"
};

firebase.initializeApp(firebaseConfig);
const messaging = firebase.messaging();

messaging.onBackgroundMessage((payload) => {
    console.log('Mensagem em background recebida:', payload);
    const notificationTitle = payload.notification.title;
    const notificationOptions = {
        body: payload.notification.body,
        icon: '/static/icon.png' // Ajuste o caminho do ícone conforme necessário
    };
    self.registration.showNotification(notificationTitle, notificationOptions);
});