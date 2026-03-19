/**
 * SCRIPT DE TESTE PARA CONSOLE DO NAVEGADOR
 * Cole este script no console para diagnosticar problemas com notificações push
 * 
 * Como usar:
 * 1. Abra o navegador em http://localhost:5000/perfil
 * 2. Pressione F12 para abrir o Console do Desenvolvedor
 * 3. Cole todo este código no console
 * 4. Pressione Enter
 * 5. Veja os resultados
 */

console.log('%c========================================', 'color: cyan; font-weight: bold');
console.log('%c🧪 DIAGNÓSTICO DE PUSH NOTIFICATIONS', 'color: cyan; font-weight: bold; font-size: 16px');
console.log('%c========================================', 'color: cyan; font-weight: bold');
console.log('');

// 1. Verificar contexto seguro
console.log('%c1️⃣ Contexto Seguro:', 'color: yellow; font-weight: bold');
const isSecure = window.isSecureContext;
const protocol = location.protocol;
const hostname = location.hostname;
console.log(`   ${isSecure ? '✅' : '❌'} isSecureContext: ${isSecure}`);
console.log(`   📍 Protocolo: ${protocol}`);
console.log(`   📍 Hostname: ${hostname}`);
if (!isSecure && hostname !== 'localhost' && hostname !== '127.0.0.1') {
    console.error('%c   ⚠️ PROBLEMA: Push API requer HTTPS ou localhost!', 'color: red; font-weight: bold');
    console.log('%c   💡 Solução: Acesse via http://localhost:5000 ou use ngrok', 'color: orange');
}
console.log('');

// 2. Verificar suporte do navegador
console.log('%c2️⃣ Suporte do Navegador:', 'color: yellow; font-weight: bold');
const hasServiceWorker = 'serviceWorker' in navigator;
const hasPushManager = 'PushManager' in window;
const hasNotification = 'Notification' in window;
console.log(`   ${hasServiceWorker ? '✅' : '❌'} Service Worker: ${hasServiceWorker}`);
console.log(`   ${hasPushManager ? '✅' : '❌'} Push Manager (API nativa): ${hasPushManager}`);
console.log(`   ${hasNotification ? '✅' : '❌'} Notifications API: ${hasNotification}`);
if (hasNotification) {
    console.log(`   📍 Notification.permission: ${Notification.permission}`);
}
console.log('');

// 3. Verificar nosso objeto customizado
console.log('%c3️⃣ PushNotificationManager (Nosso Objeto):', 'color: yellow; font-weight: bold');
const hasPushNotificationManager = typeof window.PushNotificationManager !== 'undefined';
console.log(`   ${hasPushNotificationManager ? '✅' : '❌'} window.PushNotificationManager: ${hasPushNotificationManager}`);
if (hasPushNotificationManager) {
    const pnm = window.PushNotificationManager;
    console.log(`   📍 isSubscribed: ${pnm.isSubscribed}`);
    console.log(`   📍 swRegistration: ${pnm.swRegistration ? 'OK' : 'null'}`);
    console.log(`   📍 publicKey: ${pnm.publicKey ? pnm.publicKey.substring(0, 30) + '...' : 'null'}`);
} else {
    console.error('%c   ⚠️ PROBLEMA: PushNotificationManager não foi carregado!', 'color: red; font-weight: bold');
    console.log('%c   💡 Verifique se push-manager.js está sendo carregado', 'color: orange');
}
console.log('');

// 4. Verificar Service Worker
console.log('%c4️⃣ Service Worker Status:', 'color: yellow; font-weight: bold');
if (hasServiceWorker) {
    navigator.serviceWorker.getRegistration().then(reg => {
        if (reg) {
            console.log('   ✅ Service Worker registrado');
            console.log(`   📍 Scope: ${reg.scope}`);
            console.log(`   📍 Active: ${reg.active ? 'Sim' : 'Não'}`);
            console.log(`   📍 Installing: ${reg.installing ? 'Sim' : 'Não'}`);
            console.log(`   📍 Waiting: ${reg.waiting ? 'Sim' : 'Não'}`);
        } else {
            console.warn('   ⚠️ Service Worker não está registrado');
        }
    });
} else {
    console.error('   ❌ Service Worker não suportado');
}
console.log('');

// 5. Verificar elementos do DOM
console.log('%c5️⃣ Elementos do DOM:', 'color: yellow; font-weight: bold');
const toggle = document.getElementById('pushNotificationToggle');
const status = document.getElementById('pushStatus');
const controls = document.getElementById('pushNotificationControls');
const inactive = document.getElementById('pushNotificationInactive');
console.log(`   ${toggle ? '✅' : '❌'} pushNotificationToggle: ${toggle ? 'encontrado' : 'NÃO encontrado'}`);
console.log(`   ${status ? '✅' : '❌'} pushStatus: ${status ? 'encontrado' : 'NÃO encontrado'}`);
console.log(`   ${controls ? '✅' : '❌'} pushNotificationControls: ${controls ? 'encontrado' : 'NÃO encontrado'}`);
console.log(`   ${inactive ? '✅' : '❌'} pushNotificationInactive: ${inactive ? 'encontrado' : 'NÃO encontrado'}`);
console.log('');

// 6. Testar endpoint VAPID
console.log('%c6️⃣ Testando Endpoint VAPID:', 'color: yellow; font-weight: bold');
fetch('/get_vapid_public_key')
    .then(r => {
        console.log(`   ✅ Status: ${r.status}`);
        return r.json();
    })
    .then(data => {
        console.log(`   ✅ Chave pública recebida: ${data.publicKey?.substring(0, 30)}...`);
    })
    .catch(err => {
        console.error('   ❌ Erro ao buscar chave VAPID:', err);
    });
console.log('');

// 7. Resumo e próximos passos
setTimeout(() => {
    console.log('');
    console.log('%c========================================', 'color: cyan; font-weight: bold');
    console.log('%c📋 RESUMO E PRÓXIMOS PASSOS', 'color: cyan; font-weight: bold; font-size: 16px');
    console.log('%c========================================', 'color: cyan; font-weight: bold');
    console.log('');
    
    if (isSecure && hasPushNotificationManager && toggle) {
        console.log('%c✅ TUDO PRONTO! Sistema configurado corretamente.', 'color: green; font-weight: bold');
        console.log('');
        console.log('Próximos passos:');
        console.log('1. Clique no botão "Ativar Notificações" na página');
        console.log('2. Aceite a permissão quando o navegador solicitar');
        console.log('3. Clique em "Enviar Teste" para testar');
        console.log('');
        console.log('Para testar manualmente via console:');
        console.log('%c   window.PushNotificationManager.subscribe()', 'color: lightblue');
    } else {
        console.log('%c⚠️ PROBLEMAS ENCONTRADOS:', 'color: orange; font-weight: bold');
        console.log('');
        
        if (!isSecure && hostname !== 'localhost') {
            console.log('❌ Não está em contexto seguro');
            console.log('   → Acesse via http://localhost:5000 ou use HTTPS');
        }
        
        if (!hasPushNotificationManager) {
            console.log('❌ PushNotificationManager não carregado');
            console.log('   → Verifique se push-manager.js está na página');
            console.log('   → Recarregue a página (Ctrl+Shift+R)');
        }
        
        if (!toggle) {
            console.log('❌ Elementos de UI não encontrados');
            console.log('   → Você está na página /perfil?');
            console.log('   → Recarregue a página');
        }
    }
    
    console.log('');
    console.log('%c========================================', 'color: cyan; font-weight: bold');
}, 500);
