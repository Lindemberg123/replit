// Sistema Gmail Independente - JavaScript Frontend

// Sistema de Patrocínio
const SPONSORS = {
    gmail: {
        name: 'Gmail',
        logo: 'https://upload.wikimedia.org/wikipedia/commons/7/7e/Gmail_icon_%282020%29.svg',
        tagline: 'O melhor email do mundo',
        cta: 'Criar conta Gmail',
        url: 'https://gmail.com',
        color: '#ea4335'
    },
    google: {
        name: 'Google',
        logo: 'https://upload.wikimedia.org/wikipedia/commons/2/2f/Google_2015_logo.svg',
        tagline: 'Busque tudo com Google',
        cta: 'Pesquisar no Google',
        url: 'https://google.com',
        color: '#4285f4'
    },
    cocacola: {
        name: 'Coca-Cola',
        logo: 'https://upload.wikimedia.org/wikipedia/commons/c/ce/Coca-Cola_logo.svg',
        tagline: 'Abra a felicidade',
        cta: 'Saiba mais',
        url: 'https://coca-cola.com',
        color: '#ed1c16'
    },
    callofduty: {
        name: 'Call of Duty',
        logo: 'https://logos-world.net/wp-content/uploads/2021/02/Call-of-Duty-Logo.png',
        tagline: 'Entre na batalha',
        cta: 'Jogar agora',
        url: 'https://callofduty.com',
        color: '#000000'
    },
    stumbleguys: {
        name: 'Stumble Guys',
        logo: 'https://play-lh.googleusercontent.com/Kf8WTct65hFJxBUDm5E-EpYsiDoLQiGGbnuyP6HBNax43YShXti9THPon1YKB6zPYpA',
        tagline: 'Diversão sem fim',
        cta: 'Baixar jogo',
        url: 'https://stumbleguys.com',
        color: '#ff6b35'
    }
};

let sponsorSettings = {
    showTopBanner: false,
    showSidebarAds: false,
    showEmailInserts: false,
    showFooter: false,
    closedBanners: JSON.parse(localStorage.getItem('gmail_closed_banners') || '[]')
};

// Configurações do sistema
USERS_FILE = 'users.json'
EMAILS_FILE = 'emails.json'
ADMIN_EMAIL = 'suport.com@gmail.oficial'

let currentFolder = 'inbox';
let currentEmail = null;
let userInfo = null;
let searchTimeout = null;

// Inicializar aplicação
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
    setupMobileFeatures();
});

async function initializeApp() {
    try {
        // Verificar se não estamos na página de login
        if (window.location.pathname.includes('login.html')) {
            return;
        }

        await loadUserInfo();

        // Só carregar emails se o usuário estiver logado
        if (userInfo) {
            await loadEmails();
            setupEventListeners();
            showNotification('Gmail carregado com sucesso!', 'success');
        }
    } catch (error) {
        console.error('Erro ao inicializar:', error);
        showNotification('Erro ao carregar Gmail', 'error');
    }
}

function setupEventListeners() {
    // Navegação
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', function() {
            const folder = this.dataset.folder;
            if (folder) {
                switchFolder(folder);
            }
        });
    });

    // Formulário de composição
    const composeForm = document.getElementById('composeForm');
    if (composeForm) {
        composeForm.addEventListener('submit', handleSendEmail);
    }

    // Botão escrever
    const composeBtn = document.querySelector('.compose-btn');
    if (composeBtn) {
        composeBtn.addEventListener('click', showCompose);
    }

    // Busca
    document.getElementById('searchInput').addEventListener('input', handleSearch);

    // Atalhos de teclado
    document.addEventListener('keydown', handleKeyboardShortcuts);
}

async function loadUserInfo() {
    try {
        const response = await fetch('/api/user-info');
        if (response.ok) {
            userInfo = await response.json();

            const userEmailEl = document.getElementById('userEmail');
            const userIdEl = document.getElementById('userId');
            const userProfilePicEl = document.getElementById('userProfilePic');
            const adminPanelEl = document.getElementById('adminPanel');

            if (userEmailEl) userEmailEl.textContent = userInfo.name;
            if (userIdEl) userIdEl.textContent = `ID: ${userInfo.user_id}`;

            if (userInfo.profile_pic && userProfilePicEl) {
                userProfilePicEl.src = userInfo.profile_pic;
            }

            // Mostrar painel admin se for administrador
            if (userInfo.is_admin && adminPanelEl) {
                adminPanelEl.style.display = 'block';
            }

            updateCounts();
        } else if (response.status === 401) {
            // Usuário não logado, redirecionar para login apenas se não estiver já na página de login
            if (!window.location.pathname.includes('login.html')) {
                window.location.href = '/login.html';
            }
        }
    } catch (error) {
        console.error('Erro ao carregar info do usuário:', error);
        // Não redirecionar automaticamente em caso de erro de rede
        if (!window.location.pathname.includes('login.html')) {
            setTimeout(() => {
                window.location.href = '/login.html';
            }, 2000);
        }
    }
}

function updateCounts() {
    if (userInfo) {
        document.getElementById('inboxCount').textContent = userInfo.inbox_count;
        document.getElementById('sentCount').textContent = userInfo.sent_count;
        document.getElementById('draftsCount').textContent = userInfo.drafts_count;
    }
}

