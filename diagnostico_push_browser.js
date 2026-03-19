// ========================================
// DIAGNÓSTICO PUSH - Cole no console (F12)
// ========================================

console.clear();
console.log('%c🔍 DIAGNÓSTICO PUSH NOTIFICATIONS', 'font-size: 18px; font-weight: bold; background: #4f46e5; color: white; padding: 8px;');
console.log('');

// 1. URL atual
console.log('1️⃣ INFORMAÇÕES DA URL:');
console.log('   URL completa:', window.location.href);
console.log('   Protocolo:', window.location.protocol);
console.log('   Hostname:', window.location.hostname);
console.log('   Port:', window.location.port);
console.log('   Contexto seguro:', window.isSecureContext ? '✅ SIM' : '❌ NÃO');

if (!window.isSecureContext) {
    console.log('');
    console.log('%c⚠️ PROBLEMA IDENTIFICADO: Contexto NÃO é seguro!', 'color: red; font-weight: bold; font-size: 14px;');
    console.log('   Push API requer HTTPS ou localhost');
    console.log('   Você está acessando via:', window.location.protocol + '//' + window.location.hostname);
    console.log('');
    console.log('%c💡 SOLUÇÃO:', 'color: orange; font-weight: bold;');
    console.log('   Acesse via: http://localhost:5000/perfil');
    console.log('   OU via: http://127.0.0.1:5000/perfil');
    console.log('   NÃO use o IP (192.168.x.x) sem HTTPS!');
}

// 2. PushNotificationManager
console.log('');
console.log('2️⃣ PUSHNOTIFICATIONMANAGER:');
console.log('   Existe:', window.PushNotificationManager ? '✅ SIM' : '❌ NÃO');

if (window.PushNotificationManager) {
    console.log('   Tipo:', typeof window.PushNotificationManager);
    console.log('   isSubscribed:', window.PushNotificationManager.isSubscribed);
    console.log('   swRegistration:', window.PushNotificationManager.swRegistration);
    console.log('   publicKey:', window.PushNotificationManager.publicKey ? 'Carregada ✅' : 'Não carregada ❌');
    
    // Verificar estado de inicialização
    if (window.PushNotificationManager.swRegistration === null) {
        console.log('');
        console.log('%c⚠️ Service Worker não foi registrado ainda', 'color: orange;');
        console.log('   Possíveis causas:');
        console.log('   1. Contexto não seguro (HTTP sem localhost)');
        console.log('   2. Service Worker não carregou');
        console.log('   3. Erro durante inicialização');
    }
    
    if (window.PushNotificationManager.publicKey === null) {
        console.log('');
        console.log('%c⚠️ Chave VAPID não foi carregada', 'color: orange;');
        console.log('   Possíveis causas:');
        console.log('   1. Servidor não está rodando');
        console.log('   2. Endpoint /get_vapid_public_key não responde');
        console.log('   3. Inicialização não completou');
    }
} else {
    console.log('');
    console.log('%c❌ PushNotificationManager NÃO EXISTE!', 'color: red; font-weight: bold; font-size: 14px;');
    console.log('   Possíveis causas:');
    console.log('   1. Arquivo push-manager.js não foi carregado');
    console.log('   2. Erro de JavaScript impediu a criação');
    console.log('   3. Cache do navegador com versão antiga');
}

// 3. Service Worker
console.log('');
console.log('3️⃣ SERVICE WORKER:');
console.log('   API disponível:', 'serviceWorker' in navigator ? '✅ SIM' : '❌ NÃO');

if ('serviceWorker' in navigator) {
    navigator.serviceWorker.getRegistration().then(reg => {
        if (reg) {
            console.log('   Registrado:', '✅ SIM');
            console.log('   Scope:', reg.scope);
            console.log('   Estado:', reg.active ? reg.active.state : 'sem worker ativo');
        } else {
            console.log('   Registrado:', '❌ NÃO');
            console.log('   %c⚠️ Service Worker não está registrado!', 'color: orange;');
        }
    });
}

// 4. Push API
console.log('');
console.log('4️⃣ PUSH API:');
console.log('   PushManager nativo:', 'PushManager' in window ? '✅ SIM' : '❌ NÃO');
console.log('   Notification API:', 'Notification' in window ? '✅ SIM' : '❌ NÃO');

if ('Notification' in window) {
    console.log('   Permissão:', Notification.permission);
    
    if (Notification.permission === 'denied') {
        console.log('');
        console.log('%c⚠️ Notificações foram BLOQUEADAS pelo usuário!', 'color: red; font-weight: bold;');
        console.log('   Para habilitar:');
        console.log('   1. Clique no ícone de cadeado na barra de endereço');
        console.log('   2. Encontre "Notificações"');
        console.log('   3. Altere para "Permitir"');
        console.log('   4. Recarregue a página');
    }
}

