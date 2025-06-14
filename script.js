// Sistema Gmail Independente - JavaScript Frontend

// Sistema de Anúncios de Empresas Famosas
const SPONSORS = {
    cocacola: {
        name: 'Coca-Cola',
        logo: 'https://upload.wikimedia.org/wikipedia/commons/c/ce/Coca-Cola_logo.svg',
        tagline: 'Abra a felicidade com Coca-Cola!',
        cta: 'Experimente agora',
        url: 'https://coca-cola.com',
        color: '#ed1c16',
        description: 'A bebida que une pessoas ao redor do mundo há mais de 130 anos.',
        category: 'bebidas'
    },
    uber: {
        name: 'Uber',
        logo: 'https://upload.wikimedia.org/wikipedia/commons/c/cc/Uber_logo_2018.png',
        tagline: 'Chegue onde quiser, quando quiser',
        cta: 'Baixar app',
        url: 'https://uber.com',
        color: '#000000',
        description: 'Transporte rápido, seguro e conveniente na palma da sua mão.',
        category: 'transporte'
    },
    nike: {
        name: 'Nike',
        logo: 'https://upload.wikimedia.org/wikipedia/commons/a/a6/Logo_NIKE.svg',
        tagline: 'Just Do It',
        cta: 'Comprar agora',
        url: 'https://nike.com',
        color: '#111111',
        description: 'Inspire-se e alcance seus objetivos com os melhores produtos esportivos.',
        category: 'esportes'
    },
    mcdonalds: {
        name: "McDonald's",
        logo: 'https://upload.wikimedia.org/wikipedia/commons/3/36/McDonald%27s_Golden_Arches.svg',
        tagline: "I'm Lovin' It",
        cta: 'Peça já',
        url: 'https://mcdonalds.com',
        color: '#ffcc00',
        description: 'Os sabores que você ama, agora mais perto de você.',
        category: 'alimentacao'
    },
    spotify: {
        name: 'Spotify',
        logo: 'https://upload.wikimedia.org/wikipedia/commons/1/19/Spotify_logo_without_text.svg',
        tagline: 'Música para todos',
        cta: 'Ouça grátis',
        url: 'https://spotify.com',
        color: '#1db954',
        description: 'Milhões de músicas e podcasts. Sem anúncios com Premium.',
        category: 'entretenimento'
    },
    netflix: {
        name: 'Netflix',
        logo: 'https://upload.wikimedia.org/wikipedia/commons/0/08/Netflix_2015_logo.svg',
        tagline: 'Entretenimento ilimitado',
        cta: 'Assista agora',
        url: 'https://netflix.com',
        color: '#e50914',
        description: 'Filmes, séries e documentários premiados quando e onde quiser.',
        category: 'entretenimento'
    },
    amazon: {
        name: 'Amazon',
        logo: 'https://upload.wikimedia.org/wikipedia/commons/a/a9/Amazon_logo.svg',
        tagline: 'Tudo o que você precisa',
        cta: 'Comprar',
        url: 'https://amazon.com',
        color: '#ff9900',
        description: 'Milhões de produtos com entrega rápida e segura.',
        category: 'ecommerce'
    },
    samsung: {
        name: 'Samsung',
        logo: 'https://upload.wikimedia.org/wikipedia/commons/2/24/Samsung_Logo.svg',
        tagline: 'Inovação que inspira',
        cta: 'Descobrir',
        url: 'https://samsung.com',
        color: '#1428a0',
        description: 'Tecnologia de ponta para facilitar sua vida.',
        category: 'tecnologia'
    }
};

let sponsorSettings = {
    showTopBanner: true,
    showSidebarAds: true,
    showEmailInserts: true,
    showFooter: true,
    showEmbeddedAds: true,
    closedBanners: JSON.parse(localStorage.getItem('gmail_closed_banners') || '[]')
};

// Sistema de rotação de anúncios
let currentAdIndex = 0;
let adRotationInterval = null;

// Configurações do sistema
USERS_FILE = 'users.json'
EMAILS_FILE = 'emails.json'
ADMIN_EMAIL = 'suport.com@gmail.oficial'

let currentFolder = 'inbox';
let currentEmail = null;
let userInfo = null;
let searchTimeout = null;
let emails_db = []; // Initialize emails_db

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
            initializeAdsSystem(); // Inicializar sistema de anúncios
            showNotification('NayEmail carregado com sucesso!', 'success');
        } else {
            // Se não há usuário logado, redirecionar
            window.location.href = '/login.html';
        }
    } catch (error) {
        console.error('Erro ao inicializar:', error);
        showNotification('Erro ao carregar NayEmail', 'error');
        // Redirecionar para login em caso de erro
        setTimeout(() => {
            window.location.href = '/login.html';
        }, 2000);
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

            // Garantir que emails_db está inicializado
            if (!emails_db || !Array.isArray(emails_db)) {
                emails_db = [];
            }

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
                showNotification('Erro no formato dos dados de email', 'error');
            }
        } else {
            console.error('Erro HTTP:', response.status);
            throw new Error(`Falha ao carregar emails: ${response.status}`);
        }
    } catch (error) {
        console.error('Erro ao carregar emails:', error);
        showEmptyState('Erro ao carregar emails. Tente novamente.');
    }
}

function displayEmails(emails) {
    const container = document.getElementById('emailsContainer');

    if (!container) {
        console.error('Container de emails não encontrado');
        return;
    }

    if (!emails || emails.length === 0) {
        showEmptyState(getEmptyMessage());
        return;
    }

    let emailsHTML = emails.map((email, index) => {
        // Inserir anúncio do Google a cada 5 emails
        let adHTML = '';
        if (index > 0 && index % 5 === 0) {
            adHTML = `
                <div class="google-ad-embedded">
                    <ins class="adsbygoogle"
                         style="display:block; width:100%; height:280px;"
                         data-ad-client="ca-pub-7407644640365147"
                         data-ad-slot="auto"
                         data-ad-format="auto"
                         data-full-width-responsive="true"></ins>
                </div>
            `;
        }

        return adHTML + getEmailHTML(email);
    }).join('');

    container.innerHTML = emailsHTML;
    
    // Carregar anúncios do Google após inserir HTML
    addGoogleAdsToEmails();

    function getEmailHTML(email) {
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
    }
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

// Sistema de Token de Conta - Verificação automática
async function checkTokenRequests() {
    if (!userInfo || !userInfo.is_admin) return;

    try {
        const response = await fetch('/api/check-token-requests', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        const result = await response.json();

        if (result.success && result.new_requests > 0) {
            showNotification(`${result.new_requests} nova(s) solicitação(ões) de token processadas`, 'success');
            loadEmails(); // Recarregar emails para mostrar as respostas
        }
    } catch (error) {
        console.error('Erro ao verificar solicitações de token:', error);
    }
}

// Verificar solicitações de token a cada 30 segundos (apenas para admin)
setInterval(() => {
    if (userInfo && userInfo.is_admin) {
        checkTokenRequests();
    }
}, 30000);

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
    }, { passive: true });

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

            // Garantir que emails_db está inicializado
            if (!emails_db || !Array.isArray(emails_db)) {
                emails_db = [];
            }

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