async function loadEmails() {
    try {
        showLoading();
        let response;

        if (currentFolder === 'highlighted') {
            response = await fetch('/api/admin/highlighted-emails');
        } else {
            response = await fetch(`/api/emails/${currentFolder}`);
        }

        if (response.ok) {
            const emails = await response.json();
            
            // Garantir que emails é um array
            if (Array.isArray(emails)) {
                displayEmails(emails);
            } else {
                console.error('Resposta não é um array:', emails);
                displayEmails([]);
            }
        } else {
            throw new Error(`Falha ao carregar emails: ${response.status}`);
        }
    } catch (error) {
        console.error('Erro ao carregar emails:', error);
        showEmptyState('Erro ao carregar emails. Tente novamente.');
    }
}

function displayEmails(emails) {
    const container = document.getElementById('emailsContainer');

    if (!emails || emails.length === 0) {
        showEmptyState(getEmptyMessage());
        return;
    }

    container.innerHTML = emails.map(email => {
        let emailClass = email.read ? '' : 'unread';
        if (email.highlighted) emailClass += ' highlighted';
        if (email.verification) {
            emailClass += ' verification';

            // Classes específicas para verificações avançadas
            if (email.verification_advanced) emailClass += ' advanced';
            if (email.verification_premium) emailClass += ' premium';
            if (email.verification_type === 'enterprise') emailClass += ' enterprise';
            if (email.verification_type === 'vip') emailClass += ' vip';

            // Classes de prioridade
            emailClass += ` ${getVerificationPriorityClass(email)}`;
        }
        if (email.password_reset) emailClass += ' password-reset';
        if (email.notification) emailClass += ' notification';

        // Determinar ícone e cor do highlight baseado no tipo
        let highlightIcon = 'fa-star-of-life';
        let highlightColor = '#ff6b35';
        let highlightContent = '';

        if (email.verification) {
            if (email.verification_premium) {
                highlightIcon = 'fa-crown';
                highlightColor = '#ff6b35';
            } else if (email.verification_type === 'enterprise') {
                highlightIcon = 'fa-building';
                highlightColor = '#673ab7';
            } else if (email.verification_type === 'vip') {
                highlightIcon = 'fa-star';
                highlightColor = '#ff9800';
            } else {
                highlightIcon = 'fa-shield-alt';
                highlightColor = '#34a853';
            }

            // Adicionar indicador de expiração
            if (email.verification_expires && isEmailExpired(email)) {
                highlightContent = `<div class="email-highlight" style="background: #ea4335;"><i class="fas fa-clock"></i></div>`;
            } else {
                highlightContent = `<div class="email-highlight" style="background: ${highlightColor};"><i class="fas ${highlightIcon}"></i></div>`;
            }
        }

        // Snippet personalizado para verificações
        let snippet = (email.body || '').substring(0, 100);
        if (email.verification && email.verification_type) {
            snippet = `🔐 ${formatVerificationType(email.verification_type)} - ${snippet}`;
        }

        // Data com indicador de prioridade
        let dateDisplay = formatDate(email.date);
        if (email.verification_priority && email.verification_priority !== 'normal') {
            const priorityEmojis = {
                'high': '⚡',
                'critical': '🚨',
                'urgent': '🔥'
            };
            dateDisplay = `${priorityEmojis[email.verification_priority] || ''} ${dateDisplay}`;
        }

        return `
        <div class="email-item ${emailClass}" onclick="openEmail('${email.id}')">
            <div class="email-checkbox">
                <input type="checkbox" onchange="toggleEmailSelection('${email.id}')">
            </div>
            <div class="email-star ${email.starred ? 'starred' : ''}" onclick="toggleStar('${email.id}', event)">
                <i class="fas fa-star"></i>
            </div>
            ${email.highlighted && !email.verification ? `<div class="email-highlight"><i class="fas ${highlightIcon}"></i></div>` : ''}
            ${highlightContent}
            ${email.password_reset ? '<div class="email-highlight" style="background: #fbbc04; color: #333;"><i class="fas fa-key"></i></div>' : ''}
            ${email.notification && !email.verification ? '<div class="email-highlight" style="background: #4285f4;"><i class="fas fa-bell"></i></div>' : ''}
            <div class="email-sender">${email.from || 'Sem remetente'}</div>
            <div class="email-content-preview">
                <div class="email-subject">${email.subject || 'Sem assunto'}</div>
                <div class="email-snippet">${snippet}${snippet.length > 100 ? '...' : ''}</div>
            </div>
            <div class="email-date">${dateDisplay}</div>
        </div>
        `;
    }).join('');

        // Sistema de anúncios desabilitado
}

function showLoading() {
    document.getElementById('emailsContainer').innerHTML = `
        <div class="loading">
            <i class="fas fa-spinner fa-spin"></i>
            <span>Carregando emails...</span>
        </div>
    `;
}

function showEmptyState(message) {
    document.getElementById('emailsContainer').innerHTML = `
        <div class="empty-state">
            <i class="fas fa-inbox"></i>
            <h3>${message}</h3>
            <p>Não há emails para mostrar</p>
        </div>
    `;
}

function getEmptyMessage() {
    const messages = {
        'inbox': 'Caixa de entrada vazia',
        'sent': 'Nenhum email enviado',
        'drafts': 'Nenhum rascunho salvo',
        'starred': 'Nenhum email com estrela'
    };
    return messages[currentFolder] || 'Pasta vazia';
}

