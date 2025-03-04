// script.js

document.addEventListener('DOMContentLoaded', () => {
    // Função para abrir/fechar o menu lateral
    function toggleSidebar() {
        const sidebar = document.querySelector('.sidebar');
        sidebar.classList.toggle('open');
    }

    // Adiciona evento ao botão do menu lateral
    const sidebarToggle = document.querySelector('.sidebar-toggle');
    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', toggleSidebar);
    }

    // Função para carregar dados do usuário (usada no index.html)
    function loadUserData() {
        fetch('/get_user_data')
            .then(response => response.json())
            .then(user => {
                if (user.logged_in) {
                    const memberName = document.getElementById('memberName');
                    const memberEmail = document.getElementById('memberEmail');
                    const memberInstrument = document.getElementById('memberInstrument');
                    const memberPhone = document.getElementById('memberPhone');

                    if (memberName) memberName.textContent = user.name;
                    if (memberEmail) memberEmail.textContent = user.email;
                    if (memberInstrument) memberInstrument.textContent = user.instrument || 'N/A';
                    if (memberPhone) memberPhone.textContent = user.phone || 'N/A';
                } else {
                    console.error('Usuário não encontrado ou não logado.');
                    alert('Erro ao carregar os dados do usuário. Tente novamente.');
                }
            })
            .catch(error => {
                console.error('Erro ao carregar os dados do usuário:', error);
                alert('Erro ao carregar os dados do usuário. Tente novamente.');
            });
    }

    // Função para carregar avisos (usada no index.html)
    function loadAnnouncements() {
        const announcementsList = document.getElementById('announcements');
        if (announcementsList) {
            fetch('/get_announcements')
                .then(response => response.json())
                .then(announcements => {
                    if (announcements.length === 0) {
                        announcementsList.innerHTML = '<p class="no-announcements">Nenhum aviso disponível.</p>';
                    } else {
                        announcementsList.innerHTML = '';
                        announcements.forEach(announcement => {
                            const div = document.createElement('div');
                            div.className = 'announcement-item';
                            div.innerHTML = `<p>${announcement.text}</p>`;
                            announcementsList.appendChild(div);
                            // Animação para novos avisos
                            div.style.opacity = '0';
                            setTimeout(() => {
                                div.style.transition = 'opacity 0.5s ease';
                                div.style.opacity = '1';
                            }, 100);
                        });
                    }
                })
                .catch(error => {
                    console.error('Erro ao carregar os avisos:', error);
                    announcementsList.innerHTML = '<p class="text-center text-danger">Erro ao carregar os avisos. Tente novamente.</p>';
                });
        }
    }

    // Função para carregar escalas (usada no index.html)
    function loadScales() {
        const scalePanel = document.getElementById('scalePanel');
        const scalesList = document.getElementById('scales');
        if (scalePanel && scalesList) {
            fetch('/get_user_scales')
                .then(response => response.json())
                .then(scales => {
                    if (scales.length > 0) {
                        scalePanel.style.display = 'block';
                        scalesList.innerHTML = '';
                        scales.forEach(item => {
                            const li = document.createElement('li');
                            li.className = 'list-group-item text-white';
                            li.textContent = `${item.culto.date} - ${item.culto.time}: ${item.culto.description}`;
                            scalesList.appendChild(li);
                            // Animação para novas escalas
                            li.style.opacity = '0';
                            setTimeout(() => {
                                li.style.transition = 'opacity 0.5s ease';
                                li.style.opacity = '1';
                            }, 100);
                        });
                    } else {
                        scalePanel.style.display = 'none';
                    }
                })
                .catch(error => {
                    console.error('Erro ao carregar as escalas:', error);
                    scalesList.innerHTML = '<li class="list-group-item text-danger">Erro ao carregar as escalas. Tente novamente.</li>';
                });
        }
    }

    // Função para carregar calendário de cultos (usada no index.html)
    function loadCultCalendar() {
        const cultCalendar = document.getElementById('cultCalendar');
        if (cultCalendar) {
            fetch('/get_cult_calendar')
                .then(response => response.json())
                .then(cultsCalendar => {
                    cultCalendar.innerHTML = '';
                    cultsCalendar.forEach(cult => {
                        const li = document.createElement('li');
                        li.className = 'list-group-item text-white';
                        li.innerHTML = `<a href="#" class="text-danger">${cult.date} - ${cult.time}: ${cult.description}</a>`;
                        cultCalendar.appendChild(li);
                        // Animação para novos cultos
                        li.style.opacity = '0';
                        setTimeout(() => {
                            li.style.transition = 'opacity 0.5s ease';
                            li.style.opacity = '1';
                        }, 100);
                    });
                })
                .catch(error => {
                    console.error('Erro ao carregar o calendário de cultos:', error);
                    cultCalendar.innerHTML = '<li class="list-group-item text-danger">Erro ao carregar o calendário. Tente novamente.</li>';
                });
        }
    }

    // Função para carregar membros (usada no membros.html)
    function loadMembers() {
        const instrumentsContainer = document.getElementById('instrumentsContainer');
        if (instrumentsContainer) {
            fetch('/get_membros')  // Corrigido de '/get_members' para '/get_membros'
                .then(response => response.json())
                .then(members => {
                    instrumentsContainer.innerHTML = '';
                    const groupedMembers = members.reduce((acc, member) => {
                        if (!acc[member.instrument]) {
                            acc[member.instrument] = [];
                        }
                        acc[member.instrument].push(member);
                        return acc;
                    }, {});

                    Object.keys(groupedMembers).forEach(instrument => {
                        createInstrumentSection(instrument, groupedMembers[instrument]);
                    });
                })
                .catch(error => {
                    console.error('Erro ao carregar os membros:', error);
                    instrumentsContainer.innerHTML = '<p class="text-center text-danger">Erro ao carregar os membros. Tente novamente.</p>';
                });
        }
    }

    // Função auxiliar para criar seção de instrumentos (usada em loadMembers)
    function createInstrumentSection(instrument, members) {
        const section = document.createElement('div');
        section.className = 'member-group';

        const title = document.createElement('h3');
        title.className = 'member-group-title';
        title.textContent = instrument;
        section.appendChild(title);

        const list = document.createElement('ul');
        list.className = 'member-list';

        members.forEach(member => {
            const li = document.createElement('li');
            li.className = 'member-item';
            li.innerHTML = `
                <div class="member-info">
                    <strong>${member.name}</strong><br>
                    <span>Email: ${member.email}</span><br>
                    <span>Telefone: ${member.phone}
                        <a href="https://wa.me/${member.phone.replace(/\D/g, '')}" target="_blank" title="Contato no WhatsApp">
                            <i class="fab fa-whatsapp" style="color: #25d366;"></i>
                        </a>
                    </span>
                </div>
            `;
            list.appendChild(li);
            // Animação para novos membros
            li.style.opacity = '0';
            setTimeout(() => {
                li.style.transition = 'opacity 0.5s ease';
                li.style.opacity = '1';
            }, 100);
        });

        section.appendChild(list);
        instrumentsContainer.appendChild(section);
    }

    // Executa as funções com base na página atual
    if (document.getElementById('memberName')) {
        // Página index.html
        loadUserData();
        loadAnnouncements();
        loadScales();
        loadCultCalendar();
    } else if (document.getElementById('instrumentsContainer')) {
        // Página membros.html
        loadMembers();
    }

    // Adiciona animação suave ao rolar a página
    window.addEventListener('scroll', () => {
        const sections = document.querySelectorAll('.section-title, .member-group, .feature-card, .announcement-item');
        sections.forEach(section => {
            const rect = section.getBoundingClientRect();
            if (rect.top < window.innerHeight - 100) {
                section.classList.add('fade-in');
            }
        });
    });

    // Adiciona evento de clique para fechar o menu lateral ao clicar fora (opcional)
    document.addEventListener('click', (e) => {
        const sidebar = document.querySelector('.sidebar');
        const sidebarToggle = document.querySelector('.sidebar-toggle');
        if (!sidebar.contains(e.target) && !sidebarToggle.contains(e.target) && sidebar.classList.contains('open')) {
            sidebar.classList.remove('open');
        }
    });
});