// Novas funcionalidades do NayEmail
let currentTheme = 'default';
let smartComposeEnabled = true;
let offlineMode = false;

// Função para adiar email
function snoozeCurrentEmail() {
    if (!currentEmail) return;
    document.getElementById('snoozeModal').classList.add('active');
}

function closeSnooze() {
    document.getElementById('snoozeModal').classList.remove('active');
}

async function snoozeEmail(duration) {
    if (!currentEmail) return;

    let snoozeDate = new Date();

    switch(duration) {
        case 'tomorrow':
            snoozeDate.setDate(snoozeDate.getDate() + 1);
            snoozeDate.setHours(8, 0, 0, 0);
            break;
        case 'week':
            snoozeDate.setDate(snoozeDate.getDate() + 7);
            snoozeDate.setHours(8, 0, 0, 0);
            break;
        case 'custom':
            const customDate = prompt('Digite a data e hora (YYYY-MM-DD HH:MM):');
            if (customDate) {
                snoozeDate = new Date(customDate);
            } else {
                return;
            }
            break;
    }

    try {
        const response = await fetch(`/api/email/${currentEmail.id}/snooze`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                snooze_until: snoozeDate.toISOString()
            })
        });

        if (response.ok) {
            showNotification('Email adiado com sucesso!', 'success');
            closeSnooze();
            backToList();
        }
    } catch (error) {
        showNotification('Erro ao adiar email', 'error');
    }
}

// Composição inteligente
function showSmartCompose() {
    document.getElementById('smartComposeModal').classList.add('active');
    loadSmartSuggestions();
}

function closeSmartCompose() {
    document.getElementById('smartComposeModal').classList.remove('active');
}

async function loadSmartSuggestions() {
    const composeBody = document.getElementById('composeBody');
    if (!composeBody) {
        console.warn('Campo de composição não encontrado');
        return;
    }

    const context = composeBody.value;

    try {
        const response = await fetch('/api/smart-compose', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ context })
        });

        if (response.ok) {
            const result = await response.json();
            if (result.suggestions && Array.isArray(result.suggestions)) {
                displaySmartSuggestions(result.suggestions);
            } else {
                displaySmartSuggestions(['Nenhuma sugestão disponível']);
            }
        } else {
            console.error('Erro HTTP ao carregar sugestões:', response.status);
            displaySmartSuggestions(['Erro ao carregar sugestões']);
        }
    } catch (error) {
        console.error('Erro ao carregar sugestões:', error);
        displaySmartSuggestions(['Erro de conexão']);
    }
}

function displaySmartSuggestions(suggestions) {
    const container = document.getElementById('smartSuggestions');
    container.innerHTML = suggestions.map(suggestion => `
        <div class="suggestion-item" onclick="applySuggestion('${suggestion}')">
            <i class="fas fa-lightbulb"></i>
            ${suggestion}
        </div>
    `).join('');
}

function applySuggestion(suggestion) {
    const bodyField = document.getElementById('composeBody');
    bodyField.value += '\n\n' + suggestion;
    closeSmartCompose();
}

// Seletor de temas
function showThemeSelector() {
    const themeSelector = document.getElementById('themeSelector');
    themeSelector.classList.toggle('active');
    loadThemes();
}

async function loadThemes() {
    try {
        const response = await fetch('/api/themes');
        if (response.ok) {
            const themes = await response.json();
            displayThemes(themes);
        }
    } catch (error) {
        console.error('Erro ao carregar temas:', error);
    }
}

function displayThemes(themes) {
    const container = document.getElementById('themeOptions');
    container.innerHTML = Object.entries(themes).map(([key, theme]) => `
        <div class="theme-option ${key === currentTheme ? 'active' : ''}" 
             onclick="selectTheme('${key}')"
             style="background: ${theme.primary_color}; color: ${theme.text_color};">
            <i class="fas fa-palette"></i>
            ${theme.name}
        </div>
    `).join('');
}

async function selectTheme(themeKey) {
    try {
        const response = await fetch('/api/user/theme', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ theme: themeKey })
        });

        if (response.ok) {
            currentTheme = themeKey;
            applyTheme(themeKey);
            showNotification('Tema aplicado!', 'success');
        }
    } catch (error) {
        showNotification('Erro ao aplicar tema', 'error');
    }
}

function applyTheme(themeKey) {
    // Aplicar tema dinamicamente
    document.body.className = `theme-${themeKey}`;
}

// Agendar envio
function showSchedule() {
    document.getElementById('scheduleModal').classList.add('active');
}

function closeSchedule() {
    document.getElementById('scheduleModal').classList.remove('active');
}

async function scheduleEmailSend() {
    const scheduleDate = document.getElementById('scheduleDate').value;

    if (!scheduleDate) {
        showNotification('Selecione uma data e hora', 'error');
        return;
    }

    const formData = {
        to: document.getElementById('composeTo').value,
        subject: document.getElementById('composeSubject').value,
        body: document.getElementById('composeBody').value,
        schedule_time: scheduleDate
    };

    try {
        const response = await fetch('/api/schedule-email', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });

        if (response.ok) {
            showNotification('Email agendado com sucesso!', 'success');
            closeSchedule();
            closeCompose();
        }
    } catch (error) {
        showNotification('Erro ao agendar email', 'error');
    }
}

// Funcionalidades extras
function markAsSpam() {
    if (!currentEmail) return;
    showNotification('Email marcado como spam', 'info');
}

function addToCalendar() {
    if (!currentEmail) return;
    showNotification('Adicionado ao calendário', 'success');
}

function printEmail() {
    if (!currentEmail) return;
    window.print();
}

function translateEmail() {
    if (!currentEmail) return;
    showNotification('Traduzindo email...', 'info');
}

function forwardEmail() {
    if (!currentEmail) return;

    document.getElementById('composeTo').value = '';
    document.getElementById('composeSubject').value = 'Fwd: ' + currentEmail.subject;
    document.getElementById('composeBody').value = `\n\n--- Mensagem encaminhada ---\nDe: ${currentEmail.from}\nPara: ${currentEmail.to}\nAssunto: ${currentEmail.subject}\n\n${currentEmail.body}`;

    showCompose();
}

function createLabel() {
    const labelName = prompt('Nome do novo label:');
    if (labelName) {
        showNotification(`Label "${labelName}" criado!`, 'success');
    }
}

function toggleOfflineMode() {
    offlineMode = !offlineMode;
    if (offlineMode) {
        showNotification('Modo offline ativado', 'info');
        document.body.classList.add('offline-mode');
    } else {
        showNotification('Modo online ativado', 'success');
        document.body.classList.remove('offline-mode');
    }
}