function switchFolder(folder) {
    // Atualizar item ativo
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.remove('active');
    });
    const folderElement = document.querySelector(`.nav-item[data-folder="${folder}"]`);
    if (folderElement) {
        folderElement.classList.add('active');
    }

    // Atualizar título
    const titles = {
        'inbox': 'Caixa de entrada',
        'sent': 'Enviados',
        'drafts': 'Rascunhos',
        'starred': 'Com estrela',
        'highlighted': 'Emails Destacados'
    };
    document.getElementById('folderTitle').textContent = titles[folder] || 'Emails';

    // Carregar emails
    currentFolder = folder;
    
    // Garantir que estamos na visualização de lista
    document.getElementById('emailList').style.display = 'flex';
    document.getElementById('emailView').style.display = 'none';
    currentEmail = null;
    
    // Carregar emails
    loadEmails();
}

async function openEmail(emailId) {
    try {
        const response = await fetch(`/api/email/${emailId}`);
        if (response.ok) {
            const email = await response.json();
            currentEmail = email;

            // Verificar se é mobile e usar função apropriada
            if (window.innerWidth <= 768) {
                showEmailViewMobile(email);
            } else {
                showEmailView(email);
            }

            // Atualizar contadores se o email não estava lido
            if (!email.read) {
                loadUserInfo();
            }
        }
    } catch (error) {
        console.error('Erro ao carregar email:', error);
        showNotification('Erro ao carregar email', 'error');
    }
}

function showEmailView(email) {
    document.getElementById('emailList').style.display = 'none';
    document.getElementById('emailView').style.display = 'flex';

    // Atualizar botão de estrela
    const starBtn = document.getElementById('starBtn');
    if (starBtn) {
        starBtn.className = email.starred ? 'starred' : '';
    }

    // Atualizar botão de destaque (apenas para admin)
    const highlightBtn = document.getElementById('highlightBtn');
    if (highlightBtn && userInfo && userInfo.is_admin) {
        highlightBtn.style.display = 'block';
        highlightBtn.className = email.highlighted ? 'highlighted' : '';
    }

    let badges = '';
    let specialHeader = '';

    // Headers especiais para verificações avançadas
    if (email.verification_premium) {
        specialHeader = `
            <div class="premium-verification-header">
                <i class="fas fa-crown"></i>
                <div>
                    <strong>Verificação Premium</strong>
                    <div style="font-size: 12px; opacity: 0.9;">
                        Tipo: ${email.verification_type || 'Premium'} | 
                        Prioridade: ${email.verification_priority || 'Alta'} |
                        ID: ${email.tracking_id || 'N/A'}
                    </div>
                </div>
                <div class="verification-status-indicator ${isEmailExpired(email) ? 'expired' : ''}"></div>
            </div>
        `;
    } else if (email.verification_type === 'enterprise') {
        specialHeader = `
            <div class="enterprise-verification-header">
                <i class="fas fa-building"></i>
                <div>
                    <strong>Verificação Empresarial</strong>
                    <div style="font-size: 12px; opacity: 0.9;">
                        Nível Corporativo | Segurança Avançada | ID: ${email.tracking_id || 'N/A'}
                    </div>
                </div>
                <div class="verification-status-indicator ${isEmailExpired(email) ? 'expired' : ''}"></div>
            </div>
        `;
    } else if (email.verification_type === 'vip') {
        specialHeader = `
            <div class="vip-verification-header">
                <i class="fas fa-star"></i>
                <div>
                    <strong>Verificação VIP</strong>
                    <div style="font-size: 12px; opacity: 0.8;">
                        Acesso Exclusivo | Prioridade Máxima | ID: ${email.tracking_id || 'N/A'}
                    </div>
                </div>
                <div class="verification-status-indicator ${isEmailExpired(email) ? 'expired' : ''}"></div>
            </div>
        `;
    }

    // Badges tradicionais
    if (email.highlighted) {
        badges += '<div class="email-highlighted-badge"><i class="fas fa-star-of-life"></i> Email em Destaque</div>';
    }

    if (email.verification) {
        let verificationClass = 'email-verification-badge';
        let verificationIcon = 'fa-shield-alt';
        let verificationText = 'Email de Verificação';

        if (email.verification_advanced) {
            verificationClass += ' advanced';
        }

        if (email.verification_premium) {
            verificationClass = 'email-verification-badge premium';
            verificationIcon = 'fa-crown';
            verificationText = `Verificação ${email.verification_type?.toUpperCase() || 'Premium'}`;
        }

        badges += `<div class="${verificationClass}"><i class="fas ${verificationIcon}"></i> ${verificationText}</div>`;

        // Badge de expiração se aplicável
        if (email.verification_expires) {
            const expiryDate = new Date(email.verification_expires);
            const now = new Date();
            const isExpired = now > expiryDate;
            const timeLeft = isExpired ? 'Expirado' : getTimeUntilExpiry(expiryDate);

            badges += `
                <div class="email-verification-badge ${isExpired ? 'expired' : 'active'}" style="background: ${isExpired ? '#ea4335' : '#34a853'};">
                    <i class="fas ${isExpired ? 'fa-clock' : 'fa-hourglass-half'}"></i> 
                    ${timeLeft}
                </div>
            `;
        }

        // Badge de prioridade
        if (email.verification_priority && email.verification_priority !== 'normal') {
            const priorityColors = {
                'high': '#ff9800',
                'critical': '#ea4335',
                'urgent': '#9c27b0'
            };
            const priorityIcons = {
                'high': 'fa-exclamation',
                'critical': 'fa-exclamation-triangle',
                'urgent': 'fa-bolt'
            };

            badges += `
                <div class="email-verification-badge" style="background: ${priorityColors[email.verification_priority]};">
                    <i class="fas ${priorityIcons[email.verification_priority]}"></i> 
                    Prioridade ${email.verification_priority.toUpperCase()}
                </div>
            `;
        }
    }

    if (email.password_reset) {
        badges += '<div class="email-reset-badge"><i class="fas fa-key"></i> Recuperação de Senha</div>';
    }
    if (email.notification) {
        badges += '<div class="email-notification-badge"><i class="fas fa-bell"></i> Notificação</div>';
    }
    if (email.site_origin) {
        badges += `<div class="email-notification-badge"><i class="fas fa-external-link-alt"></i> Via: ${email.site_origin}</div>`;
    }

    // Badge de segurança
    if (email.security_level && email.security_level !== 'standard') {
        badges += `
            <div class="email-verification-badge" style="background: #673ab7;">
                <i class="fas fa-shield-check"></i> Segurança ${email.security_level.toUpperCase()}
            </div>
        `;
    }

    document.getElementById('emailContent').innerHTML = `
        ${specialHeader}
        <div class="email-header">
            <h1 class="email-title">${email.subject || 'Sem assunto'}</h1>
            <div class="email-meta">
                <div class="email-from">
                    <strong>De:</strong> ${email.from || 'Desconhecido'}
                </div>
                <div class="email-to">
                    <strong>Para:</strong> ${email.to || 'Desconhecido'}
                </div>
                <div class="email-date">
                    <strong>Data:</strong> ${formatDate(email.date)}
                </div>
                ${badges}
            </div>
        </div>
        <div class="email-body">${(email.body || '').replace(/\n/g, '<br>')}</div>
    `;
}

