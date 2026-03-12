// ========================================
// MINISTÉRIO DE LOUVOR - SCRIPT MODERNO
// ========================================

// ========================================
// UTILITÁRIOS E HELPERS
// ========================================
const App = {
    // Configurações globais
    config: {
        toastDuration: 4000,
        animationDuration: 300,
        apiTimeout: 10000
    },

    // Sistema de Tema Dark/Light
    theme: {
        current: 'light',

        init() {
            // Carregar tema salvo ou detectar preferência do sistema
            const savedTheme = localStorage.getItem('theme');
            const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
            
            this.current = savedTheme || (prefersDark ? 'dark' : 'light');
            this.apply(this.current);
            
            // Atualizar ícone
            this.updateIcon();
        },

        apply(theme) {
            document.documentElement.setAttribute('data-theme', theme);
            this.current = theme;
            localStorage.setItem('theme', theme);
        },

        toggle() {
            const newTheme = this.current === 'light' ? 'dark' : 'light';
            this.apply(newTheme);
            this.updateIcon();
            
            // Feedback visual
            App.toast.success(`Tema ${newTheme === 'dark' ? 'escuro' : 'claro'} ativado!`);
        },

        updateIcon() {
            const icons = document.querySelectorAll('.theme-toggle i, .theme-toggle-login i');
            icons.forEach(icon => {
                if (icon) {
                    icon.className = this.current === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
                }
            });
        }
    },

    // Sistema de Toast Notifications
    toast: {
        container: null,

        init() {
            if (!this.container) {
                this.container = document.createElement('div');
                this.container.className = 'toast-container';
                document.body.appendChild(this.container);
            }
        },

        show(message, type = 'info') {
            this.init();
            
            const toast = document.createElement('div');
            toast.className = `toast toast-${type}`;
            
            const icons = {
                success: 'fa-check-circle',
                error: 'fa-exclamation-circle',
                warning: 'fa-exclamation-triangle',
                info: 'fa-info-circle'
            };
            
            toast.innerHTML = `
                <i class="fas ${icons[type]}"></i>
                <span class="toast-message">${message}</span>
                <button class="toast-close" onclick="this.parentElement.remove()">
                    <i class="fas fa-times"></i>
                </button>
            `;
            
            this.container.appendChild(toast);
            
            // Animação de entrada
            setTimeout(() => toast.classList.add('show'), 10);
            
            // Auto remoção
            setTimeout(() => {
                toast.classList.remove('show');
                setTimeout(() => toast.remove(), App.config.animationDuration);
            }, App.config.toastDuration);
        },

        success(message) { this.show(message, 'success'); },
        error(message) { this.show(message, 'error'); },
        warning(message) { this.show(message, 'warning'); },
        info(message) { this.show(message, 'info'); }
    },

    // Sistema de Loading
    loading: {
        overlay: null,

        show(message = 'Carregando...') {
            if (!this.overlay) {
                this.overlay = document.createElement('div');
                this.overlay.className = 'loading-overlay';
                this.overlay.innerHTML = `
                    <div class="loading-content">
                        <div class="loading-spinner"></div>
                        <p class="loading-message">${message}</p>
                    </div>
                `;
                document.body.appendChild(this.overlay);
            }
            this.overlay.style.display = 'flex';
        },

        hide() {
            if (this.overlay) {
                this.overlay.style.display = 'none';
            }
        }
    },

    // Gerenciador de Modals
    modal: {
        open(modalId) {
            const modal = document.getElementById(modalId);
            if (modal) {
                modal.classList.add('active');
                modal.style.display = 'flex';
                document.body.style.overflow = 'hidden';
            }
        },

        close(modalId) {
            const modal = document.getElementById(modalId);
            if (modal) {
                modal.classList.remove('active');
                setTimeout(() => {
                    modal.style.display = 'none';
                    document.body.style.overflow = '';
                }, App.config.animationDuration);
            }
        },

        closeAll() {
            document.querySelectorAll('.modal.active').forEach(modal => {
                this.close(modal.id);
            });
        }
    },

    // Gerenciador de Sidebar
    sidebar: {
        element: null,
        overlay: null,

        init() {
            this.element = document.querySelector('.sidebar');
            
            // Criar overlay
            if (!this.overlay) {
                this.overlay = document.createElement('div');
                this.overlay.className = 'sidebar-overlay';
                this.overlay.addEventListener('click', () => this.close());
                document.body.appendChild(this.overlay);
            }
        },

        toggle() {
            this.init();
            if (this.element.classList.contains('open')) {
                this.close();
            } else {
                this.open();
            }
        },

        open() {
            this.init();
            this.element.classList.add('open');
            this.overlay.classList.add('active');
        },

        close() {
            if (this.element) {
                this.element.classList.remove('open');
            }
            if (this.overlay) {
                this.overlay.classList.remove('active');
            }
        }
    },

    // Requisições API
    api: {
        async request(url, options = {}) {
            const defaultOptions = {
                headers: {
                    'Content-Type': 'application/json',
                },
                ...options
            };

            try {
                const response = await fetch(url, defaultOptions);
                
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                
                const data = await response.json();
                return { success: true, data };
            } catch (error) {
                console.error('API Error:', error);
                return { success: false, error: error.message };
            }
        },

        async get(url) {
            return this.request(url, { method: 'GET' });
        },

        async post(url, data) {
            return this.request(url, {
                method: 'POST',
                body: JSON.stringify(data)
            });
        },

        async put(url, data) {
            return this.request(url, {
                method: 'PUT',
                body: JSON.stringify(data)
            });
        },

        async delete(url) {
            return this.request(url, { method: 'DELETE' });
        }
    },

    // Validação de formulários
    validate: {
        email(email) {
            const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            return re.test(email);
        },

        phone(phone) {
            const re = /^[\d\s\-\(\)+]+$/;
            return phone.length >= 10 && re.test(phone);
        },

        required(value) {
            return value && value.trim().length > 0;
        },

        url(url) {
            try {
                new URL(url);
                return true;
            } catch {
                return false;
            }
        }
    },

    // Formatadores
    format: {
        date(dateString) {
            const date = new Date(dateString);
            return date.toLocaleDateString('pt-BR');
        },

        time(timeString) {
            return timeString.substring(0, 5);
        },

        phone(phone) {
            return phone.replace(/\D/g, '');
        },

        datetime(dateTimeString) {
            const date = new Date(dateTimeString);
            return date.toLocaleString('pt-BR', {
                day: '2-digit',
                month: '2-digit',
                year: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            });
        },

        relativeDate(dateTimeString) {
            const date = new Date(dateTimeString);
            const now = new Date();
            const diffMs = now - date;
            const diffMins = Math.floor(diffMs / 60000);
            const diffHours = Math.floor(diffMs / 3600000);
            const diffDays = Math.floor(diffMs / 86400000);

            if (diffMins < 1) return 'Agora';
            if (diffMins < 60) return `${diffMins} min atrás`;
            if (diffHours < 24) return `${diffHours}h atrás`;
            if (diffDays === 1) return 'Ontem';
            if (diffDays < 7) return `${diffDays} dias atrás`;
            return date.toLocaleDateString('pt-BR');
        },

        monthShort(dateString) {
            const months = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez'];
            const date = new Date(dateString);
            return months[date.getMonth()];
        }
    }
};