// 5. Scripts carregados
console.log('');
console.log('5️⃣ SCRIPTS CARREGADOS:');
const scripts = Array.from(document.querySelectorAll('script[src]')).map(s => s.src);
const pushManagerScript = scripts.find(src => src.includes('push-manager.js'));

console.log('   Total de scripts:', scripts.length);
console.log('   push-manager.js:', pushManagerScript ? '✅ Carregado' : '❌ NÃO encontrado');

if (pushManagerScript) {
    console.log('   URL:', pushManagerScript);
}

// 6. Elementos DOM
console.log('');
console.log('6️⃣ ELEMENTOS DO DOM:');
const elementos = {
    'Toggle switch': document.getElementById('pushNotificationToggle'),
    'Texto de status': document.getElementById('pushStatus'),
    'Controles ativos': document.getElementById('pushNotificationControls'),
    'Seção inativa': document.getElementById('pushNotificationInactive')
};

Object.entries(elementos).forEach(([nome, elem]) => {
    console.log(`   ${nome}:`, elem ? '✅ Encontrado' : '❌ Não encontrado');
});

// 7. Console de erros
console.log('');
console.log('7️⃣ VERIFICANDO ERROS NO CONSOLE:');
console.log('   Procure por linhas VERMELHAS acima ⬆️');
console.log('   Erros comuns:');
console.log('   - SyntaxError: erro de sintaxe em arquivo JS');
console.log('   - Failed to register: Service Worker falhou');
console.log('   - SecurityError: contexto não seguro');

// 8. Teste manual
console.log('');
console.log('8️⃣ TESTE MANUAL:');
if (window.PushNotificationManager) {
    console.log('   Tente inicializar manualmente:');
    console.log('   %cwindow.PushNotificationManager.init()', 'background: #eee; padding: 4px; font-family: monospace;');
    console.log('');
    console.log('   Cole o comando acima e pressione Enter');
} else {
    console.log('   ❌ Não é possível testar (PushNotificationManager não existe)');
}

// RESUMO FINAL
console.log('');
console.log('═══════════════════════════════════════');
console.log('%c📋 RESUMO DO DIAGNÓSTICO', 'font-size: 16px; font-weight: bold; color: #4f46e5;');
console.log('═══════════════════════════════════════');

const problemas = [];

if (!window.isSecureContext && window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1') {
    problemas.push('⚠️ Acessando via IP sem HTTPS - Use localhost');
}

if (!window.PushNotificationManager) {
    problemas.push('❌ PushNotificationManager não carregou');
}

if (window.PushNotificationManager && window.PushNotificationManager.swRegistration === null) {
    problemas.push('⚠️ Service Worker não registrado');
}

if (window.PushNotificationManager && window.PushNotificationManager.publicKey === null) {
    problemas.push('⚠️ Chave VAPID não carregada');
}

if ('Notification' in window && Notification.permission === 'denied') {
    problemas.push('⚠️ Notificações bloqueadas pelo navegador');
}

if (problemas.length === 0) {
    console.log('%c✅ TUDO OK!', 'color: green; font-weight: bold; font-size: 16px;');
    console.log('Sistema deve estar funcionando normalmente');
    console.log('Se ainda não funciona, tente ativar as notificações novamente');
} else {
    console.log('%cPROBLEMAS ENCONTRADOS:', 'color: red; font-weight: bold;');
    problemas.forEach(p => console.log('  ' + p));
    console.log('');
    console.log('%c💡 PRÓXIMOS PASSOS:', 'color: orange; font-weight: bold;');
    
    if (!window.isSecureContext && window.location.hostname !== 'localhost') {
        console.log('1. MUDE A URL para: http://localhost:5000/perfil');
        console.log('2. Limpe o cache: Ctrl+Shift+R');
        console.log('3. Execute este diagnóstico novamente');
    } else if (!window.PushNotificationManager) {
        console.log('1. Limpe o cache: Ctrl+Shift+Delete (Cache de imagens)');
        console.log('2. Recarregue com força: Ctrl+Shift+R');
        console.log('3. Verifique a aba Network (F12) se push-manager.js retorna 200');
    } else if (window.PushNotificationManager.swRegistration === null) {
        console.log('1. Verifique erros vermelhos no console acima');
        console.log('2. Tente inicializar manualmente: window.PushNotificationManager.init()');
        console.log('3. Verifique se Service Worker está registrado na aba Application');
    }
}

console.log('');
console.log('═══════════════════════════════════════');