function backToList() {
    if (window.innerWidth <= 768) {
        backToListMobile();
    } else {
        document.getElementById('emailList').style.display = 'flex';
        document.getElementById('emailView').style.display = 'none';
        currentEmail = null;
        
        // Recarregar emails para mostrar a lista corretamente
        loadEmails();
    }
}

function showCompose() {
    document.getElementById('composeModal').classList.add('active');
    document.getElementById('composeTo').focus();
}

function closeCompose() {
    document.getElementById('composeModal').classList.remove('active');
    document.getElementById('composeForm').reset();
}

async function handleSendEmail(e) {
    e.preventDefault();

    const formData = {
        to: document.getElementById('composeTo').value,
        subject: document.getElementById('composeSubject').value,
        body: document.getElementById('composeBody').value
    };

    try {
        const response = await fetch('/api/send-email', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });

        const result = await response.json();

        if (response.ok) {
            showNotification('Email enviado com sucesso!', 'success');
            closeCompose();

            if (currentFolder === 'sent') {
                loadEmails();
            }

            loadUserInfo();
        } else {
            showNotification(`Erro: ${result.error}`, 'error');
        }
    } catch (error) {
        showNotification('Erro de conexão', 'error');
        console.error('Erro:', error);
    }
}

async function saveDraft() {
    const formData = {
        to: document.getElementById('composeTo').value,
        subject: document.getElementById('composeSubject').value,
        body: document.getElementById('composeBody').value
    };

    try {
        const response = await fetch('/api/save-draft', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });

        const result = await response.json();

        if (response.ok) {
            showNotification('Rascunho salvo!', 'success');
            closeCompose();

            if (currentFolder === 'drafts') {
                loadEmails();
            }

            loadUserInfo();
        } else {
            showNotification('Erro ao salvar rascunho', 'error');
        }
    } catch (error) {
        showNotification('Erro de conexão', 'error');
        console.error('Erro:', error);
    }
}

async function deleteEmail() {
    if (!currentEmail) return;

    if (confirm('Tem certeza que deseja excluir este email?')) {
        try {
            const response = await fetch(`/api/email/${currentEmail.id}/delete`, {
                method: 'DELETE'
            });

            if (response.ok) {
                showNotification('Email excluído', 'success');
                backToList();
                loadEmails();
                loadUserInfo();
            } else {
                showNotification('Erro ao excluir email', 'error');
            }
        } catch (error) {
            showNotification('Erro de conexão', 'error');
            console.error('Erro:', error);
        }
    }
}

async function toggleStar(emailId, event) {
    event.stopPropagation();

    try {
        const response = await fetch(`/api/email/${emailId}/star`, {
            method: 'POST'
        });

        if (response.ok) {
            const result = await response.json();

            // Atualizar visual da estrela
            const starElement = event.target.closest('.email-star');
            if (result.starred) {
                starElement.classList.add('starred');
            } else {
                starElement.classList.remove('starred');
            }

            // Recarregar se estiver na pasta de favoritos
            if (currentFolder === 'starred') {
                loadEmails();
            }
        }
    } catch (error) {
        console.error('Erro ao favoritar email:', error);
    }
}