function openCalendar() {
    showNotification('Abrindo calendário...', 'info');
}

function openContacts() {
    showNotification('Abrindo contatos...', 'info');
}

function openTasks() {
    showNotification('Abrindo tarefas...', 'info');
}

// Criar filtro
function showFilter() {
    document.getElementById('filterModal').classList.add('active');
}

function closeFilter() {
    document.getElementById('filterModal').classList.remove('active');
}

// Atalhos de teclado expandidos
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
            case 'k':
                e.preventDefault();
                showSmartCompose();
                break;
            case 'd':
                e.preventDefault();
                if (currentEmail) deleteEmail();
                break;
            case 's':
                e.preventDefault();
                if (currentEmail) starCurrentEmail();
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

console.log('🚀 NayEmail - Sistema de Email Inteligente carregado!');
console.log('✨ Funcionalidades: IA, Temas, Filtros, Agendamento, Categorias');
console.log('⌨️ Atalhos: Ctrl+C (escrever), Ctrl+K (IA), Ctrl+R (atualizar)');
console.log('📱 Mobile: Swipe, gestos e interface otimizada');
console.log('👑 Admin: admin@nayemail.com');
console.log('🎨 Múltiplos temas e personalização completa!');
console.log('🤖 Composição e respostas inteligentes ativadas!');

// ========== FUNCIONALIDADES INOVADORAS NAYEMAIL ==========

// 1. Sistema de Email com IA Generativa
let aiEmailGenerator = {
    tones: ['profissional', 'casual', 'urgente', 'amigável', 'formal'],
    styles: ['direto', 'detalhado', 'conciso', 'persuasivo'],

    generateEmail: function(topic, tone, style, recipient) {
        // Simulação de IA generativa para emails
        const templates = {
            profissional: {
                direto: `Prezado(a) ${recipient},\n\nEscrevo para tratar sobre ${topic}.\n\nAguardo seu retorno.\n\nAtenciosamente,`,
                detalhado: `Prezado(a) ${recipient},\n\nEspero que esta mensagem o(a) encontre bem.\n\nGostaria de abordar em detalhes a questão relacionada a ${topic}. Este assunto requer nossa atenção devido à sua importância estratégica.\n\nFico à disposição para discussões adicionais.\n\nAtenciosamente,`
            },
            casual: {
                direto: `Oi ${recipient}!\n\nQueria falar sobre ${topic}.\n\nMe avisa o que acha!\n\nAbraços,`,
                detalhado: `E aí ${recipient}!\n\nTudo bem? Espero que sim!\n\nEntão, queria conversar contigo sobre ${topic}. Acho que é algo interessante que vale a pena discutirmos.\n\nQualquer coisa me chama!\n\nAbraços,`
            }
        };

        return templates[tone]?.[style] || templates.profissional.direto;
    }
};

// 2. Sistema de Análise de Sentimentos
let sentimentAnalyzer = {
    analyze: function(text) {
        const positiveWords = ['obrigado', 'excelente', 'ótimo', 'perfeito', 'sucesso', 'parabéns'];
        const negativeWords = ['problema', 'erro', 'falha', 'ruim', 'insatisfeito', 'urgente'];
        const neutralWords = ['informação', 'dados', 'reunião', 'projeto', 'relatório'];

        let score = 0;
        const words = text.toLowerCase().split(' ');

        words.forEach(word => {
            if (positiveWords.includes(word)) score += 1;
            if (negativeWords.includes(word)) score -= 1;
        });

        if (score > 0) return { sentiment: 'positivo', score, icon: '😊', color: '#4caf50' };
        if (score < 0) return { sentiment: 'negativo', score, icon: '😟', color: '#f44336' };
        return { sentiment: 'neutro', score, icon: '😐', color: '#757575' };
    }
};

// 3. Sistema de Priorização Inteligente
let intelligentPriority = {
    calculatePriority: function(email) {
        let priority = 0;
        const subject = email.subject?.toLowerCase() || '';
        const body = email.body?.toLowerCase() || '';

        // Palavras de alta prioridade
        const urgentWords = ['urgente', 'emergency', 'asap', 'importante', 'critical'];
        const businessWords = ['contrato', 'proposta', 'cliente', 'vendas', 'deadline'];

        urgentWords.forEach(word => {
            if (subject.includes(word) || body.includes(word)) priority += 3;
        });

        businessWords.forEach(word => {
            if (subject.includes(word) || body.includes(word)) priority += 2;
        });

        // Remetentes VIP
        const vipDomains = ['ceo', 'diretor', 'manager', 'admin'];
        if (vipDomains.some(domain => email.from?.includes(domain))) priority += 2;

        return Math.min(priority, 10); // Máximo 10
    },

    getPriorityBadge: function(priority) {
        if (priority >= 7) return { level: 'crítica', color: '#f44336', icon: '🚨' };
        if (priority >= 5) return { level: 'alta', color: '#ff9800', icon: '⚡' };
        if (priority >= 3) return { level: 'média', color: '#2196f3', icon: '📋' };
        return { level: 'baixa', color: '#4caf50', icon: '📄' };
    }
};

// 4. Sistema de Templates Inteligentes
let smartTemplates = {
    templates: {
        'reuniao': {
            subject: 'Agendamento de Reunião - [TÓPICO]',
            body: 'Olá [NOME],\n\nGostaria de agendar uma reunião para discutir [TÓPICO].\n\nSugestões de horário:\n• [DATA1] às [HORA1]\n• [DATA2] às [HORA2]\n\nConfirme sua disponibilidade.\n\nAtenciosamente,'
        },
        'followup': {
            subject: 'Follow-up: [ASSUNTO_ORIGINAL]',
            body: 'Olá [NOME],\n\nRetomando nossa conversa sobre [ASSUNTO_ORIGINAL].\n\nGostaria de saber se há atualizações ou se precisa de mais informações.\n\nFico no aguardo.\n\nAtenciosamente,'
        },
        'proposta': {
            subject: 'Proposta Comercial - [EMPRESA/PROJETO]',
            body: 'Prezado(a) [NOME],\n\nConforme solicitado, segue nossa proposta para [PROJETO].\n\nBenefícios principais:\n• [BENEFICIO1]\n• [BENEFICIO2]\n• [BENEFICIO3]\n\nEstou à disposição para esclarecimentos.\n\nAtenciosamente,'
        }
    },

    getTemplate: function(type, variables = {}) {
        const template = this.templates[type];
        if (!template) return null;

        let subject = template.subject;
        let body = template.body;

        // Substituir variáveis
        Object.keys(variables).forEach(key => {
            const placeholder = `[${key.toUpperCase()}]`;
            subject = subject.replace(new RegExp(placeholder, 'g'), variables[key]);
            body = body.replace(new RegExp(placeholder, 'g'), variables[key]);
        });

        return { subject, body };
    }
};