// ========================================
// FUNÇÕES PRINCIPAIS
// ========================================

// Toggle Sidebar
window.toggleSidebar = function() {
    App.sidebar.toggle();
};

// Carregar dados do usuário
async function loadUserData() {
    const result = await App.api.get('/get_user_data');
    
    if (result.success && result.data.logged_in) {
        const user = result.data;
        
        // Atualiza elementos se existirem
        const updates = {
            'memberName': user.name,
            'memberEmail': user.email,
            'memberInstrument': user.instrument || 'N/A',
            'memberPhone': user.phone || 'N/A'
        };
        
        Object.entries(updates).forEach(([id, value]) => {
            const element = document.getElementById(id);
            if (element) element.textContent = value;
        });
    } else {
        App.toast.error('Erro ao carregar dados do usuário');
    }
}

// Carregar avisos
async function loadAnnouncements() {
    const announcementsList = document.getElementById('announcements');
    if (!announcementsList) return;

    const result = await App.api.get('/get_announcements');
    
    if (result.success) {
        const announcements = result.data;
        
        if (announcements.length === 0) {
            announcementsList.innerHTML = '<p class="no-announcements">Nenhum aviso disponível.</p>';
        } else {
            announcementsList.innerHTML = '';
            announcements.forEach((announcement, index) => {
                const div = document.createElement('div');
                div.className = 'announcement-item animate-slide-left';
                div.style.animationDelay = `${index * 0.1}s`;
                
                const priorityIcons = {
                    urgent: '🔴',
                    high: '🟠',
                    normal: '🟢',
                    low: '🔵'
                };
                
                div.innerHTML = `
                    <div class="announcement-header">
                        <strong>${priorityIcons[announcement.priority] || ''} ${announcement.title || 'Aviso'}</strong>
                        <span class="announcement-date">${announcement.created_at || ''}</span>
                    </div>
                    <p>${announcement.text || announcement.message}</p>
                `;
                announcementsList.appendChild(div);
            });
        }
    } else {
        announcementsList.innerHTML = '<p class="text-center">Erro ao carregar avisos.</p>';
    }
}