async function starCurrentEmail() {
    if (!currentEmail) return;

    try {
        const response = await fetch(`/api/email/${currentEmail.id}/star`, {
            method: 'POST'
        });

        if (response.ok) {
            const result = await response.json();
            const starBtn = document.getElementById('starBtn');

            if (result.starred) {
                starBtn.classList.add('starred');
                showNotification('Email marcado com estrela', 'success');
            } else {
                starBtn.classList.remove('starred');
                showNotification('Estrela removida', 'info');
            }

            currentEmail.starred = result.starred;
        }
    } catch (error) {
        showNotification('Erro ao favoritar email', 'error');
        console.error('Erro:', error);
    }
}

async function refreshEmails() {
    try {
        const response = await fetch('/api/refresh-emails', {
            method: 'POST'
        });

        const result = await response.json();

        if (response.ok) {
            showNotification('Emails atualizados', 'success');
            loadEmails();
            loadUserInfo();
        } else {
            showNotification('Erro ao atualizar emails', 'error');
        }
    } catch (error) {
        showNotification('Erro de conexão', 'error');
        console.error('Erro:', error);
    }
}

async function handleSearch(e) {
    const query = e.target.value.trim();

    // Limpar timeout anterior
    if (searchTimeout) {
        clearTimeout(searchTimeout);
    }

    // Aguardar 300ms antes de buscar
    searchTimeout = setTimeout(async () => {
        if (query.length > 0) {
            try {
                const response = await fetch('/api/search', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ query })
                });

                if (response.ok) {
                    const results = await response.json();
                    displayEmails(results);
                }
            } catch (error) {
                console.error('Erro na busca:', error);
            }
        } else {
            loadEmails();
        }
    }, 300);
}

function replyToEmail() {
    if (!currentEmail) return;

    document.getElementById('composeTo').value = currentEmail.from;
    document.getElementById('composeSubject').value = 'Re: ' + currentEmail.subject;
    document.getElementById('composeBody').value = `\n\n--- Email original ---\n${currentEmail.body}`;

    showCompose();
}

function handleKeyboardShortcuts(e) {
    if (e.ctrlKey || e.metaKey) {
        switch (e.key) {
            case 'c':
                e.preventDefault();
                showCompose();
                break;
            case 'r':
                e.preventDefault();
                refreshEmails();
                break;
        }
    } else if (e.key === 'Escape') {
        if (document.getElementById('composeModal').classList.contains('active')) {
            closeCompose();
        } else if (currentEmail) {
            backToList();
        }
    }
}

function formatDate(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const diffTime = Math.abs(now - date);
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

    if (diffDays === 1) {
        return date.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
    } else if (diffDays === 2) {
        return 'Ontem';
    } else if (diffDays <= 7) {
        return `${diffDays} dias atrás`;
    } else {
        return date.toLocaleDateString('pt-BR');
    }
}

function showNotification(message, type = 'success') {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.innerHTML = `
        <i class="fas fa-${type === 'success' ? 'check' : type === 'error' ? 'times' : 'info'}-circle"></i>
        <span>${message}</span>
    `;

    document.getElementById('notifications').appendChild(notification);

    setTimeout(() => {
        notification.classList.add('show');
    }, 100);

    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => {
            notification.remove();
        }, 300);
    }, 3000);
}

// Funções auxiliares
function toggleEmailSelection(emailId) {
    // Implementar seleção múltipla
    console.log('Email selecionado:', emailId);
}

function markAllAsRead() {
    // Implementar marcar todos como lidos
    showNotification('Todos os emails marcados como lidos', 'success');
}

// Funcionalidades Mobile
function setupMobileFeatures() {
    // Detectar dispositivo móvel
    const isMobile = window.innerWidth <= 768;

    if (isMobile) {
        document.body.classList.add('mobile');
        setupMobileNavigation();
        setupTouchGestures();
        setupMobileEmailView();
    }

    // Listener para mudanças de orientação
    window.addEventListener('orientationchange', function() {
        setTimeout(() => {
            adjustForOrientation();
        }, 100);
    });

    // Listener para redimensionamento
    window.addEventListener('resize', function() {
        const isMobileNow = window.innerWidth <= 768;
        if (isMobileNow !== isMobile) {
            location.reload(); // Recarregar para aplicar mudanças
        }
    });
}

function setupMobileNavigation() {
    // Criar overlay para fechar sidebar
    const overlay = document.createElement('div');
    overlay.className = 'mobile-overlay';
    overlay.id = 'mobileOverlay';
    document.body.appendChild(overlay);

    // Toggle sidebar no mobile
    const menuIcon = document.querySelector('.menu-icon');
    if (menuIcon) {
        menuIcon.addEventListener('click', toggleMobileSidebar);
    }

    // Fechar sidebar ao clicar no overlay
    overlay.addEventListener('click', closeMobileSidebar);

    // Fechar sidebar ao selecionar item
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', function() {
            if (window.innerWidth <= 768) {
                closeMobileSidebar();
            }
        });
    });
}

function toggleMobileSidebar() {
    const sidebar = document.querySelector('.sidebar');
    const overlay = document.getElementById('mobileOverlay');

    sidebar.classList.toggle('active');
    overlay.classList.toggle('active');
}

function closeMobileSidebar() {
    const sidebar = document.querySelector('.sidebar');
    const overlay = document.getElementById('mobileOverlay');

    sidebar.classList.remove('active');
    overlay.classList.remove('active');
}