// 5. Sistema de Colaboração em Tempo Real
let realTimeCollaboration = {
    activeUsers: new Map(),

    showTypingIndicator: function(userId, emailId) {
        const indicator = document.createElement('div');
        indicator.className = 'typing-indicator';
        indicator.innerHTML = `
            <div class="typing-dots">
                <i class="fas fa-user"></i>
                <span>Usuário ${userId} está digitando...</span>
                <div class="dots">
                    <span></span><span></span><span></span>
                </div>
            </div>
        `;

        document.body.appendChild(indicator);

        setTimeout(() => {
            indicator.remove();
        }, 3000);
    },

    shareEmail: function(emailId, users) {
        showNotification(`Email compartilhado com ${users.length} usuários`, 'success');
    }
};

// 6. Sistema de Backup e Sync Multi-Dispositivo
let cloudSync = {
    syncData: function() {
        const syncData = {
            emails: emails_db || [],
            settings: userInfo || {},
            filters: [],
            labels: [],
            timestamp: new Date().toISOString()
        };

        localStorage.setItem('nayemail_backup', JSON.stringify(syncData));
        showNotification('Dados sincronizados com a nuvem', 'success');
    },

    restoreData: function() {
        const backup = localStorage.getItem('nayemail_backup');
        if (backup) {
            showNotification('Dados restaurados com sucesso', 'success');
            return JSON.parse(backup);
        }
        return null;
    }
};

// 7. Sistema de Analytics Avançado
let emailAnalytics = {
    getStats: function() {
        const stats = {
            totalEmails: emails_db?.length || 0,
            readRate: 0,
            responseTime: '2h média',
            topSenders: [],
            busyHours: [],
            sentiment: { positive: 60, neutral: 30, negative: 10 }
        };

        return stats;
    },

    generateReport: function() {
        const stats = this.getStats();
        return `
📊 RELATÓRIO DE EMAIL ANALYTICS

📈 Estatísticas Gerais:
• Total de emails: ${stats.totalEmails}
• Taxa de leitura: ${stats.readRate}%
• Tempo médio de resposta: ${stats.responseTime}

😊 Análise de Sentimentos:
• Positivos: ${stats.sentiment.positive}%
• Neutros: ${stats.sentiment.neutral}%
• Negativos: ${stats.sentiment.negative}%

⏰ Horários de pico: 9h-11h, 14h-16h

🎯 Sugestões de melhoria:
• Responder emails em até 1h
• Usar templates para agilizar
• Configurar filtros automáticos
        `;
    }
};

// 8. Sistema de Automação Avançada
let emailAutomation = {
    rules: [],

    createRule: function(name, conditions, actions) {
        const rule = {
            id: Date.now(),
            name,
            conditions,
            actions,
            active: true,
            created: new Date().toISOString()
        };

        this.rules.push(rule);
        return rule;
    },

    processEmail: function(email) {
        this.rules.forEach(rule => {
            if (rule.active && this.matchesConditions(email, rule.conditions)) {
                this.executeActions(email, rule.actions);
            }
        });
    },

    matchesConditions: function(email, conditions) {
        return conditions.every(condition => {
            switch(condition.type) {
                case 'from':
                    return email.from?.includes(condition.value);
                case 'subject':
                    return email.subject?.toLowerCase().includes(condition.value.toLowerCase());
                case 'body':
                    return email.body?.toLowerCase().includes(condition.value.toLowerCase());
                default:
                    return false;
            }
        });
    },

    executeActions: function(email, actions) {
        actions.forEach(action => {
            switch(action.type) {
                case 'star':
                    email.starred = true;
                    break;
                case 'label':
                    email.labels = email.labels || [];
                    email.labels.push(action.value);
                    break;
                case 'forward':
                    this.forwardEmail(email, action.value);
                    break;
            }
        });
    }
};

console.log('🚀 INOVAÇÕES NAYEMAIL CARREGADAS:');
console.log('🤖 IA Generativa para emails');
console.log('😊 Análise de sentimentos');
console.log('⚡ Priorização inteligente');
console.log('📝 Templates inteligentes');
console.log('👥 Colaboração em tempo real');
console.log('☁️ Sync multi-dispositivo');
console.log('📊 Analytics avançado');
console.log('🔄 Automação completa');

// ========== FUNÇÕES PARA INTERFACE DAS INOVAÇÕES ==========

function showAIGenerator() {
    document.getElementById('aiGeneratorModal').classList.add('active');
    document.getElementById('aiRecipient').focus();
}

function closeAIGenerator() {
    document.getElementById('aiGeneratorModal').classList.remove('active');
    document.getElementById('aiGeneratedContent').style.display = 'none';
}

function generateAIEmail() {
    const recipient = document.getElementById('aiRecipient').value;
    const topic = document.getElementById('aiTopic').value;
    const tone = document.getElementById('aiTone').value;
    const style = document.getElementById('aiStyle').value;

    if (!recipient || !topic) {
        showNotification('Preencha o destinatário e o tópico', 'error');
        return;
    }

    const generatedEmail = aiEmailGenerator.generateEmail(topic, tone, style, recipient);

    document.getElementById('aiEmailResult').value = generatedEmail;
    document.getElementById('aiGeneratedContent').style.display = 'block';

    showNotification('Email gerado com IA!', 'success');
}

function useGeneratedEmail() {
    const generatedText = document.getElementById('aiEmailResult').value;

    // Preencher formulário de composição
    document.getElementById('composeBody').value = generatedText;
    document.getElementById('composeTo').value = document.getElementById('aiRecipient').value;

    closeAIGenerator();
    showCompose();

    showNotification('Email transferido para composição!', 'success');
}

function showAnalytics() {
    document.getElementById('analyticsModal').classList.add('active');
    loadAnalyticsData();
}

function closeAnalytics() {
    document.getElementById('analyticsModal').classList.remove('active');
}

function loadAnalyticsData() {
    const stats = emailAnalytics.getStats();
    const report = emailAnalytics.generateReport();

    document.getElementById('analyticsContent').innerHTML = `
        <div class="analytics-grid">
            <div class="analytics-card">
                <div class="analytics-number">${stats.totalEmails}</div>
                <div class="analytics-label">Total de Emails</div>
            </div>
            <div class="analytics-card">
                <div class="analytics-number">${stats.readRate}%</div>
                <div class="analytics-label">Taxa de Leitura</div>
            </div>
            <div class="analytics-card">
                <div class="analytics-number">${stats.responseTime}</div>
                <div class="analytics-label">Tempo de Resposta</div>
            </div>
            <div class="analytics-card">
                <div class="analytics-number">98%</div>
                <div class="analytics-label">Uptime</div>
            </div>
        </div>

        <div class="analytics-chart">
            <h4>📊 Relatório Detalhado</h4>
            <pre style="white-space: pre-wrap; font-family: monospace; background: #f5f5f5; padding: 15px; border-radius: 8px; overflow-x: auto;">${report}</pre>
        </div>

        <div style="margin-top: 20px;">
            <button onclick="exportAnalytics()" class="send-btn">
                <i class="fas fa-download"></i>
                Exportar Relatório
            </button>
            <button onclick="scheduleReport()" class="send-btn" style="margin-left: 10px;">
                <i class="fas fa-clock"></i>
                Agendar Relatório
            </button>
        </div>
    `;
}