// Carregar escalas do usuário
async function loadScales() {
    const scalesList = document.getElementById('scales');
    const scalePanel = document.getElementById('scalePanel');
    
    if (!scalesList) return;

    const result = await App.api.get('/get_user_scales');
    
    if (result.success) {
        const scales = result.data;
        
        if (scales.length > 0 && scalePanel) {
            scalePanel.style.display = 'block';
        }
        
        scalesList.innerHTML = '';
        scales.forEach((item, index) => {
            const li = document.createElement('li');
            li.className = 'escala-item animate-scale';
            li.style.animationDelay = `${index * 0.1}s`;
            li.innerHTML = `
                <strong>${App.format.date(item.culto.date)}</strong> às ${item.culto.time}
                <br>
                <span class="role">${item.role} - ${item.culto.description}</span>
            `;
            scalesList.appendChild(li);
        });
    }
}

// Carregar calendário de cultos
async function loadCultCalendar() {
    const cultCalendar = document.getElementById('cultCalendar');
    if (!cultCalendar) return;

    const result = await App.api.get('/get_cult_calendar');
    
    if (result.success) {
        const cultos = result.data;
        
        cultCalendar.innerHTML = '';
        cultos.forEach((culto, index) => {
            const li = document.createElement('li');
            li.className = 'culto-item animate-slide-right';
            li.style.animationDelay = `${index * 0.1}s`;
            li.innerHTML = `
                <strong>${App.format.date(culto.date)}</strong> às ${culto.time}
                <br>
                <span>${culto.description}</span>
            `;
            cultCalendar.appendChild(li);
        });
    }
}