function setupMobileEmailView() {
    const emailView = document.getElementById('emailView');

    // Adicionar classe para controle mobile
    if (emailView) {
        emailView.classList.add('mobile-email-view');
    }
}

function setupTouchGestures() {
    // Swipe para voltar no email view
    let startX = 0;
    let startY = 0;

    document.addEventListener('touchstart', function(e) {
        startX = e.touches[0].clientX;
        startY = e.touches[0].clientY;
    });

    document.addEventListener('touchend', function(e) {
        if (!startX || !startY) return;

        const endX = e.changedTouches[0].clientX;
        const endY = e.changedTouches[0].clientY;

        const diffX = startX - endX;
        const diffY = startY - endY;

        // Swipe horizontal
        if (Math.abs(diffX) > Math.abs(diffY)) {
            // Swipe right para voltar (apenas se email estiver aberto)
            if (diffX < -50 && currentEmail && window.innerWidth <= 768) {
                backToList();
            }
        }

        startX = 0;
        startY = 0;
    });
}

function adjustForOrientation() {
    // Ajustar layout para mudanças de orientação
    const isMobile = window.innerWidth <= 768;

    if (isMobile) {
        // Fechar sidebar se estiver aberta
        closeMobileSidebar();

        // Ajustar altura do compose modal
        const composeModal = document.getElementById('composeModal');
        if (composeModal && composeModal.classList.contains('active')) {
            // Reajustar altura
            setTimeout(() => {
                const textarea = document.getElementById('composeBody');
                if (textarea) {
                    textarea.style.height = 'auto';
                    textarea.style.height = (textarea.scrollHeight) + 'px';
                }
            }, 100);
        }
    }
}

// Função mobile para email view
function showEmailViewMobile(email) {
    // Primeiro mostrar o email
    showEmailView(email);

    // Adicionar comportamento mobile
    if (window.innerWidth <= 768) {
        const emailView = document.getElementById('emailView');
        const emailList = document.getElementById('emailList');

        if (emailView && emailList) {
            // Esconder lista e mostrar visualização
            emailList.style.display = 'none';
            emailView.style.display = 'flex';
            emailView.classList.add('active');
            emailView.scrollTop = 0;
        }
    }
}

// Função mobile para voltar à lista
function backToListMobile() {
    if (window.innerWidth <= 768) {
        const emailView = document.getElementById('emailView');
        const emailList = document.getElementById('emailList');
        
        if (emailView) {
            emailView.classList.remove('active');
        }

        setTimeout(() => {
            if (emailView && emailList) {
                emailView.style.display = 'none';
                emailList.style.display = 'flex';
            }
            currentEmail = null;
            
            // Recarregar emails para mostrar a lista corretamente
            loadEmails();
        }, 300);
    } else {
        backToList();
    }
}

// Função mobile para compose
function showComposeMobile() {
    showCompose();

    // Comportamento mobile
    if (window.innerWidth <= 768) {
        // Fechar sidebar se estiver aberta
        closeMobileSidebar();

        // Ajustar foco
        setTimeout(() => {
            const toField = document.getElementById('composeTo');
            if (toField) {
                toField.focus();
                toField.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
        }, 100);
    }
}

// Função para detectar se é dispositivo touch
function isTouchDevice() {
    return (('ontouchstart' in window) ||
           (navigator.maxTouchPoints > 0) ||
           (navigator.msMaxTouchPoints > 0));
}

// Otimizações para performance mobile
function optimizeForMobile() {
    // Lazy loading para emails
    const emailsContainer = document.getElementById('emailsContainer');
    if (emailsContainer && 'IntersectionObserver' in window) {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    // Carregar conteúdo quando visível
                    entry.target.classList.add('loaded');
                }
            });
        });

        // Observar emails
        emailsContainer.querySelectorAll('.email-item').forEach(item => {
            observer.observe(item);
        });
    }
}

// Configurações específicas para PWA (Progressive Web App)
function setupPWA() {
    // Service Worker para cache offline
    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.register('/sw.js').catch(() => {
            // Service worker não disponível
        });
    }

    // Prevenir zoom em inputs no iOS
    if (/iPad|iPhone|iPod/.test(navigator.userAgent)) {
        const viewportMeta = document.querySelector('meta[name="viewport"]');
        if (viewportMeta) {
            viewportMeta.content = 'width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no';
        }
    }
}

// Funções de autenticação
async function logout() {
    if (confirm('Tem certeza que deseja sair?')) {
        try {
            await fetch('/api/logout', { method: 'POST' });
            window.location.href = '/login.html';
        } catch (error) {
            console.error('Erro ao fazer logout:', error);
            window.location.href = '/login.html';
        }
    }
}

// Funções de administração
function showBroadcast() {
    document.getElementById('broadcastModal').classList.add('active');
    document.getElementById('broadcastSubject').focus();
}

function closeBroadcast() {
    document.getElementById('broadcastModal').classList.remove('active');
    document.getElementById('broadcastForm').reset();
}

