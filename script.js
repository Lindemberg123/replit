
// Gmail System - Complete Email Management

let currentFolder = 'inbox';
let currentEmail = null;
let userInfo = null;

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

async function initializeApp() {
    try {
        await loadUserInfo();
        await loadEmails();
        setupEventListeners();
        showNotification('Gmail carregado com sucesso!', 'success');
    } catch (error) {
        console.error('Error initializing app:', error);
        showNotification('Erro ao carregar Gmail', 'error');
    }
}

function setupEventListeners() {
    // Navigation
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', function() {
            const folder = this.dataset.folder;
            if (folder) {
                switchFolder(folder);
            }
        });
    });

    // Compose form
    document.getElementById('composeForm').addEventListener('submit', handleSendEmail);
    
    // Search functionality
    document.querySelector('.search-box input').addEventListener('input', handleSearch);
}

async function loadUserInfo() {
    try {
        const response = await fetch('/api/user-info');
        if (response.ok) {
            userInfo = await response.json();
            document.getElementById('userEmail').textContent = userInfo.email;
            updateCounts();
        }
    } catch (error) {
        console.error('Error loading user info:', error);
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
        const response = await fetch(`/api/emails/${currentFolder}`);
        
        if (response.ok) {
            const emails = await response.json();
            displayEmails(emails);
        } else {
            throw new Error('Failed to load emails');
        }
    } catch (error) {
        console.error('Error loading emails:', error);
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
        <div class="email-item ${email.read ? '' : 'unread'}" onclick="openEmail(${email.id})">
            <div class="email-sender">${email.from}</div>
            <div class="email-content-preview">
                <div class="email-subject">${email.subject}</div>
                <div class="email-snippet">${email.body.substring(0, 100)}${email.body.length > 100 ? '...' : ''}</div>
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
        'drafts': 'Nenhum rascunho salvo'
    };
    return messages[currentFolder] || 'Pasta vazia';
}

function switchFolder(folder) {
    // Update active nav item
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.remove('active');
    });
    document.querySelector(`.nav-item[data-folder="${folder}"]`).classList.add('active');
    
    // Update folder title
    const titles = {
        'inbox': 'Caixa de entrada',
        'sent': 'Enviados',
        'drafts': 'Rascunhos'
    };
    document.getElementById('folderTitle').textContent = titles[folder];
    
    // Load emails for the folder
    currentFolder = folder;
    loadEmails();
    
    // Show email list if viewing email
    backToList();
}

async function openEmail(emailId) {
    try {
        const response = await fetch(`/api/email/${emailId}`);
        if (response.ok) {
            const email = await response.json();
            currentEmail = email;
            showEmailView(email);
        }
    } catch (error) {
        console.error('Error loading email:', error);
        showNotification('Erro ao carregar email', 'error');
    }
}

function showEmailView(email) {
    document.getElementById('emailList').style.display = 'none';
    document.getElementById('emailView').style.display = 'flex';
    
    document.getElementById('emailContent').innerHTML = `
        <div class="email-header">
            <h1 class="email-title">${email.subject}</h1>
            <div class="email-meta">
                <div><strong>De:</strong> ${email.from}</div>
                <div><strong>Para:</strong> ${email.to}</div>
                <div><strong>Data:</strong> ${formatDate(email.date)}</div>
            </div>
        </div>
        <div class="email-body">${email.body}</div>
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
            
            // Reload emails if viewing sent folder
            if (currentFolder === 'sent') {
                loadEmails();
            }
            
            // Update user info
            loadUserInfo();
        } else {
            showNotification(`Erro: ${result.error}`, 'error');
        }
    } catch (error) {
        showNotification('Erro de conexão', 'error');
        console.error('Error:', error);
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
            
            // Reload emails if viewing drafts folder
            if (currentFolder === 'drafts') {
                loadEmails();
            }
            
            // Update user info
            loadUserInfo();
        } else {
            showNotification('Erro ao salvar rascunho', 'error');
        }
    } catch (error) {
        showNotification('Erro de conexão', 'error');
        console.error('Error:', error);
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
            console.error('Error:', error);
        }
    }
}

async function refreshEmails() {
    try {
        const response = await fetch('/api/refresh-emails', {
            method: 'POST'
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showNotification(`${result.count} emails atualizados`, 'success');
            loadEmails();
            loadUserInfo();
        } else {
            showNotification('Erro ao atualizar emails', 'error');
        }
    } catch (error) {
        showNotification('Erro de conexão', 'error');
        console.error('Error:', error);
    }
}

function handleSearch(e) {
    const searchTerm = e.target.value.toLowerCase();
    const emailItems = document.querySelectorAll('.email-item');
    
    emailItems.forEach(item => {
        const sender = item.querySelector('.email-sender').textContent.toLowerCase();
        const subject = item.querySelector('.email-subject').textContent.toLowerCase();
        const snippet = item.querySelector('.email-snippet').textContent.toLowerCase();
        
        if (sender.includes(searchTerm) || subject.includes(searchTerm) || snippet.includes(searchTerm)) {
            item.style.display = 'flex';
        } else {
            item.style.display = 'none';
        }
    });
}

function formatDate(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const diffTime = Math.abs(now - date);
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    
    if (diffDays === 1) {
        return 'Hoje';
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
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.remove();
    }, 3000);
}

// Keyboard shortcuts
document.addEventListener('keydown', function(e) {
    if (e.key === 'c' && (e.ctrlKey || e.metaKey)) {
        e.preventDefault();
        showCompose();
    } else if (e.key === 'Escape') {
        if (document.getElementById('composeModal').classList.contains('active')) {
            closeCompose();
        } else if (currentEmail) {
            backToList();
        }
    }
});

console.log('Gmail System carregado com sucesso!');
console.log('Atalhos: Ctrl+C para escrever, Esc para voltar');