// Carregar membros agrupados por instrumento
async function loadMembers() {
    const instrumentsContainer = document.getElementById('instrumentsContainer');
    if (!instrumentsContainer) return;

    App.loading.show('Carregando membros...');
    
    const result = await App.api.get('/get_membros');
    
    App.loading.hide();
    
    if (result.success) {
        const members = result.data;
        
        // Agrupar por instrumento
        const grouped = members.reduce((acc, member) => {
            const instrument = member.instrument || 'Outros';
            if (!acc[instrument]) acc[instrument] = [];
            acc[instrument].push(member);
            return acc;
        }, {});

        instrumentsContainer.innerHTML = '';
        
        Object.entries(grouped).forEach(([instrument, membersList], groupIndex) => {
            const section = document.createElement('div');
            section.className = 'member-group animate-scale';
            section.style.animationDelay = `${groupIndex * 0.1}s`;

            const title = document.createElement('h3');
            title.className = 'member-group-title';
            title.innerHTML = `<i class="fas fa-music"></i> ${instrument}`;
            section.appendChild(title);

            const list = document.createElement('ul');
            list.className = 'member-list';

            membersList.forEach(member => {
                const li = document.createElement('li');
                li.className = 'member-item';
                
                const whatsappLink = member.phone ? 
                    `<a href="https://wa.me/${App.format.phone(member.phone)}" target="_blank" title="WhatsApp">
                        <i class="fab fa-whatsapp" style="color: #25d366;"></i>
                    </a>` : '';
                
                const emailLink = `<a href="mailto:${member.email}" title="Email">
                    <i class="fas fa-envelope" style="color: var(--primary-color);"></i>
                </a>`;
                
                li.innerHTML = `
                    <div class="member-info">
                        <strong><i class="fas fa-user"></i> ${member.name}</strong>
                        ${member.suspended ? '<span class="badge badge-danger">Suspenso</span>' : ''}
                        <br>
                        <span><i class="fas fa-envelope"></i> ${member.email} ${emailLink}</span>
                        <br>
                        ${member.phone ? `<span><i class="fas fa-phone"></i> ${member.phone} ${whatsappLink}</span>` : ''}
                    </div>
                `;
                list.appendChild(li);
            });

            section.appendChild(list);
            instrumentsContainer.appendChild(section);
        });
    } else {
        instrumentsContainer.innerHTML = '<p class="text-center">Erro ao carregar membros.</p>';
    }
}

// Carregar cultos
async function loadCultos() {
    const cultosList = document.getElementById('cultosList');
    if (!cultosList) return;

    const result = await App.api.get('/get_cultos');
    
    if (result.success) {
        const cultos = result.data;
        
        cultosList.innerHTML = '';
        cultos.forEach((culto, index) => {
            const div = document.createElement('div');
            div.className = 'culto-item animate-slide-left';
            div.style.animationDelay = `${index * 0.05}s`;
            div.innerHTML = `
                <div class="d-flex justify-between align-center">
                    <div>
                        <strong><i class="fas fa-church"></i> ${culto.description}</strong>
                        <br>
                        <span><i class="fas fa-calendar"></i> ${App.format.date(culto.date)} às ${culto.time}</span>
                    </div>
                </div>
            `;
            cultosList.appendChild(div);
        });
    }
}

// Enviar feedback
window.submitFeedback = async function(event) {
    if (event) event.preventDefault();
    
    const feedback = document.getElementById('feedbackText')?.value;
    const type = document.getElementById('feedbackType')?.value || 'feedback';
    
    if (!App.validate.required(feedback)) {
        App.toast.warning('Por favor, escreva sua mensagem.');
        return;
    }
    
    App.loading.show('Enviando feedback...');
    
    const result = await App.api.post('/submit_feedback', { feedback, type });
    
    App.loading.hide();
    
    if (result.success && result.data.success) {
        App.toast.success('Feedback enviado com sucesso!');
        document.getElementById('feedbackText').value = '';
    } else {
        App.toast.error('Erro ao enviar feedback. Tente novamente.');
    }
};