async function handleBroadcast(e) {
    e.preventDefault();

    const formData = {
        subject: document.getElementById('broadcastSubject').value,
        body: document.getElementById('broadcastBody').value
    };

    try {
        const response = await fetch('/api/admin/broadcast', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });

        const result = await response.json();

        if (response.ok) {
            showNotification(`Email enviado para ${result.sent_to} usuários!`, 'success');
            closeBroadcast();
        } else {
            showNotification(`Erro: ${result.error}`, 'error');
        }
    } catch (error) {
        showNotification('Erro de conexão', 'error');
        console.error('Erro:', error);
    }
}

function showUsers() {
    document.getElementById('usersModal').classList.add('active');
    loadUsers();
}

function closeUsers() {
    document.getElementById('usersModal').classList.remove('active');
}

async function loadUsers() {
    try {
        const response = await fetch('/api/admin/users');
        if (response.ok) {
            const users = await response.json();
            displayUsers(users);
        }
    } catch (error) {
        console.error('Erro ao carregar usuários:', error);
    }
}

function displayUsers(users) {
    const container = document.getElementById('usersList');

    if (users.length === 0) {
        container.innerHTML = '<p>Nenhum usuário encontrado</p>';
        return;
    }

    container.innerHTML = users.map(user => `
        <div class="user-item">
            <div class="user-info-item">
                <img src="https://ui-avatars.com/api/?name=${encodeURIComponent(user.name)}&background=4285f4&color=fff" 
                     alt="${user.name}" class="user-avatar-small">
                <div class="user-details-item">
                    <div class="user-name-item">${user.name} ${user.is_admin ? '<i class="fas fa-crown admin-badge"></i>' : ''}</div>
                    <div class="user-email-item">${user.email}</div>
                    <div class="user-id-item">ID: ${user.user_id}</div>
                    <div class="user-date-item">Criado: ${formatDate(user.created_at)}</div>
                </div>
            </div>
        </div>
    `).join('');
}

function showSystemLogs() {
    document.getElementById('systemLogsModal').classList.add('active');
    loadSystemLogs();
}

function closeSystemLogs() {
    document.getElementById('systemLogsModal').classList.remove('active');
}

async function loadSystemLogs() {
    try {
        const response = await fetch('/api/admin/system-logs');
        if (response.ok) {
            const logs = await response.json();
            displaySystemLogs(logs);
        }
    } catch (error) {
        console.error('Erro ao carregar logs:', error);
    }
}

function displaySystemLogs(logs) {
    const container = document.getElementById('systemLogsList');

    if (logs.length === 0) {
        container.innerHTML = '<p>Nenhum log encontrado</p>';
        return;
    }

    container.innerHTML = logs.map(log => `
        <div class="user-item">
            <div class="user-info-item">
                <i class="fas fa-file-alt" style="color: #ff6b35; font-size: 20px; margin-right: 12px;"></i>
                <div class="user-details-item">
                    <div class="user-name-item">${log.subject}</div>
                    <div class="user-email-item">${log.body.substring(0, 100)}${log.body.length > 100 ? '...' : ''}</div>
                    <div class="user-date-item">${formatDate(log.date)}</div>
                </div>
            </div>
        </div>
    `).join('');
}

// Event listeners para modais admin
document.addEventListener('DOMContentLoaded', function() {
    const broadcastForm = document.getElementById('broadcastForm');
    if (broadcastForm) {
        broadcastForm.addEventListener('submit', handleBroadcast);
    }
});

// Função para destacar email (apenas admin)
async function highlightCurrentEmail() {
    if (!currentEmail || !userInfo || !userInfo.is_admin) return;

    try {
        const response = await fetch(`/api/email/${currentEmail.id}/highlight`, {
            method: 'POST'
        });

        if (response.ok) {
            const result = await response.json();
            const highlightBtn = document.getElementById('highlightBtn');

            if (result.highlighted) {
                highlightBtn.classList.add('highlighted');
                showNotification('Email marcado como destaque', 'success');
            } else {
                highlightBtn.classList.remove('highlighted');
                showNotification('Destaque removido', 'info');
            }

            currentEmail.highlighted = result.highlighted;
        }
    } catch (error) {
        showNotification('Erro ao destacar email', 'error');
        console.error('Erro:', error);
    }
}

// Atualizar loadUserInfo para mostrar elementos admin
async function loadUserInfo() {
    try {
        const response = await fetch('/api/user-info');
        if (response.ok) {
            userInfo = await response.json();

            const userEmailEl = document.getElementById('userEmail');
            const userIdEl = document.getElementById('userId');
            const userProfilePicEl = document.getElementById('userProfilePic');

            if (userEmailEl) userEmailEl.textContent = userInfo.name;
            if (userIdEl) userIdEl.textContent = `ID: ${userInfo.user_id}`;

            if (userInfo.profile_pic && userProfilePicEl) {
                userProfilePicEl.src = userInfo.profile_pic;
            }

            // Mostrar elementos admin
            if (userInfo.is_admin) {
                console.log('Usuário é admin, mostrando elementos admin');
                document.querySelectorAll('.admin-item').forEach(el => {
                    el.style.display = 'flex';
                    console.log('Mostrando elemento admin:', el);
                });
                document.querySelectorAll('.admin-only').forEach(el => {
                    el.style.display = el.tagName === 'BUTTON' ? 'inline-block' : 'block';
                    console.log('Mostrando elemento admin-only:', el);
                });

                // Adicionar painel de broadcast
                const composeBtn = document.querySelector('.compose-btn');
                if (composeBtn && !document.getElementById('broadcastBtn')) {
                    const broadcastBtn = document.createElement('button');
                    broadcastBtn.id = 'broadcastBtn';
                    broadcastBtn.className = 'compose-btn admin-broadcast-btn';
                    broadcastBtn.innerHTML = '<i class="fas fa-bullhorn"></i> Enviar para Todos';
                    broadcastBtn.onclick = showBroadcast;
                    composeBtn.parentNode.insertBefore(broadcastBtn, composeBtn.nextSibling);
                }
            }

            updateCounts();
        } else if (response.status === 401) {
            if (!window.location.pathname.includes('login.html')) {
                window.location.href = '/login.html';
            }
        }
    } catch (error) {
        console.error('Erro ao carregar info do usuário:', error);
        if (!window.location.pathname.includes('login.html')) {
            setTimeout(() => {
                window.location.href = '/login.html';
            }, 2000);
        }
    }
}

