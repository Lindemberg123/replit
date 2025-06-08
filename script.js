
// Gmail API Pro - Frontend Functionality

// API Base URL
const API_BASE = '';

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    loadEmails();
    setupEventListeners();
});

function setupEventListeners() {
    // Email form submission
    document.getElementById('emailForm').addEventListener('submit', handleEmailSubmit);
}

async function handleEmailSubmit(e) {
    e.preventDefault();
    
    const formData = {
        to: document.getElementById('to').value,
        subject: document.getElementById('subject').value,
        message: document.getElementById('message').value
    };

    try {
        const response = await fetch(`${API_BASE}/api/send-email`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer gmail-api-pro-key-2024'
            },
            body: JSON.stringify(formData)
        });

        const result = await response.json();
        
        if (response.ok) {
            showNotification('Email enviado com sucesso!', 'success');
            document.getElementById('emailForm').reset();
            loadEmails(); // Reload emails list
        } else {
            showNotification(`Erro: ${result.message}`, 'error');
        }
    } catch (error) {
        showNotification('Erro de conexão com a API', 'error');
        console.error('Error:', error);
    }
}

async function loadEmails() {
    try {
        const response = await fetch(`${API_BASE}/api/emails`, {
            headers: {
                'Authorization': 'Bearer gmail-api-pro-key-2024'
            }
        });

        if (response.ok) {
            const emails = await response.json();
            displayEmails(emails);
        } else {
            console.error('Failed to load emails');
        }
    } catch (error) {
        console.error('Error loading emails:', error);
        // Show sample emails for demonstration
        displaySampleEmails();
    }
}

function displayEmails(emails) {
    const emailsList = document.getElementById('emailsList');
    
    if (emails.length === 0) {
        emailsList.innerHTML = '<p>Nenhum email encontrado.</p>';
        return;
    }

    emailsList.innerHTML = emails.map(email => `
        <div class="email-item">
            <h4>${email.subject}</h4>
            <p><strong>De:</strong> ${email.from}</p>
            <p><strong>Para:</strong> ${email.to}</p>
            <p>${email.message.substring(0, 100)}${email.message.length > 100 ? '...' : ''}</p>
            <small>Recebido em: ${new Date(email.timestamp).toLocaleString('pt-BR')}</small>
        </div>
    `).join('');
}

function displaySampleEmails() {
    const sampleEmails = [
        {
            subject: 'Bem-vindo ao Gmail API Pro',
            from: 'sistema@gmailapipro.com',
            to: 'usuario@exemplo.com',
            message: 'Obrigado por usar nosso sistema de API de Gmail profissional. Este é um email de demonstração.',
            timestamp: new Date().toISOString()
        },
        {
            subject: 'Teste de Integração',
            from: 'desenvolvedor@site.com',
            to: 'api@gmailapipro.com',
            message: 'Este é um teste de integração da API enviado através do nosso sistema.',
            timestamp: new Date(Date.now() - 3600000).toISOString()
        }
    ];
    
    displayEmails(sampleEmails);
}

function copyApiKey() {
    const apiKeyInput = document.getElementById('apiKey');
    apiKeyInput.select();
    document.execCommand('copy');
    showNotification('API Key copiada para a área de transferência!', 'success');
}

function showNotification(message, type) {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    
    // Style the notification
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 15px 20px;
        border-radius: 8px;
        color: white;
        font-weight: bold;
        z-index: 1000;
        animation: slideIn 0.3s ease;
        ${type === 'success' ? 'background: #28a745;' : 'background: #dc3545;'}
    `;
    
    // Add animation keyframes
    if (!document.querySelector('#notification-styles')) {
        const style = document.createElement('style');
        style.id = 'notification-styles';
        style.textContent = `
            @keyframes slideIn {
                from { transform: translateX(100%); opacity: 0; }
                to { transform: translateX(0); opacity: 1; }
            }
        `;
        document.head.appendChild(style);
    }
    
    document.body.appendChild(notification);
    
    // Remove notification after 3 seconds
    setTimeout(() => {
        notification.remove();
    }, 3000);
}

// API Testing Functions
window.testAPI = {
    sendEmail: async function(to, subject, message) {
        const response = await fetch(`${API_BASE}/api/send-email`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer gmail-api-pro-key-2024'
            },
            body: JSON.stringify({ to, subject, message })
        });
        return response.json();
    },
    
    getEmails: async function() {
        const response = await fetch(`${API_BASE}/api/emails`, {
            headers: {
                'Authorization': 'Bearer gmail-api-pro-key-2024'
            }
        });
        return response.json();
    }
};

console.log('Gmail API Pro Frontend carregado. Use window.testAPI para testar as funções.');