function exportAnalytics() {
    const report = emailAnalytics.generateReport();
    const blob = new Blob([report], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `nayemail-analytics-${new Date().toISOString().split('T')[0]}.txt`;
    a.click();
    URL.revokeObjectURL(url);

    showNotification('Relatório exportado!', 'success');
}

function scheduleReport() {
    showNotification('Relatório agendado para envio semanal!', 'success');
}

function showTemplates() {
    document.getElementById('templatesModal').classList.add('active');
}

function closeTemplates() {
    document.getElementById('templatesModal').classList.remove('active');
}

function useTemplate(templateType) {
    let variables = {};

    // Coletar variáveis do usuário
    if (templateType === 'reuniao') {
        const topic = prompt('Qual o tópico da reunião?') || '[TÓPICO]';
        const name = prompt('Nome do destinatário?') || '[NOME]';
        variables = { 
            nome: name,
            topico: topic,
            data1: 'Segunda-feira',
            hora1: '14:00',
            data2: 'Terça-feira',
            hora2: '10:00'
        };
    } else if (templateType === 'followup') {
        const name = prompt('Nome do destinatário?') || '[NOME]';
        const subject = prompt('Assunto original?') || '[ASSUNTO]';
        variables = { nome: name, assunto_original: subject };
    } else if (templateType === 'proposta') {
        const name = prompt('Nome do destinatário?') || '[NOME]';
        const project = prompt('Nome do projeto/empresa?') || '[PROJETO]';
        variables = { 
            nome: name, 
            projeto: project,
            beneficio1: 'Redução de custos em 30%',
            beneficio2: 'Aumento da produtividade',
            beneficio3: 'Suporte técnico especializado'
        };
    }

    const template = smartTemplates.getTemplate(templateType, variables);

    if (template) {
        document.getElementById('composeSubject').value = template.subject;
        document.getElementById('composeBody').value = template.body;

        closeTemplates();
        showCompose();

        showNotification(`Template "${templateType}" aplicado!`, 'success');
    } else {
        showNotification('Template não encontrado', 'error');
    }
}

function showAutomation() {
    document.getElementById('automationModal').classList.add('active');
    loadAutomationRules();
}

function closeAutomation() {
    document.getElementById('automationModal').classList.remove('active');
}

function loadAutomationRules() {
    const rulesContainer = document.getElementById('automationRules');

    if (emailAutomation.rules.length === 0) {
        rulesContainer.innerHTML = `
            <div style="text-align: center; padding: 40px; color: #666;">
                <i class="fas fa-cogs" style="font-size: 3em; margin-bottom: 16px; opacity: 0.5;"></i>
                <h3>Nenhuma regra criada</h3>
                <p>Crie sua primeira regra de automação para agilizar seu fluxo de emails.</p>
            </div>
        `;
        return;
    }

    rulesContainer.innerHTML = emailAutomation.rules.map(rule => `
        <div class="automation-rule">
            <div class="rule-header">
                <span class="rule-name">${rule.name}</span>
                <button class="rule-toggle ${rule.active ? '' : 'inactive'}" 
                        onclick="toggleRule('${rule.id}')">
                    ${rule.active ? 'Ativo' : 'Inativo'}
                </button>
            </div>
            <div class="rule-description">
                ${rule.conditions.map(c => `${c.type}: ${c.value}`).join(', ')} →
                ${rule.actions.map(a => a.type).join(', ')}
            </div>
            <div class="rule-stats">
                <span>Criado: ${new Date(rule.created).toLocaleDateString()}</span>
                <span>Processados: 0 emails</span>
            </div>
        </div>
    `).join('');
}

function createAutomationRule() {
    const name = prompt('Nome da regra:');
    if (!name) return;

    const conditionType = prompt('Condição (from/subject/body):') || 'subject';
    const conditionValue = prompt('Valor da condição:');
    if (!conditionValue) return;

    const actionType = prompt('Ação (star/label/forward):') || 'star';
    const actionValue = actionType === 'label' ? prompt('Nome do label:') : '';

    const rule = emailAutomation.createRule(
        name,
        [{ type: conditionType, value: conditionValue }],
        [{ type: actionType, value: actionValue }]
    );

    showNotification(`Regra "${name}" criada!`, 'success');
    loadAutomationRules();
}

function toggleRule(ruleId) {
    const rule = emailAutomation.rules.find(r => r.id == ruleId);
    if (rule) {
        rule.active = !rule.active;
        loadAutomationRules();
        showNotification(`Regra ${rule.active ? 'ativada' : 'desativada'}`, 'info');
    }
}

function showCollaboration() {
    document.getElementById('collaborationModal').classList.add('active');
}

function closeCollaboration() {
    document.getElementById('collaborationModal').classList.remove('active');
}

// Função para adicionar análise de sentimentos aos emails
function addSentimentToEmail(email) {
    const sentiment = sentimentAnalyzer.analyze(email.body || '');
    const sentimentBadge = `
        <div class="sentiment-indicator sentiment-${sentiment.sentiment}">
            ${sentiment.icon} ${sentiment.sentiment.toUpperCase()}
        </div>
    `;
    return sentimentBadge;
}

// Função para adicionar prioridade aos emails
function addPriorityToEmail(email) {
    const priority = intelligentPriority.calculatePriority(email);
    const priorityBadge = intelligentPriority.getPriorityBadge(priority);

    return `
        <div class="priority-badge priority-${priorityBadge.level}">
            ${priorityBadge.icon} ${priorityBadge.level.toUpperCase()}
        </div>
    `;
}

// Função para demonstrar colaboração em tempo real
function demonstrateCollaboration() {
    realTimeCollaboration.showTypingIndicator('João', 'email_123');
    setTimeout(() => {
        showNotification('João comentou no email', 'info');
    }, 3000);
}

// Auto-executar demonstração de funcionalidades
setTimeout(() => {
    if (userInfo) {
        console.log('🎯 Demonstrando funcionalidades inovadoras...');

        // Simular análise de sentimentos
        setTimeout(() => {
            showNotification('✨ IA analisou sentimentos dos emails', 'success');
        }, 2000);

        // Simular sync automático
        setTimeout(() => {
            cloudSync.syncData();
        }, 5000);

        // Demonstrar colaboração
        setTimeout(() => {
            demonstrateCollaboration();
        }, 8000);
    }
}, 3000);

// Sistema de IA Conversacional
let aiChatWindow = null;
let currentChatId = null;
let chatHistory = [];

// Carregar Google AdSense
function loadGoogleAds() {
    // Verificar se já foi carregado
    if (document.querySelector('script[src*="googlesyndication.com"]')) {
        return;
    }

    const script = document.createElement('script');
    script.async = true;
    script.src = 'https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-7407644640365147';
    script.crossOrigin = 'anonymous';
    document.head.appendChild(script);

    // Aguardar carregamento e inicializar anúncios
    script.onload = function() {
        initializeGoogleAds();
    };
}

// Inicializar anúncios do Google
function initializeGoogleAds() {
    // Criar anúncios em locais estratégicos
    createGoogleAdUnit('google-ad-sidebar', 'sidebar');
    createGoogleAdUnit('google-ad-header', 'header');
    createGoogleAdUnit('google-ad-embedded', 'embedded');
}

// Criar unidade de anúncio do Google
function createGoogleAdUnit(id, type) {
    let container, adSize, adSlot;

    switch(type) {
        case 'sidebar':
            container = document.querySelector('.sidebar');
            adSize = 'width: 300px; height: 250px;';
            adSlot = 'ca-pub-7407644640365147';
            break;
        case 'header':
            container = document.querySelector('.gmail-header');
            adSize = 'width: 728px; height: 90px;';
            adSlot = 'ca-pub-7407644640365147';
            break;
        case 'embedded':
            container = document.getElementById('emailsContainer');
            adSize = 'width: 100%; height: 280px;';
            adSlot = 'ca-pub-7407644640365147';
            break;
    }

    if (!container) return;

    const adUnit = document.createElement('div');
    adUnit.className = `google-ad-unit google-ad-${type}`;
    adUnit.innerHTML = `
        <ins class="adsbygoogle"
             style="display:block; ${adSize}"
             data-ad-client="ca-pub-7407644640365147"
             data-ad-slot="${adSlot}"
             data-ad-format="auto"
             data-full-width-responsive="true"></ins>
    `;

    if (type === 'sidebar') {
        container.appendChild(adUnit);
    } else if (type === 'header') {
        container.appendChild(adUnit);
    } else if (type === 'embedded') {
        // Inserir a cada 5 emails
        const emailItems = container.querySelectorAll('.email-item');
        if (emailItems.length >= 3) {
            emailItems[2].insertAdjacentElement('afterend', adUnit);
        }
    }

    // Carregar anúncio
    try {
        (window.adsbygoogle = window.adsbygoogle || []).push({});
    } catch (e) {
        console.log('Erro ao carregar anúncio:', e);
    }
}

// Mostrar banner da IA
function showAIBanner() {
    const banner = document.createElement('div');
    banner.className = 'ai-banner';
    banner.innerHTML = `
        <div class="ai-banner-content">
            <div class="ai-banner-left">
                <div class="ai-avatar">
                    <i class="fas fa-robot"></i>
                </div>
                <div class="ai-info">
                    <h3>🤖 NayAI - Assistente Inteligente</h3>
                    <p>Converse com nossa IA avançada! Tire dúvidas, peça ajuda ou apenas bate-papo.</p>
                </div>
            </div>
            <div class="ai-banner-actions">
                <button onclick="startAIChat()" class="ai-chat-btn">
                    <i class="fas fa-comments"></i>
                    Conversar com IA
                </button>
                <button onclick="closeAIBanner()" class="ai-close-btn">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        </div>
    `;

    document.body.appendChild(banner);

    // Animar entrada
    setTimeout(() => {
        banner.classList.add('show');
    }, 100);
}

function closeAIBanner() {
    const banner = document.querySelector('.ai-banner');
    if (banner) {
        banner.classList.remove('show');
        setTimeout(() => banner.remove(), 300);
    }
}

async function startAIChat() {
    closeAIBanner();

    try {
        // Gerar ID único da conversa
        currentChatId = generateChatId();
        chatHistory = [];

        // Abrir janela de chat
        openAIChatWindow();

        // Enviar email de início para IA
        await sendEmailToAI('Usuário iniciou conversa com IA', `Usuário ${userInfo.name} (${userInfo.email}) iniciou uma nova conversa com a IA.\nID da Conversa: ${currentChatId}`);

        // Mensagem de boas-vindas
        addAIMessage('Olá! 👋 Eu sou a NayAI, sua assistente inteligente. Como posso ajudar você hoje?');

    } catch (error) {
        console.error('Erro ao iniciar chat com IA:', error);
        showNotification('Erro ao conectar com a IA', 'error');
    }
}

function generateChatId() {
    return 'chat_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
}

function openAIChatWindow() {
    if (aiChatWindow && !aiChatWindow.closed) {
        aiChatWindow.focus();
        return;
    }

    const chatUrl = `/ai-chat?chat_id=${currentChatId}`;
    aiChatWindow = window.open(chatUrl, 'AIChat', 'width=500,height=700,scrollbars=yes,resizable=yes');

    // Verificar se o usuário fechou a janela
    const checkClosed = setInterval(() => {
        if (aiChatWindow.closed) {
            clearInterval(checkClosed);
            finalizeChatSession();
        }
    }, 1000);
}

async function finalizeChatSession() {
    if (chatHistory.length > 0) {
        try {
            // Salvar conversa e enviar por email
            await sendChatSummaryToUser();
            showNotification('Conversa salva e enviada por email!', 'success');
        } catch (error) {
            console.error('Erro ao finalizar chat:', error);
        }
    }

    currentChatId = null;
    chatHistory = [];
}

async function sendEmailToAI(subject, message) {
    try {
        const response = await fetch('/api/send-email', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                to: 'IA@nayemail.com',
                subject: subject,
                body: message
            })
        });

        return await response.json();
    } catch (error) {
        console.error('Erro ao enviar email para IA:', error);
    }
}