// Carregar repertório
async function loadRepertorio() {
    const repertorioList = document.getElementById('repertorioList');
    if (!repertorioList) return;

    App.loading.show('Carregando repertório...');
    
    const result = await App.api.get('/get_repertorio');
    
    App.loading.hide();
    
    if (result.success) {
        const musicas = result.data;
        
        repertorioList.innerHTML = '';
        musicas.forEach((musica, index) => {
            const div = document.createElement('div');
            div.className = 'member-item animate-scale';
            div.style.animationDelay = `${index * 0.05}s`;
            div.innerHTML = `
                <div class="member-info">
                    <strong><i class="fas fa-music"></i> ${musica.title}</strong>
                    ${musica.artist ? `<br><span><i class="fas fa-user"></i> ${musica.artist}</span>` : ''}
                    ${musica.key_tone ? `<br><span><i class="fas fa-key"></i> Tom: ${musica.key_tone}</span>` : ''}
                    ${musica.category ? `<br><span class="badge badge-primary">${musica.category}</span>` : ''}
                    <br>
                    <div style="margin-top: 0.5rem;">
                        ${musica.link_video ? `<a href="${musica.link_video}" target="_blank" class="btn btn-sm btn-outline"><i class="fab fa-youtube"></i> Vídeo</a>` : ''}
                        ${musica.link_audio ? `<a href="${musica.link_audio}" target="_blank" class="btn btn-sm btn-outline"><i class="fas fa-headphones"></i> Áudio</a>` : ''}
                    </div>
                </div>
            `;
            repertorioList.appendChild(div);
        });
    }
}

// Carregar dashboard stats (admin)
async function loadDashboardStats() {
    const statsContainer = document.getElementById('dashboardStats');
    if (!statsContainer) return;

    App.loading.show('Carregando estatísticas...');
    
    const result = await App.api.get('/get_dashboard_stats');
    
    App.loading.hide();
    
    if (result.success) {
        const stats = result.data;
        
        statsContainer.innerHTML = `
            <div class="features">
                <div class="feature-card">
                    <i class="fas fa-users feature-icon"></i>
                    <h3>${stats.total_membros}</h3>
                    <p>Total de Membros</p>
                </div>
                <div class="feature-card">
                    <i class="fas fa-user-check feature-icon"></i>
                    <h3>${stats.membros_ativos}</h3>
                    <p>Membros Ativos</p>
                </div>
                <div class="feature-card">
                    <i class="fas fa-church feature-icon"></i>
                    <h3>${stats.total_cultos}</h3>
                    <p>Cultos Cadastrados</p>
                </div>
                <div class="feature-card">
                    <i class="fas fa-music feature-icon"></i>
                    <h3>${stats.total_musicas}</h3>
                    <p>Músicas no Repertório</p>
                </div>
                <div class="feature-card">
                    <i class="fas fa-calendar-check feature-icon"></i>
                    <h3>${stats.total_escalas}</h3>
                    <p>Escalas Ativas</p>
                </div>
                <div class="feature-card">
                    <i class="fas fa-comments feature-icon"></i>
                    <h3>${stats.feedbacks_pendentes}</h3>
                    <p>Feedbacks Pendentes</p>
                </div>
            </div>
        `;
    },

    // PWA - Progressive Web App
    pwa: {
        deferredPrompt: null,
        banner: null,

        init() {
            // Registrar Service Worker
            if ('serviceWorker' in navigator) {
                navigator.serviceWorker.register('/sw.js')
                    .then(registration => {
                        console.log('✅ Service Worker registrado:', registration.scope);
                    })
                    .catch(error => {
                        console.error('❌ Erro ao registrar Service Worker:', error);
                    });
            }

            // Capturar evento de instalação
            window.addEventListener('beforeinstallprompt', (e) => {
                e.preventDefault();
                this.deferredPrompt = e;
                this.showBanner();
            });

            // Verificar se já está instalado
            window.addEventListener('appinstalled', () => {
                console.log('✅ PWA instalado!');
                this.hideBanner();
                App.toast.success('App instalado com sucesso! 🎉');
            });

            // Detectar se está rodando como PWA
            if (window.matchMedia('(display-mode: standalone)').matches || 
                window.navigator.standalone === true) {
                console.log('✅ App rodando como PWA');
                this.hideBanner();
            }
        },

        showBanner() {
            // Mostrar banner apenas se não foi dispensado recentemente
            const dismissed = localStorage.getItem('pwa-banner-dismissed');
            const dismissedTime = dismissed ? parseInt(dismissed) : 0;
            const daysSinceDismissed = (Date.now() - dismissedTime) / (1000 * 60 * 60 * 24);

            if (daysSinceDismissed > 7 || !dismissed) {
                this.banner = document.getElementById('pwaInstallBanner');
                if (this.banner) {
                    setTimeout(() => {
                        this.banner.style.display = 'block';
                        setTimeout(() => this.banner.classList.add('show'), 100);
                    }, 2000); // Mostrar após 2 segundos
                }

                // Também mostrar botão no menu
                const menuBtn = document.getElementById('pwaInstallButton');
                if (menuBtn) {
                    menuBtn.style.display = 'block';
                }
            }
        },

        hideBanner() {
            if (this.banner) {
                this.banner.classList.remove('show');
                setTimeout(() => {
                    this.banner.style.display = 'none';
                }, 300);
            }

            const menuBtn = document.getElementById('pwaInstallButton');
            if (menuBtn) {
                menuBtn.style.display = 'none';
            }
        },

        dismissBanner() {
            localStorage.setItem('pwa-banner-dismissed', Date.now().toString());
            this.hideBanner();
        },

        async install() {
            if (!this.deferredPrompt) {
                // Já instalado ou não disponível
                if (window.matchMedia('(display-mode: standalone)').matches) {
                    App.toast.info('App já está instalado! 📱');
                } else {
                    App.toast.info('Instalação não disponível neste navegador');
                }
                return;
            }

            // Mostrar prompt de instalação
            this.deferredPrompt.prompt();

            // Aguardar escolha do usuário
            const { outcome } = await this.deferredPrompt.userChoice;

            if (outcome === 'accepted') {
                console.log('✅ Usuário aceitou a instalação');
                App.toast.success('Instalando aplicativo... 📲');
            } else {
                console.log('❌ Usuário recusou a instalação');
                this.dismissBanner();
            }

            // Limpar prompt
            this.deferredPrompt = null;
        }
    }
}