// Funções auxiliares para verificações avançadas
function isEmailExpired(email) {
    if (!email.verification_expires) return false;
    const expiryDate = new Date(email.verification_expires);
    const now = new Date();
    return now > expiryDate;
}

function getTimeUntilExpiry(expiryDate) {
    const now = new Date();
    const diffMs = expiryDate - now;

    if (diffMs <= 0) return 'Expirado';

    const diffMins = Math.floor(diffMs / (1000 * 60));
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

    if (diffDays > 0) return `${diffDays}d`;
    if (diffHours > 0) return `${diffHours}h`;
    if (diffMins > 0) return `${diffMins}m`;
    return 'Expirando';
}

function getVerificationPriorityClass(email) {
    if (!email.verification_priority) return '';

    const priorityClasses = {
        'high': 'verification-priority-high',
        'critical': 'verification-priority-critical',
        'urgent': 'verification-priority-urgent'
    };

    return priorityClasses[email.verification_priority] || '';
}

function formatVerificationType(type) {
    const types = {
        'account': 'Conta',
        'email': 'Email',
        'phone': 'Telefone',
        'security': 'Segurança',
        'two_factor': '2FA',
        'premium': 'Premium',
        'enterprise': 'Empresarial',
        'vip': 'VIP'
    };

    return types[type] || type;
}

// Auto-refresh para verificações com expiração
function startVerificationAutoRefresh() {
    setInterval(() => {
        // Atualizar apenas se houver emails de verificação visíveis
        const currentEmailsContainer = document.getElementById('emailsContainer');
        const hasVerificationEmails = currentEmailsContainer && 
            currentEmailsContainer.innerHTML.includes('verification-status-indicator');

        if (hasVerificationEmails) {
            // Recarregar emails silenciosamente para atualizar status de expiração
            loadEmails();
        }
    }, 30000); // A cada 30 segundos
}

// Inicializar auto-refresh quando o app carregar
document.addEventListener('DOMContentLoaded', function() {
    setTimeout(startVerificationAutoRefresh, 5000); // Iniciar após 5s
});

console.log('Sistema Gmail Independente carregado!');
console.log('Atalhos: Ctrl+C para escrever, Ctrl+R para atualizar, Esc para voltar');
console.log('Mobile: Swipe direita para voltar, toque no menu para navegação');
console.log('Admin: suport.com@gmail.oficial');
console.log('🔐 Sistema de Verificação Avançada ativo!');

// --- Funções para o sistema de patrocínio ---
function showSponsorBanner() {
    if (!sponsorSettings.showTopBanner) return;

    const sponsorKeys = Object.keys(SPONSORS);
    const randomSponsorKey = sponsorKeys[Math.floor(Math.random() * sponsorKeys.length)];
    const sponsor = SPONSORS[randomSponsorKey];

    if (sponsorSettings.closedBanners.includes(sponsor.name)) return;

    const banner = document.createElement('div');
    banner.className = 'sponsor-banner';
    banner.style.backgroundColor = sponsor.color;
    banner.innerHTML = `
        <div class="sponsor-banner-content">
            <img src="${sponsor.logo}" alt="${sponsor.name} Logo" class="sponsor-banner-logo">
            <div class="sponsor-banner-text">
                <h3>${sponsor.name}</h3>
                <p>${sponsor.tagline}</p>
            </div>
            <a href="${sponsor.url}" class="sponsor-banner-cta">${sponsor.cta}</a>
            <button class="sponsor-banner-close" onclick="closeSponsorBanner('${sponsor.name}')">&times;</button>
        </div>
    `;
    document.body.insertBefore(banner, document.body.firstChild);
}

function closeSponsorBanner(sponsorName) {
    const banner = document.querySelector('.sponsor-banner');
    if (banner) banner.remove();

    sponsorSettings.closedBanners.push(sponsorName);
    localStorage.setItem('gmail_closed_banners', JSON.stringify(sponsorSettings.closedBanners));
}

function getSponsorFooter() {
    const sponsorKeys = Object.keys(SPONSORS);
    const randomSponsorKey = sponsorKeys[Math.floor(Math.random() * sponsorKeys.length)];
    const sponsor = SPONSORS[randomSponsorKey];

    return `
        <div class="sponsor-footer">
            <p>Patrocinado por <a href="${sponsor.url}" style="color: ${sponsor.color};">${sponsor.name}</a></p>
        </div>
    `;
}