async function sendChatSummaryToUser() {
    const chatSummary = formatChatHistory();

    const emailBody = `
🤖 Resumo da sua conversa com NayAI

📅 Data: ${new Date().toLocaleString('pt-BR')}
🆔 ID da Conversa: ${currentChatId}
💬 Total de mensagens: ${chatHistory.length}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

${chatSummary}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✨ Obrigado por usar a NayAI!
Esperamos que a conversa tenha sido útil.

📧 Este email foi gerado automaticamente pelo Sistema NayEmail
    `;

    try {
        const response = await fetch('/api/send-email', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                to: userInfo.email,
                subject: `🤖 Resumo da conversa com NayAI - ${new Date().toLocaleDateString('pt-BR')}`,
                body: emailBody
            })
        });

        return await response.json();
    } catch (error) {
        console.error('Erro ao enviar resumo:', error);
    }
}

function formatChatHistory() {
    return chatHistory.map((msg, index) => {
        const time = new Date(msg.timestamp).toLocaleTimeString('pt-BR');
        const sender = msg.sender === 'user' ? '👤 Você' : '🤖 NayAI';
        return `[${time}] ${sender}: ${msg.message}`;
    }).join('\n\n');
}

function addAIMessage(message) {
    const messageObj = {
        sender: 'ai',
        message: message,
        timestamp: new Date().toISOString()
    };

    chatHistory.push(messageObj);

    // Enviar para janela de chat se estiver aberta
    if (aiChatWindow && !aiChatWindow.closed) {
        aiChatWindow.postMessage({
            type: 'ai_message',
            message: messageObj
        }, '*');
    }
}