// ========================================
// INICIALIZAÇÃO
// ========================================
document.addEventListener('DOMContentLoaded', () => {
    // Inicializar tema (PRIMEIRO)
    App.theme.init();
    
    // Inicializar PWA
    App.pwa.init();
    
    // Configurar sidebar toggle
    const sidebarToggle = document.querySelector('.sidebar-toggle');
    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', () => App.sidebar.toggle());
    }

    // Fechar modals ao clicar fora
    document.addEventListener('click', (e) => {
        if (e.target.classList.contains('modal')) {
            App.modal.close(e.target.id);
        }
    });

    // Carregar dados baseado na página
    const currentPage = window.location.pathname;
    
    if (currentPage.includes('index') || currentPage === '/') {
        loadUserData();
        loadAnnouncements();
        loadScales();
        loadCultCalendar();
    }
    
    if (currentPage.includes('membros')) {
        loadMembers();
    }
    
    if (currentPage.includes('cultos')) {
        loadCultos();
    }
    
    if (currentPage.includes('repertorio')) {
        loadRepertorio();
    }
    
    if (currentPage.includes('dashboard')) {
        loadDashboardStats();
    }

    // Marcar link ativo no menu
    const navLinks = document.querySelectorAll('.nav-link, .nav-item');
    navLinks.forEach(link => {
        if (link.href === window.location.href) {
            link.classList.add('active');
        }
    });

    // Animações de entrada
    const animatedElements = document.querySelectorAll('[class*="animate-"]');
    animatedElements.forEach((el, index) => {
        el.style.opacity = '0';
        setTimeout(() => {
            el.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
            el.style.opacity = '1';
        }, index * 100);
    });
});

// Exportar App para uso global
window.App = App;
