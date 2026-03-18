/**
 * Push Notifications Manager
 * Gerencia inscrições e permissões de notificações push
 */

const PushNotificationManager = {
    // Estado
    isSubscribed: false,
    swRegistration: null,
    publicKey: null,

    /**
     * Inicializa o sistema de push notifications
     */
    async init() {
        console.log('[Push] 🚀 Inicializando Push Notifications...');
        console.log('[Push] 📍 URL:', window.location.href);
        console.log('[Push] 🔒 isSecureContext:', window.isSecureContext);
        console.log('[Push] 🌐 Protocol:', window.location.protocol);

        // Verificar se está em contexto seguro (HTTPS ou localhost)
        const isSecureContext = window.isSecureContext;
        const isLocalhost = location.hostname === 'localhost' || location.hostname === '127.0.0.1';
        
        console.log('[Push] ✅ isLocalhost:', isLocalhost);
        
        if (!isSecureContext && !isLocalhost) {
            console.error('[Push] ❌ Push Notifications requerem HTTPS ou localhost!');
            console.error('[Push] Acesso atual:', location.protocol + '//' + location.hostname);
            this.showNotSecureWarning();
            return false;
        }

        // Verificar suporte
        if (!('serviceWorker' in navigator)) {
            console.warn('[Push] ❌ Service Worker não suportado neste navegador');
            this.showUnsupportedWarning('Service Worker');
            return false;
        }

        if (!('PushManager' in window)) {
            console.warn('[Push] ❌ Push API não suportada neste navegador');
            this.showUnsupportedWarning('Push API');
            return false;
        }
        
        console.log('[Push] ✅ Todos os requisitos atendidos, continuando...');

        try {
            // Aguardar Service Worker estar pronto
            console.log('[Push] ⏳ Aguardando Service Worker...');
            this.swRegistration = await navigator.serviceWorker.ready;
            console.log('[Push] ✅ Service Worker pronto');

            // Buscar chave pública VAPID
            console.log('[Push] ⏳ Buscando chave pública VAPID...');
            await this.fetchPublicKey();
            
            if (!this.publicKey) {
                console.error('[Push] ❌ VAPID public key não obtida!');
                return false;
            }
            console.log('[Push] ✅ VAPID key obtida:', this.publicKey.substring(0, 20) + '...');

            // Verificar subscription existente
            console.log('[Push] ⏳ Verificando subscription existente...');
            await this.checkSubscription();
            
            console.log('[Push] 🎉 Inicialização completa!');
            console.log('[Push] 📊 Estado final:', {
                isSubscribed: this.isSubscribed,
                swRegistration: !!this.swRegistration,
                publicKey: !!this.publicKey
            });

            // Atualizar UI
            this.updateUI();

            return true;
        } catch (error) {
            console.error('[Push] ❌ ERRO na inicialização:', error);
            console.error('[Push] Stack trace:', error.stack);
            return false;
        }
    },

    /**
     * Busca a chave pública VAPID do servidor
     */
    async fetchPublicKey() {
        try {
            const response = await fetch('/get_vapid_public_key');
            const data = await response.json();
            
            if (data.publicKey) {
                this.publicKey = data.publicKey;
                console.log('[Push] Chave pública VAPID obtida');
            } else {
                console.error('[Push] Chave pública não disponível');
            }
        } catch (error) {
            console.error('[Push] Erro ao buscar chave pública:', error);
        }
    },

    /**
     * Verifica se já existe uma subscription
     */
    async checkSubscription() {
        try {
            const subscription = await this.swRegistration.pushManager.getSubscription();
            this.isSubscribed = (subscription !== null);
            
            if (this.isSubscribed) {
                console.log('[Push] Já inscrito:', subscription.endpoint);
            } else {
                console.log('[Push] Não inscrito');
            }
            
            return subscription;
        } catch (error) {
            console.error('[Push] Erro ao verificar subscription:', error);
            return null;
        }
    },

    /**
     * Solicita permissão e inscreve usuário
     */
    async subscribe() {
        console.log('[Push] 🔔 subscribe() chamado');
        
        try {
            // Verificar permissão
            console.log('[Push] ⏳ Solicitando permissão...');
            const permission = await Notification.requestPermission();
            console.log('[Push] 📋 Permissão:', permission);
            
            if (permission !== 'granted') {
                console.log('[Push] ❌ Permissão negada pelo usuário');
                this.showToast('Você negou a permissão para notificações', 'warning');
                return false;
            }

            console.log('[Push] ✅ Permissão concedida, inscrevendo...');

            if (!this.publicKey) {
                console.log('[Push] ⚠️ Public key não existe, buscando...');
                await this.fetchPublicKey();
            }

            if (!this.publicKey) {
                console.error('[Push] ❌ Impossível obter public key!');
                this.showToast('Erro ao configurar notificações. Tente novamente.', 'error');
                return false;
            }
            
            console.log('[Push] ✅ Public key disponível:', this.publicKey.substring(0, 20) + '...');

            // Converter chave VAPID para Uint8Array
            console.log('[Push] ⏳ Convertendo VAPID key...');
            const applicationServerKey = this.urlBase64ToUint8Array(this.publicKey);
            console.log('[Push] ✅ VAPID key convertida');

            // Criar subscription
            console.log('[Push] ⏳ Criando subscription no browser...');
            const subscription = await this.swRegistration.pushManager.subscribe({
                userVisibleOnly: true,
                applicationServerKey: applicationServerKey
            });

            console.log('[Push] ✅ Subscription criada:', subscription.endpoint.substring(0, 50) + '...');

            // Enviar subscription para o servidor
            console.log('[Push] ⏳ Salvando subscription no servidor...');
            const saved = await this.saveSubscriptionToServer(subscription);

            if (saved) {
                this.isSubscribed = true;
                this.updateUI();
                this.showToast('✅ Notificações ativadas com sucesso!', 'success');
                return true;
            } else {
                this.showToast('Erro ao salvar inscrição no servidor', 'error');
                return false;
            }

        } catch (error) {
            console.error('[Push] Erro ao inscrever:', error);
            this.showToast('Erro ao ativar notificações', 'error');
            return false;
        }
    },

    /**
     * Remove inscrição de push
     */
    async unsubscribe() {
        try {
            const subscription = await this.swRegistration.pushManager.getSubscription();
            
            if (!subscription) {
                console.log('[Push] Nenhuma subscription encontrada');
                return true;
            }

            // Desinscrever no navegador
            const success = await subscription.unsubscribe();

            if (success) {
                console.log('[Push] Desinscrito do navegador');
                
                // Remover do servidor
                await this.removeSubscriptionFromServer(subscription.endpoint);
                
                this.isSubscribed = false;
                this.updateUI();
                this.showToast('Notificações desativadas', 'info');
                return true;
            }

            return false;
        } catch (error) {
            console.error('[Push] Erro ao desinscrever:', error);
            this.showToast('Erro ao desativar notificações', 'error');
            return false;
        }
    },

    /**
     * Salva subscription no servidor
     */
    async saveSubscriptionToServer(subscription) {
        try {
            const response = await fetch('/push_subscribe', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    subscription: subscription.toJSON()
                })
            });

            const data = await response.json();
            return data.success;
        } catch (error) {
            console.error('[Push] Erro ao salvar no servidor:', error);
            return false;
        }
    },

    /**
     * Remove subscription do servidor
     */
    async removeSubscriptionFromServer(endpoint) {
        try {
            const response = await fetch('/push_unsubscribe', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ endpoint })
            });

            const data = await response.json();
            return data.success;
        } catch (error) {
            console.error('[Push] Erro ao remover do servidor:', error);
            return false;
        }
    },

    /**
     * Envia notificação de teste
     */
    async sendTest() {
        try {
            const response = await fetch('/push_test', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            const data = await response.json();
            
            if (data.success) {
                this.showToast(data.message, 'success');
                return true;
            } else {
                this.showToast(data.message, 'error');
                return false;
            }
        } catch (error) {
            console.error('[Push] Erro ao enviar teste:', error);
            this.showToast('Erro ao enviar notificação de teste', 'error');
            return false;
        }
    },

    /**
     * Atualiza UI baseada no estado da subscription
     */
    updateUI() {
        // Botão de toggle
        const toggleBtn = document.getElementById('pushNotificationToggle');
        if (toggleBtn) {
            toggleBtn.checked = this.isSubscribed;
        }

        // Botão de ativar/desativar
        const btn = document.getElementById('pushNotificationBtn');
        if (btn) {
            if (this.isSubscribed) {
                btn.textContent = '🔕 Desativar Notificações';
                btn.classList.remove('btn-primary');
                btn.classList.add('btn-secondary');
            } else {
                btn.textContent = '🔔 Ativar Notificações';
                btn.classList.remove('btn-secondary');
                btn.classList.add('btn-primary');
            }
        }

        // Status text
        const statusText = document.getElementById('pushStatus');
        if (statusText) {
            if (this.isSubscribed) {
                statusText.textContent = '✅ Ativadas';
                statusText.style.color = '#10b981';
            } else {
                statusText.textContent = '🔕 Desativadas';
                statusText.style.color = '#9ca3af';
            }
        }

        // Botão de teste (só aparece se inscrito)
        const testBtn = document.getElementById('pushTestBtn');
        if (testBtn) {
            testBtn.style.display = this.isSubscribed ? 'inline-block' : 'none';
        }
    },

    /**
     * Converte chave VAPID base64 para Uint8Array
     */
    urlBase64ToUint8Array(base64String) {
        const padding = '='.repeat((4 - base64String.length % 4) % 4);
        const base64 = (base64String + padding)
            .replace(/\-/g, '+')
            .replace(/_/g, '/');

        const rawData = window.atob(base64);
        const outputArray = new Uint8Array(rawData.length);

        for (let i = 0; i < rawData.length; ++i) {
            outputArray[i] = rawData.charCodeAt(i);
        }
        return outputArray;
    },

    /**
     * Mostra toast notification (usa sistema existente se disponível)
     */
    /**
     * Exibe aviso de ambiente não seguro
     */
    showNotSecureWarning() {
        const card = document.querySelector('.card-body');
        if (!card) return;

        const warning = document.createElement('div');
        warning.className = 'alert alert-warning';
        warning.style.cssText = `
            background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%);
            color: #78350f;
            padding: 1.5rem;
            border-radius: 0.75rem;
            margin-bottom: 1rem;
            border-left: 4px solid #d97706;
        `;
        warning.innerHTML = `
            <div style="display: flex; align-items: start; gap: 1rem;">
                <i class="fas fa-exclamation-triangle" style="font-size: 2rem; color: #d97706;"></i>
                <div>
                    <h4 style="margin: 0 0 0.5rem; color: #78350f; font-weight: bold;">⚠️ HTTPS Obrigatório para Notificações Push</h4>
                    <p style="margin: 0 0 0.5rem; color: #92400e;">
                        Push Notifications só funcionam em <strong>HTTPS</strong> ou <strong>localhost</strong>.<br>
                        Você está acessando via: <code>${location.protocol}//${location.hostname}</code>
                    </p>
                    <details style="margin-top: 1rem;">
                        <summary style="cursor: pointer; font-weight: 600; color: #78350f;">
                            🔧 Como corrigir (clique para expandir)
                        </summary>
                        <div style="margin-top: 0.75rem; padding-left: 1rem; color: #92400e;">
                            <p><strong>Opção 1 - Teste no Desktop (Mais Rápido):</strong></p>
                            <p>Acesse <code>http://localhost:5000/perfil</code> no computador onde o servidor está rodando.</p>
                            
                            <p style="margin-top: 1rem;"><strong>Opção 2 - Usar ngrok (Para Celular):</strong></p>
                            <ol style="margin-left: 1rem;">
                                <li>Baixe ngrok: <a href="https://ngrok.com/download" target="_blank" style="color: #b45309;">ngrok.com/download</a></li>
                                <li>Execute: <code>ngrok http 5000</code></li>
                                <li>Use a URL HTTPS fornecida (ex: https://abc123.ngrok.io)</li>
                            </ol>
                            
                            <p style="margin-top: 1rem;"><strong>Opção 3 - Deploy em Produção:</strong></p>
                            <p>Faça deploy no Render/Heroku para ter HTTPS automático.</p>
                        </div>
                    </details>
                </div>
            </div>
        `;

        // Inserir no início do card-body
        card.insertBefore(warning, card.firstChild);
    },

    /**
     * Exibe aviso de funcionalidade não suportada
     */
    showUnsupportedWarning(feature) {
        const card = document.querySelector('.card-body');
        if (!card) return;

        const warning = document.createElement('div');
        warning.className = 'alert alert-danger';
        warning.style.cssText = `
            background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
            color: white;
            padding: 1.5rem;
            border-radius: 0.75rem;
            margin-bottom: 1rem;
            border-left: 4px solid #b91c1c;
        `;
        warning.innerHTML = `
            <div style="display: flex; align-items: center; gap: 1rem;">
                <i class="fas fa-times-circle" style="font-size: 2rem;"></i>
                <div>
                    <h4 style="margin: 0 0 0.5rem; font-weight: bold;">❌ Navegador Incompatível</h4>
                    <p style="margin: 0; opacity: 0.9;">
                        ${feature} não é suportado neste navegador.<br>
                        Tente usar Chrome, Firefox, Edge ou Safari atualizado.
                    </p>
                </div>
            </div>
        `;

        card.insertBefore(warning, card.firstChild);
    },

    /**
     * Mostra notificação toast
     */
    showToast(message, type = 'info') {
        // Tentar usar sistema de toast existente
        if (window.App && window.App.toast && window.App.toast[type]) {
            window.App.toast[type](message);
            return;
        }

        // Fallback: criar toast simples
        const toast = document.createElement('div');
        toast.className = 'toast-notification';
        toast.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: ${type === 'success' ? '#10b981' : type === 'error' ? '#ef4444' : type === 'warning' ? '#f59e0b' : '#3b82f6'};
            color: white;
            padding: 1rem 1.5rem;
            border-radius: 0.75rem;
            box-shadow: 0 10px 15px -3px rgba(0,0,0,0.3);
            z-index: 10000;
            animation: slideInRight 0.3s ease-out;
        `;
        toast.textContent = message;
        document.body.appendChild(toast);

        setTimeout(() => {
            toast.style.animation = 'slideOutRight 0.3s ease-in';
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }
};

// Auto-inicializar quando DOM estiver pronto
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        if ('serviceWorker' in navigator) {
            PushNotificationManager.init();
        }
    });
} else {
    if ('serviceWorker' in navigator) {
        PushNotificationManager.init();
    }
}

// Exportar para uso global
window.PushNotificationManager = PushNotificationManager;