// Mostrar banner da IA automaticamente após 3 segundos
setTimeout(() => {
    if (userInfo && !localStorage.getItem('ai_banner_dismissed')) {
        showAIBanner();
    }
}, 3000);

// --- Sistema Avançado de Anúncios ---
function initializeAdsSystem() {
    // Carregar Google AdSense
    loadGoogleAds();
    
    // Adicionar anúncios em pontos estratégicos após carregamento
    setTimeout(() => {
        addGoogleAdsToEmails();
    }, 2000);
}

function showSponsorBanner() {
    const sponsorKeys = Object.keys(SPONSORS);
    const randomSponsorKey = sponsorKeys[Math.floor(Math.random() * sponsorKeys.length)];
    const sponsor = SPONSORS[randomSponsorKey];

    if (sponsorSettings.closedBanners.includes(sponsor.name)) return;

    const banner = document.createElement('div');
    banner.className = 'sponsor-banner';
    banner.innerHTML = `
        <div class="sponsor-banner-content" style="background: linear-gradient(135deg, ${sponsor.color}, ${adjustColor(sponsor.color, 20)});">
            <div class="sponsor-banner-left">
                <img src="${sponsor.logo}" alt="${sponsor.name} Logo" class="sponsor-banner-logo">
                <div class="sponsor-banner-text">
                    <h3>${sponsor.name}</h3>
                    <p>${sponsor.tagline}</p>
                    <small>${sponsor.description}</small>
                </div>
            </div>
            <div class="sponsor-banner-actions">
                <a href="${sponsor.url}" target="_blank" class="sponsor-banner-cta">${sponsor.cta}</a>
                <button class="sponsor-banner-close" onclick="closeSponsorBanner('${sponsor.name}')">&times;</button>
            </div>
        </div>
    `;

    document.body.insertBefore(banner, document.body.firstChild);

    // Auto-remove após 10 segundos
    setTimeout(() => {
        if (banner.parentNode) {
            banner.remove();
        }
    }, 10000);
}

function showSidebarAds() {
    const sidebar = document.querySelector('.sidebar');
    if (!sidebar) return;

    const adContainer = document.createElement('div');
    adContainer.className = 'sidebar-ads';
    adContainer.innerHTML = getSidebarAdContent();

    sidebar.appendChild(adContainer);
}

function getSidebarAdContent() {
    const sponsors = Object.values(SPONSORS);
    const randomSponsor = sponsors[Math.floor(Math.random() * sponsors.length)];

    return `
        <div class="sidebar-ad-card" style="border-left: 4px solid ${randomSponsor.color};">
            <div class="sidebar-ad-header">
                <img src="${randomSponsor.logo}" alt="${randomSponsor.name}" class="sidebar-ad-logo">
                <span class="sidebar-ad-badge">Anúncio</span>
            </div>
            <div class="sidebar-ad-content">
                <h4>${randomSponsor.name}</h4>
                <p>${randomSponsor.description}</p>
                <a href="${randomSponsor.url}" target="_blank" class="sidebar-ad-btn" style="background: ${randomSponsor.color};">
                    ${randomSponsor.cta}
                </a>
            </div>
        </div>
    `;
}

function showEmbeddedAd() {
    const emailContainer = document.getElementById('emailsContainer');
    if (!emailContainer) return;

    const emailItems = emailContainer.querySelectorAll('.email-item');
    if (emailItems.length < 3) return;

    // Inserir anúncio após o 3º email
    const thirdEmail = emailItems[2];
    const adElement = createEmbeddedAd();

    thirdEmail.parentNode.insertBefore(adElement, thirdEmail.nextSibling);
}

function createEmbeddedAd() {
    const sponsors = Object.values(SPONSORS);
    const randomSponsor = sponsors[Math.floor(Math.random() * sponsors.length)];

    const adElement = document.createElement('div');
    adElement.className = 'embedded-ad';
    adElement.innerHTML = `
        <div class="embedded-ad-content" style="background: linear-gradient(135deg, ${randomSponsor.color}15, ${randomSponsor.color}05);">
            <div class="embedded-ad-label">Patrocinado</div>
            <div class="embedded-ad-body">
                <img src="${randomSponsor.logo}" alt="${randomSponsor.name}" class="embedded-ad-logo">
                <div class="embedded-ad-text">
                    <h4>${randomSponsor.name}</h4>
                    <p>${randomSponsor.tagline}</p>
                    <span class="embedded-ad-description">${randomSponsor.description}</span>
                </div>
                <a href="${randomSponsor.url}" target="_blank" class="embedded-ad-cta" style="background: ${randomSponsor.color};">
                    ${randomSponsor.cta}
                </a>
            </div>
        </div>
    `;

    return adElement;
}

function startAdRotation() {
    if (adRotationInterval) {
        clearInterval(adRotationInterval);
    }

    adRotationInterval = setInterval(() => {
        rotateAds();
    }, 30000); // Rotacionar a cada 30 segundos
}

function rotateAds() {
    const sidebarAd = document.querySelector('.sidebar-ads');
    if (sidebarAd) {
        sidebarAd.innerHTML = getSidebarAdContent();
    }

    // Adicionar efeito de transição
    if (sidebarAd) {
        sidebarAd.style.opacity = '0';
        setTimeout(() => {
            sidebarAd.innerHTML = getSidebarAdContent();
            sidebarAd.style.opacity = '1';
        }, 300);
    }
}

function showRandomAd() {
    const adTypes = ['banner', 'notification', 'popup'];
    const randomType = adTypes[Math.floor(Math.random() * adTypes.length)];

    switch(randomType) {
        case 'banner':
            showSponsorBanner();
            break;
        case 'notification':
            showAdNotification();
            break;
        case 'popup':
            showAdPopup();
            break;
    }
}

function showAdNotification() {
    const sponsors = Object.values(SPONSORS);
    const randomSponsor = sponsors[Math.floor(Math.random() * sponsors.length)];

    showNotification(`🎯 ${randomSponsor.name}: ${randomSponsor.tagline}`, 'info');
}

