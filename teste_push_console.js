// ==========================================
// DIAGNÓSTICO RÁPIDO - Cole no Console (F12)
// ==========================================

console.log('%c🔍 DIAGNÓSTICO PUSH NOTIFICATIONS', 'font-size: 16px; font-weight: bold; color: #4f46e5;');
console.log('==========================================\n');

// 1. Verificar se o arquivo push-manager.js foi carregado
console.log('1️⃣ VERIFICANDO ARQUIVO JAVASCRIPT:');
const scripts = Array.from(document.querySelectorAll('script')).map(s => s.src);
const pushManagerLoaded = scripts.some(src => src.includes('push-manager.js'));
console.log('   push-manager.js carregado:', pushManagerLoaded ? '✅ SIM' : '❌ NÃO');
if (pushManagerLoaded) {
    const scriptUrl = scripts.find(src => src.includes('push-manager.js'));
    console.log('   URL:', scriptUrl);
}

// 2. Verificar se window.PushNotificationManager existe
console.log('\n2️⃣ VERIFICANDO OBJETO GLOBAL:');
console.log('   window.PushNotificationManager existe:', window.PushNotificationManager ? '✅ SIM' : '❌ NÃO');
if (window.PushNotificationManager) {
    console.log('   Tipo:', typeof window.PushNotificationManager);
    console.log('   Propriedades:', Object.keys(window.PushNotificationManager));
    console.log('   isSubscribed:', window.PushNotificationManager.isSubscribed);
    console.log('   swRegistration:', window.PushNotificationManager.swRegistration);
    console.log('   publicKey:', window.PushNotificationManager.publicKey);
}

// 3. Verificar Service Worker
console.log('\n3️⃣ VERIFICANDO SERVICE WORKER:');
console.log('   navigator.serviceWorker disponível:', 'serviceWorker' in navigator ? '✅ SIM' : '❌ NÃO');
if ('serviceWorker' in navigator) {
    navigator.serviceWorker.getRegistration().then(reg => {
        console.log('   Service Worker registrado:', reg ? '✅ SIM' : '❌ NÃO');
        if (reg) {
            console.log('   Scope:', reg.scope);
            console.log('   Estado:', reg.active ? reg.active.state : 'sem worker ativo');
        }
    });
}

// 4. Verificar contexto seguro
console.log('\n4️⃣ VERIFICANDO SEGURANÇA:');
console.log('   window.isSecureContext:', window.isSecureContext ? '✅ SIM' : '❌ NÃO');
console.log('   URL atual:', location.href);
console.log('   Protocolo:', location.protocol);
console.log('   hostname:', location.hostname);

// 5. Verificar elementos do DOM
console.log('\n5️⃣ VERIFICANDO ELEMENTOS DO DOM:');
const toggle = document.getElementById('pushNotificationToggle');
const status = document.getElementById('pushStatus');
const controls = document.getElementById('pushNotificationControls');
const inactive = document.getElementById('pushNotificationInactive');

console.log('   Toggle switch:', toggle ? '✅ Encontrado' : '❌ Não encontrado');
console.log('   Status text:', status ? '✅ Encontrado' : '❌ Não encontrado');
console.log('   Controls div:', controls ? '✅ Encontrado' : '❌ Não encontrado');
console.log('   Inactive div:', inactive ? '✅ Encontrado' : '❌ Não encontrado');

// 6. Verificar erros no console
console.log('\n6️⃣ TENTANDO INICIALIZAR MANUALMENTE:');
if (window.PushNotificationManager) {
    console.log('   Chamando PushNotificationManager.init()...');
    window.PushNotificationManager.init()
        .then(result => {
            console.log('   ✅ Init completado com sucesso!', result);
            console.log('   Estado final:', {
                isSubscribed: window.PushNotificationManager.isSubscribed,
                hasRegistration: !!window.PushNotificationManager.swRegistration,
                hasPublicKey: !!window.PushNotificationManager.publicKey
            });
        })
        .catch(error => {
            console.error('   ❌ Erro durante init:', error);
        });
} else {
    console.error('   ❌ PushNotificationManager não está disponível!');
    console.log('\n📋 PRÓXIMOS PASSOS:');
    console.log('   1. Limpe o cache: Ctrl+Shift+Delete (selecione apenas "Cache")');
    console.log('   2. Recarregue com força: Ctrl+Shift+R');
    console.log('   3. Execute este diagnóstico novamente');
    console.log('   4. Verifique no Network tab (F12) se push-manager.js carregou (200 OK)');
}

console.log('\n==========================================');
console.log('%c✅ DIAGNÓSTICO COMPLETO', 'font-size: 14px; font-weight: bold; color: #10b981;');
