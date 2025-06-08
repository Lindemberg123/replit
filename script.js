
// Sistema Gmail Independente - JavaScript Frontend

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
            displayEmails(emails);
        } else {
            throw new Error('Falha ao carregar emails');
        }
    } catch (error) {
        console.error('Erro ao carregar emails:', error);
        showEmptyState('Erro ao carregar emails');
    }
}

function displayEmails(emails) {
    const container = document.getElementById('emailsContainer');
    
    if (emails.length === 0) {
        showEmptyState(getEmptyMessage());
        return;
    }
    
    container.innerHTML = emails.map(email => `
        <div class="email-item ${email.read ? '' : 'unread'} ${email.highlighted ? 'highlighted' : ''}" onclick="openEmail('${email.id}')">
            <div class="email-checkbox">
                <input type="checkbox" onchange="toggleEmailSelection('${email.id}')">
            </div>
            <div class="email-star ${email.starred ? 'starred' : ''}" onclick="toggleStar('${email.id}', event)">
                <i class="fas fa-star"></i>
            </div>
            ${email.highlighted ? '<div class="email-highlight"><i class="fas fa-star-of-life"></i></div>' : ''}
            <div class="email-sender">${email.from || 'Sem remetente'}</div>
            <div class="email-content-preview">
                <div class="email-subject">${email.subject || 'Sem assunto'}</div>
                <div class="email-snippet">${(email.body || '').substring(0, 100)}${(email.body || '').length > 100 ? '...' : ''}</div>
            </div>
            <div class="email-date">${formatDate(email.date)}</div>
        </div>
    `).join('');
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
    loadEmails();
    
    // Voltar para lista
    backToList();
}

async function openEmail(emailId) {
    try {
        const response = await fetch(`/api/email/${emailId}`);
        if (response.ok) {
            const email = await response.json();
            currentEmail = email;
            showEmailView(email);
            
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
    
    document.getElementById('emailContent').innerHTML = `
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
                ${email.highlighted ? '<div class="email-highlighted-badge"><i class="fas fa-star-of-life"></i> Email em Destaque</div>' : ''}
            </div>
        </div>
        <div class="email-body">${(email.body || '').replace(/\n/g, '<br>')}</div>
    `;
}

function backToList() {
    document.getElementById('emailList').style.display = 'flex';
    document.getElementById('emailView').style.display = 'none';
    currentEmail = null;
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
    showEmailView(email);
    
    // Adicionar comportamento mobile
    if (window.innerWidth <= 768) {
        const emailView = document.getElementById('emailView');
        if (emailView) {
            emailView.classList.add('active');
            emailView.scrollTop = 0;
        }
    }
}

// Função mobile para voltar à lista
function backToListMobile() {
    if (window.innerWidth <= 768) {
        const emailView = document.getElementById('emailView');
        if (emailView) {
            emailView.classList.remove('active');
        }
        
        setTimeout(() => {
            backToList();
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
                document.querySelectorAll('.admin-item, .admin-only').forEach(el => {
                    el.style.display = el.tagName === 'BUTTON' ? 'inline-block' : 'flex';
                });
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

console.log('Sistema Gmail Independente carregado!');
console.log('Atalhos: Ctrl+C para escrever, Ctrl+R para atualizar, Esc para voltar');
console.log('Mobile: Swipe direita para voltar, toque no menu para navegação');
console.log('Admin: suport.com@gmail.oficial');