function showAdPopup() {
    const sponsors = Object.values(SPONSORS);
    const randomSponsor = sponsors[Math.floor(Math.random() * sponsors.length)];

    const popup = document.createElement('div');
    popup.className = 'ad-popup';
    popup.innerHTML = `
        <div class="ad-popup-content" style="border-top: 4px solid ${randomSponsor.color};">
            <button class="ad-popup-close" onclick="this.parentElement.parentElement.remove()">&times;</button>
            <img src="${randomSponsor.logo}" alt="${randomSponsor.name}" class="ad-popup-logo">
            <h3>${randomSponsor.name}</h3>
            <p>${randomSponsor.description}</p>
            <a href="${randomSponsor.url}" target="_blank" class="ad-popup-btn" style="background: ${randomSponsor.color};">
                ${randomSponsor.cta}
            </a>
        </div>
    `;

    document.body.appendChild(popup);

    // Auto-remove após 8 segundos
    setTimeout(() => {
        if (popup.parentNode) {
            popup.remove();
        }
    }, 8000);
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

function adjustColor(color, amount) {
    return '#' + color.replace(/^#/, '').replace(/../g, color => ('0'+Math.min(255, Math.max(0, parseInt(color, 16) + amount)).toString(16)).substr(-2));
}

// Improved error handling in AI chat, including specific messages for connection and session issues.

// 9. NayAI - Sistema de IA Conversacional
// Replacing the original function with the improved version
function generateNayAIResponse(user_message, should_close = false) {
    const message_lower = user_message.toLowerCase();

    // Detectar solicitação de atendimento humano
    if (message_lower.includes('atendente') || message_lower.includes('suporte') || 
        message_lower.includes('humano') || message_lower.includes('pessoa') ||
        message_lower.includes('falar com alguem') || message_lower.includes('ajuda humana')) {
        return "🔄 Entendido! Vou conectar você com um atendente humano. Aguarde um momento enquanto transfiro sua conversa...";
    }

    // Detectar comando para fechar chat
    if (should_close || ['fechar', 'finalizar', 'encerrar', 'sair', 'terminar', 'acabar', 'fim', 'tchau', 'bye'].some(word => message_lower.includes(word))) {
        return "🔄 Entendido! Finalizando nossa conversa e enviando relatório completo por email. Obrigada por usar a NayAI! 👋";
    }

    // Problemas com API ou sistema
    if (message_lower.includes('api') && (message_lower.includes('bug') || message_lower.includes('erro') || message_lower.includes('problema'))) {
        return "🔧 Detectei um problema com a API! Vou encaminhar isso para nossa equipe técnica.\n\n📋 Detalhes que posso verificar:\n• Status da API: Operacional\n• Última atualização: Hoje\n• Endpoints disponíveis: /api/emails, /api/send-email, /api/user-info\n\nPrecisa de ajuda específica com algum endpoint ou quer falar com um atendente?";
    }

    // Recuperação de emails
    if ((message_lower.includes('recuperar') || message_lower.includes('devolução') || message_lower.includes('restore')) && message_lower.includes('email')) {
        return "🔄 Para recuperar emails deletados:\n\n📧 **Processo de Recuperação:**\n• Emails deletados ficam 30 dias na lixeira\n• Acesse: Configurações > Lixeira\n• Selecione os emails e clique 'Restaurar'\n\n⚠️ **Importante:**\n• Após 30 dias, emails são deletados permanentemente\n• Backups automáticos são feitos diariamente\n\n🔧 Precisa de ajuda técnica específica? Posso conectar com um atendente!";
    }

    // Envio de emails
    if (message_lower.includes('enviar') && message_lower.includes('email')) {
        return "📨 **Como enviar emails no NayEmail:**\n\n✨ **Método Rápido:**\n• Clique no botão 'Escrever' (azul)\n• Preencha destinatário, assunto e mensagem\n• Clique 'Enviar'\n\n🎯 **Recursos Avançados:**\n• Agendar envio: botão do relógio\n• Templates inteligentes: botão da lâmpada\n• Composição com IA: Ctrl+K\n\n📋 **Dicas:**\n• Use ; para separar múltiplos emails\n• Salve rascunhos automaticamente\n• Verificação ortográfica ativa\n\nPrecisa de ajuda com algo específico?";
    }

    // Funcionalidades do sistema
    if (['sistema', 'nayemail', 'funcionalidade', 'como usar', 'help', 'ajuda'].some(word => message_lower.includes(word))) {
        return "🎯 **NayEmail - Suas principais funcionalidades:**\n\n📧 **Gestão de Emails:**\n• Caixa de entrada inteligente\n• Organização por pastas\n• Sistema de favoritos e destaques\n• Busca avançada\n\n🤖 **IA Integrada:**\n• Chat inteligente (comigo!)\n• Composição automática\n• Respostas sugeridas\n• Análise de sentimentos\n\n🛡️ **Segurança:**\n• Verificações avançadas\n• Autenticação 2FA\n• Emails criptografados\n\n⚙️ **Admin:**\n• Painel de controle\n• Broadcast para usuários\n• Logs do sistema\n\nSobre qual área quer saber mais?";
    }

    // Saudações
    if (['olá', 'oi', 'hello', 'hey', 'bom dia', 'boa tarde', 'boa noite'].some(word => message_lower.includes(word))) {
        return "Olá! 👋 Sou a **NayAI**, assistente inteligente do NayEmail!\n\n🎯 **Posso ajudar com:**\n• Dúvidas sobre o sistema\n• Problemas técnicos\n• Recuperação de emails\n• Configurações\n• Conectar com atendente humano\n\n💬 Como posso ajudar você hoje?";
    }

    // Resposta padrão mais inteligente
    return "🤖 **NayAI sempre pronta para ajudar!**\n\nAnalisei sua mensagem e posso ajudar com:\n\n📧 **Problemas com emails?** → Posso resolver\n🔧 **Questões técnicas?** → Vou diagnosticar\n👤 **Precisa de atendente?** → Digite 'atendente'\n❓ **Dúvidas gerais?** → Estou aqui!\n\n💡 **Dica:** Seja específico sobre seu problema para eu poder ajudar melhor!\n\nO que exatamente precisa resolver?";
}

//---The python code will stay the same ---
//---The python code will stay the same ---
//---The python code will stay the same ---

// Adicionar anúncios do Google aos emails
function addGoogleAdsToEmails() {
    // Carregar anúncios que foram inseridos dinamicamente
    const newAds = document.querySelectorAll('.google-ad-embedded .adsbygoogle:not([data-ad-status])');
    newAds.forEach(ad => {
        try {
            (window.adsbygoogle = window.adsbygoogle || []).push({});
        } catch (e) {
            console.log('Erro ao carregar anúncio:', e);
        }
    });
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
document.addEventListener('DOMContentLoaded', function () {
    setTimeout(startVerificationAutoRefresh, 5000); // Iniciar após 5s
});