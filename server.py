
from flask import Flask, request, jsonify, send_from_directory, session, redirect
from flask_cors import CORS
import json
import os
from datetime import datetime, timedelta
import threading
import time
import hashlib
import uuid

app = Flask(__name__)
CORS(app)
app.secret_key = 'gmail-system-secret-key-2024'

# Configurações do sistema
USERS_FILE = 'users.json'
EMAILS_FILE = 'emails.json'
ADMIN_EMAIL = 'suport.com@gmail.oficial'

# Sistema de domínios personalizados
MAIN_DOMAIN = 'naymail.com'
BUSINESS_DOMAIN = 'nay.com'
registered_companies = {}  # Empresas registradas com subdomínios

# Armazenamento em memória
users_db = {}
emails_db = []
current_session = {}

def load_data():
    """Carrega dados dos arquivos JSON"""
    global users_db, emails_db
    
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r', encoding='utf-8') as f:
            users_db = json.load(f)
    
    if os.path.exists(EMAILS_FILE):
        with open(EMAILS_FILE, 'r', encoding='utf-8') as f:
            emails_db = json.load(f)

def save_data():
    """Salva dados nos arquivos JSON"""
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(users_db, f, ensure_ascii=False, indent=2)
    
    with open(EMAILS_FILE, 'w', encoding='utf-8') as f:
        json.dump(emails_db, f, ensure_ascii=False, indent=2)

def create_admin_user():
    """Cria usuário administrador"""
    # Sempre atualizar o usuário admin para garantir que existe
    users_db[ADMIN_EMAIL] = {
        'email': ADMIN_EMAIL,
        'name': 'Administrador Sistema',
        'password': hashlib.md5('admin123'.encode()).hexdigest(),
        'created_at': datetime.now().isoformat() if ADMIN_EMAIL not in users_db else users_db[ADMIN_EMAIL].get('created_at', datetime.now().isoformat()),
        'profile_pic': 'https://ui-avatars.com/api/?name=Admin&background=ff0000&color=fff',
        'is_admin': True,
        'user_id': 'admin_001'
    }
    save_data()

def get_current_user():
    """Obtém usuário atual da sessão"""
    user_id = session.get('user_id')
    user_email = session.get('user_email')
    
    if user_id and user_email:
        # Verificar se o usuário ainda existe no banco
        if user_email in users_db:
            user = users_db[user_email]
            if user.get('user_id') == user_id:
                # Garantir que o admin está sempre marcado como admin
                if user_email == ADMIN_EMAIL:
                    user['is_admin'] = True
                    save_data()
                return user
    return None

def generate_business_email(company_name, email_type='noreply'):
    """Gera email empresarial baseado no nome da empresa"""
    clean_name = company_name.lower().replace(' ', '').replace('-', '').replace('_', '')
    return f"{email_type}@{clean_name}.{BUSINESS_DOMAIN}"

def register_company_domain(company_name, company_info):
    """Registra uma empresa para usar subdomínio personalizado"""
    domain_key = company_name.lower().replace(' ', '')
    registered_companies[domain_key] = {
        'name': company_name,
        'subdomain': f"{domain_key}.{BUSINESS_DOMAIN}",
        'registered_at': datetime.now().isoformat(),
        'email_types': ['noreply', 'suporte', 'verificacao', 'notificacoes'],
        'info': company_info
    }
    save_companies_data()
    return registered_companies[domain_key]

def save_companies_data():
    """Salva dados das empresas registradas"""
    with open('companies.json', 'w', encoding='utf-8') as f:
        json.dump(registered_companies, f, ensure_ascii=False, indent=2)

def load_companies_data():
    """Carrega dados das empresas registradas"""
    global registered_companies
    if os.path.exists('companies.json'):
        with open('companies.json', 'r', encoding='utf-8') as f:
            registered_companies = json.load(f)

def get_user_emails(user_email, folder='inbox'):
    """Obtém emails do usuário por pasta"""
    user_emails = []
    for email in emails_db:
        try:
            if folder == 'inbox' and email.get('to') == user_email:
                user_emails.append(email)
            elif folder == 'sent' and email.get('from') == user_email:
                user_emails.append(email)
            elif folder == 'drafts' and email.get('folder') == 'drafts' and email.get('from') == user_email:
                user_emails.append(email)
            elif folder == 'starred' and email.get('starred') and (email.get('to') == user_email or email.get('from') == user_email):
                user_emails.append(email)
        except Exception as e:
            print(f"Erro ao processar email: {e}")
            continue
    
    return sorted(user_emails, key=lambda x: x.get('date', ''), reverse=True)

# Inicializar dados
load_data()
load_companies_data()
create_admin_user()

@app.route('/')
def index():
    """Página principal com verificação de login"""
    user = get_current_user()
    if not user:
        return send_from_directory('.', 'login.html')
    return send_from_directory('.', 'index.html')

@app.route('/login.html')
def login_page():
    return send_from_directory('.', 'login.html')

@app.route('/api-docs')
def api_docs():
    return send_from_directory('.', 'api_docs.html')

@app.route('/docs')
def docs():
    """Rota principal de documentação da API"""
    return send_from_directory('.', 'api_docs.html')

@app.route('/reset-password')
def reset_password_page():
    """Página de redefinição de senha"""
    return send_from_directory('.', 'reset-password.html')

@app.route('/<path:filename>')
def serve_static(filename):
    """Servir arquivos estáticos"""
    return send_from_directory('.', filename)

@app.route('/api/login', methods=['POST'])
def login():
    """Login do usuário com verificação de segurança"""
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    security_answers = data.get('security_answers', {})
    
    if not email or not password:
        return jsonify({'error': 'Email e senha são obrigatórios'}), 400
    
    # Verificar se usuário existe
    if email not in users_db:
        return jsonify({'error': 'Usuário não encontrado. Use suport.com@gmail.oficial para admin'}), 401
    
    # Verificar senha
    user = users_db[email]
    if user['password'] != hashlib.md5(password.encode()).hexdigest():
        return jsonify({'error': 'Senha incorreta'}), 401
    
    # Verificação de segurança adicional para contas que não são admin
    if email != ADMIN_EMAIL:
        # Verificar se tem perguntas de segurança configuradas
        if 'security_questions' in user and user['security_questions']:
            if not security_answers:
                # Solicitar perguntas de segurança
                return jsonify({
                    'require_security': True,
                    'security_questions': [
                        {'id': 1, 'question': user['security_questions'].get('question1', 'Qual o nome da sua primeira escola?')},
                        {'id': 2, 'question': user['security_questions'].get('question2', 'Qual o nome do seu primeiro animal de estimação?')}
                    ]
                })
            
            # Verificar respostas de segurança
            answer1_hash = hashlib.md5(security_answers.get('answer1', '').lower().encode()).hexdigest()
            answer2_hash = hashlib.md5(security_answers.get('answer2', '').lower().encode()).hexdigest()
            
            if (answer1_hash != user['security_questions'].get('answer1_hash') or 
                answer2_hash != user['security_questions'].get('answer2_hash')):
                return jsonify({'error': 'Respostas de segurança incorretas'}), 401
    
    # Criar sessão
    session['user_id'] = user['user_id']
    session['user_email'] = email
    session['is_admin'] = user.get('is_admin', False)
    
    # Atualizar último login
    user['last_login'] = datetime.now().isoformat()
    save_data()
    
    print(f"Login realizado: {email}, Admin: {user.get('is_admin', False)}")
    
    return jsonify({
        'success': True,
        'user': {
            'email': email,
            'name': user['name'],
            'user_id': user['user_id'],
            'is_admin': user.get('is_admin', False)
        }
    })

@app.route('/api/logout', methods=['POST'])
def logout():
    """Logout do usuário"""
    session.clear()
    return jsonify({'success': True})

@app.route('/api/clear-saved-accounts', methods=['POST'])
def clear_saved_accounts():
    """Limpar todas as contas salvas (usado quando necessário)"""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Usuário não logado'}), 401
    
    return jsonify({'success': True, 'message': 'Use localStorage.clear() no frontend para limpar contas salvas'})

@app.route('/api/user-info')
def get_user_info():
    """Obter informações do usuário logado"""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Usuário não logado'}), 401
    
    user_email = session.get('user_email')
    inbox_count = len([e for e in get_user_emails(user_email, 'inbox') if not e.get('read')])
    sent_count = len(get_user_emails(user_email, 'sent'))
    drafts_count = len(get_user_emails(user_email, 'drafts'))
    
    return jsonify({
        'email': user_email,
        'name': user['name'],
        'user_id': user['user_id'],
        'inbox_count': inbox_count,
        'sent_count': sent_count,
        'drafts_count': drafts_count,
        'profile_pic': user.get('profile_pic', ''),
        'is_admin': user.get('is_admin', False)
    })

@app.route('/api/emails/<folder>')
def get_emails(folder):
    """Obter emails por pasta"""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Usuário não logado'}), 401
    
    user_email = session.get('user_email')
    emails = get_user_emails(user_email, folder)
    return jsonify(emails)

@app.route('/api/email/<email_id>')
def get_email_detail(email_id):
    """Obter detalhes de um email específico"""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Usuário não logado'}), 401
    
    user_email = session.get('user_email')
    
    for email in emails_db:
        if email.get('id') == email_id and (email.get('to') == user_email or email.get('from') == user_email):
            email['read'] = True
            save_data()
            return jsonify(email)
    
    return jsonify({'error': 'Email não encontrado'}), 404

@app.route('/api/send-email', methods=['POST'])
def send_email():
    """Enviar email"""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Usuário não logado'}), 401
    
    data = request.get_json()
    if not data or not all(k in data for k in ['to', 'subject', 'body']):
        return jsonify({'error': 'Dados obrigatórios: to, subject, body'}), 400
    
    user_email = session.get('user_email')
    
    new_email = {
        'id': str(uuid.uuid4()),
        'from': user_email,
        'to': data['to'],
        'subject': data['subject'],
        'body': data['body'],
        'date': datetime.now().isoformat(),
        'read': True,
        'starred': False,
        'folder': 'sent',
        'highlighted': data.get('highlighted', False)
    }
    
    emails_db.append(new_email)
    save_data()
    
    return jsonify({'success': True, 'message': 'Email enviado com sucesso'})

@app.route('/api/admin/broadcast', methods=['POST'])
def admin_broadcast():
    """Enviar email para todos os usuários (apenas admin)"""
    user = get_current_user()
    if not user or not user.get('is_admin'):
        return jsonify({'error': 'Acesso negado'}), 403
    
    data = request.get_json()
    if not data or not all(k in data for k in ['subject', 'body']):
        return jsonify({'error': 'Subject e body são obrigatórios'}), 400
    
    sent_count = 0
    for user_email in users_db.keys():
        if user_email != ADMIN_EMAIL:  # Não enviar para o próprio admin
            broadcast_email = {
                'id': str(uuid.uuid4()),
                'from': ADMIN_EMAIL,
                'to': user_email,
                'subject': f"[SISTEMA] {data['subject']}",
                'body': data['body'],
                'date': datetime.now().isoformat(),
                'read': False,
                'starred': False,
                'folder': 'inbox'
            }
            emails_db.append(broadcast_email)
            sent_count += 1
    
    save_data()
    return jsonify({'success': True, 'sent_to': sent_count, 'message': f'Email enviado para {sent_count} usuários'})

@app.route('/api/admin/users')
def admin_users():
    """Listar todos os usuários (apenas admin)"""
    user = get_current_user()
    if not user or not user.get('is_admin'):
        return jsonify({'error': 'Acesso negado'}), 403
    
    users_list = []
    for email, user_data in users_db.items():
        # Garantir que todos os usuários tenham user_id
        if 'user_id' not in user_data:
            user_data['user_id'] = f"user_{len(users_db) + 1:03d}"
            
        users_list.append({
            'email': email,
            'name': user_data['name'],
            'user_id': user_data.get('user_id', 'N/A'),
            'created_at': user_data.get('created_at', datetime.now().isoformat()),
            'is_admin': user_data.get('is_admin', False)
        })
    
    save_data()  # Salvar as correções
    return jsonify(users_list)

@app.route('/api/admin/system-logs')
def admin_system_logs():
    """Obter logs do sistema (apenas admin)"""
    user = get_current_user()
    if not user or not user.get('is_admin'):
        return jsonify({'error': 'Acesso negado'}), 403
    
    # Filtrar emails de log do sistema
    system_logs = []
    for email in emails_db:
        if email.get('to') == ADMIN_EMAIL and (
            email.get('from') == 'sistema@gmail.oficial' or 
            '[LOG]' in email.get('subject', '')
        ):
            system_logs.append(email)
    
    return jsonify(sorted(system_logs, key=lambda x: x.get('date', ''), reverse=True))

@app.route('/api/save-draft', methods=['POST'])
def save_draft():
    """Salvar rascunho"""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Usuário não logado'}), 401
    
    data = request.get_json()
    user_email = session.get('user_email')
    
    draft = {
        'id': str(uuid.uuid4()),
        'from': user_email,
        'to': data.get('to', ''),
        'subject': data.get('subject', ''),
        'body': data.get('body', ''),
        'date': datetime.now().isoformat(),
        'read': True,
        'starred': False,
        'folder': 'drafts'
    }
    
    emails_db.append(draft)
    save_data()
    
    return jsonify({'success': True, 'draft_id': draft['id']})

@app.route('/api/email/<email_id>/delete', methods=['DELETE'])
def delete_email(email_id):
    """Deletar email"""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Usuário não logado'}), 401
    
    global emails_db
    user_email = session.get('user_email')
    
    # Verificar se o email pertence ao usuário
    email_found = False
    for email in emails_db:
        if email.get('id') == email_id and (email.get('to') == user_email or email.get('from') == user_email):
            email_found = True
            break
    
    if not email_found:
        return jsonify({'error': 'Email não encontrado'}), 404
    
    emails_db = [e for e in emails_db if e.get('id') != email_id]
    save_data()
    
    return jsonify({'success': True, 'message': 'Email deletado'})

@app.route('/api/email/<email_id>/star', methods=['POST'])
def star_email(email_id):
    """Marcar/desmarcar email como favorito"""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Usuário não logado'}), 401
    
    user_email = session.get('user_email')
    
    for email in emails_db:
        if email.get('id') == email_id and (email.get('to') == user_email or email.get('from') == user_email):
            email['starred'] = not email.get('starred', False)
            save_data()
            return jsonify({'success': True, 'starred': email['starred']})
    
    return jsonify({'error': 'Email não encontrado'}), 404

@app.route('/api/email/<email_id>/highlight', methods=['POST'])
def highlight_email(email_id):
    """Marcar/desmarcar email como destacado (apenas admin)"""
    user = get_current_user()
    if not user or not user.get('is_admin'):
        return jsonify({'error': 'Acesso negado'}), 403
    
    for email in emails_db:
        if email.get('id') == email_id:
            email['highlighted'] = not email.get('highlighted', False)
            save_data()
            return jsonify({'success': True, 'highlighted': email['highlighted']})
    
    return jsonify({'error': 'Email não encontrado'}), 404

@app.route('/api/admin/highlighted-emails')
def get_highlighted_emails():
    """Obter emails destacados (apenas admin)"""
    user = get_current_user()
    if not user or not user.get('is_admin'):
        return jsonify({'error': 'Acesso negado'}), 403
    
    highlighted = [email for email in emails_db if email.get('highlighted', False)]
    return jsonify(sorted(highlighted, key=lambda x: x.get('date', ''), reverse=True))

@app.route('/api/search', methods=['POST'])
def search_emails():
    """Buscar emails"""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Usuário não logado'}), 401
    
    data = request.get_json()
    query = data.get('query', '').lower()
    user_email = session.get('user_email')
    
    results = []
    for email in emails_db:
        try:
            if (email.get('to') == user_email or email.get('from') == user_email) and (
                query in email.get('subject', '').lower() or 
                query in email.get('body', '').lower() or 
                query in email.get('from', '').lower()
            ):
                results.append(email)
        except Exception as e:
            print(f"Erro na busca: {e}")
            continue
    
    return jsonify(results)

@app.route('/api/refresh-emails', methods=['POST'])
def refresh_emails():
    """Atualizar lista de emails"""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Usuário não logado'}), 401
    
    user_email = session.get('user_email')
    inbox_emails = get_user_emails(user_email, 'inbox')
    
    return jsonify({'success': True, 'count': len(inbox_emails)})

@app.route('/api/external/send-verification', methods=['POST'])
def send_verification_email():
    """API para sites externos enviarem emails de verificação com sistema avançado"""
    data = request.get_json()
    
    # Verificar API key de segurança
    api_key = request.headers.get('X-API-Key')
    if not api_key or api_key != 'gmail-verification-api-2024':
        return jsonify({'error': 'API key inválida'}), 401
    
    # Validar dados obrigatórios
    required_fields = ['to_email', 'site_name', 'verification_code', 'verification_url']
    if not data or not all(field in data for field in required_fields):
        return jsonify({'error': 'Campos obrigatórios: to_email, site_name, verification_code, verification_url'}), 400
    
    # Verificar se o usuário existe no sistema
    to_email = data['to_email']
    if to_email not in users_db:
        return jsonify({'error': 'Usuário não encontrado no sistema'}), 404
    
    # Determinar prioridade e tipo especial
    priority = data.get('priority', 'normal')  # high, normal, low
    verification_type = data.get('type', 'account')  # account, email, phone, security
    expires_in = data.get('expires_in', 3600)  # segundos até expirar
    
    # Configurar ícones e cores baseado no tipo
    type_config = {
        'account': {'icon': 'fa-user-check', 'color': '#34a853', 'label': 'Verificação de Conta'},
        'email': {'icon': 'fa-envelope-check', 'color': '#4285f4', 'label': 'Verificação de Email'},
        'phone': {'icon': 'fa-phone-check', 'color': '#fbbc04', 'label': 'Verificação de Telefone'},
        'security': {'icon': 'fa-shield-check', 'color': '#ea4335', 'label': 'Verificação de Segurança'},
        'two_factor': {'icon': 'fa-key', 'color': '#9c27b0', 'label': 'Autenticação 2FA'}
    }
    
    config = type_config.get(verification_type, type_config['account'])
    
    # Criar corpo do email mais avançado
    expiry_time = datetime.now() + timedelta(seconds=expires_in)
    
    body = f"""
🔐 {config['label']} - {data['site_name']}

Olá!

Você solicitou {config['label'].lower()} no site {data['site_name']}.

📋 DETALHES DA VERIFICAÇÃO:
─────────────────────────────
🎯 Código: {data['verification_code']}
⏰ Válido até: {expiry_time.strftime('%d/%m/%Y às %H:%M')}
🌐 Site: {data['site_name']}
🔒 Tipo: {config['label']}

🚀 VERIFICAÇÃO RÁPIDA:
Clique no botão abaixo para verificar automaticamente:
{data['verification_url']}

💡 INSTRUÇÕES:
1. Cole o código acima no site
2. Ou clique no link de verificação
3. Complete o processo em até {expires_in//60} minutos

⚠️ SEGURANÇA:
• Se você não solicitou esta verificação, ignore este email
• Nunca compartilhe este código com terceiros
• O código expira automaticamente por segurança

📧 Este email foi enviado através do Sistema Gmail Independente
🆔 ID da Verificação: {str(uuid.uuid4())[:8]}
    """.strip()
    
    # Gerar email de origem baseado no sistema de domínios
    company_name = data['site_name']
    from_email = generate_business_email(company_name, 'verificacao')
    
    # Registrar empresa se não existir
    if company_name.lower().replace(' ', '') not in registered_companies:
        register_company_domain(company_name, {
            'type': 'verification_service',
            'auto_registered': True
        })
    
    # Criar email de verificação avançado
    verification_email = {
        'id': str(uuid.uuid4()),
        'from': from_email,
        'to': to_email,
        'subject': f"🔐 {config['label']} - {data['site_name']}",
        'body': body,
        'date': datetime.now().isoformat(),
        'read': False,
        'starred': False,
        'folder': 'inbox',
        'verification': True,
        'verification_advanced': True,
        'verification_type': verification_type,
        'verification_priority': priority,
        'verification_expires': expiry_time.isoformat(),
        'verification_icon': config['icon'],
        'verification_color': config['color'],
        'verification_label': config['label'],
        'site_origin': data['site_name'],
        'security_level': data.get('security_level', 'standard'),
        'auto_expire': True,
        'tracking_id': str(uuid.uuid4())[:8]
    }
    
    # Auto-destacar emails de alta prioridade ou segurança
    if priority == 'high' or verification_type in ['security', 'two_factor']:
        verification_email['highlighted'] = True
        verification_email['priority_highlight'] = True
    
    emails_db.append(verification_email)
    save_data()
    
    return jsonify({
        'success': True,
        'message': 'Email de verificação avançado enviado',
        'email_id': verification_email['id'],
        'tracking_id': verification_email['tracking_id'],
        'expires_at': verification_email['verification_expires'],
        'type': verification_type,
        'priority': priority
    })

@app.route('/api/external/send-reset-password', methods=['POST'])
def send_reset_password_email():
    """API para sites externos enviarem emails de recuperação de senha"""
    data = request.get_json()
    
    # Verificar API key
    api_key = request.headers.get('X-API-Key')
    if not api_key or api_key != 'gmail-verification-api-2024':
        return jsonify({'error': 'API key inválida'}), 401
    
    # Validar dados
    required_fields = ['to_email', 'site_name', 'reset_token', 'reset_url']
    if not data or not all(field in data for field in required_fields):
        return jsonify({'error': 'Campos obrigatórios: to_email, site_name, reset_token, reset_url'}), 400
    
    to_email = data['to_email']
    if to_email not in users_db:
        return jsonify({'error': 'Usuário não encontrado'}), 404
    
    # Gerar email de origem usando sistema de domínios
    company_name = data['site_name']
    from_email = generate_business_email(company_name, 'suporte')
    
    # Registrar empresa se não existir
    if company_name.lower().replace(' ', '') not in registered_companies:
        register_company_domain(company_name, {
            'type': 'password_recovery',
            'auto_registered': True
        })
    
    # Criar email de recuperação
    reset_email = {
        'id': str(uuid.uuid4()),
        'from': from_email,
        'to': to_email,
        'subject': f"Recuperação de senha - {data['site_name']}",
        'body': f"""
Olá!

Você solicitou recuperação de senha no site {data['site_name']}.

Clique no link abaixo para redefinir sua senha:
{data['reset_url']}

Token de recuperação: {data['reset_token']}

Este link expira em 24 horas.

Se você não solicitou esta recuperação, ignore este email e sua conta permanecerá segura.

Este email foi enviado através do Sistema Gmail Independente.
        """.strip(),
        'date': datetime.now().isoformat(),
        'read': False,
        'starred': False,
        'folder': 'inbox',
        'password_reset': True,
        'site_origin': data['site_name']
    }
    
    emails_db.append(reset_email)
    save_data()
    
    return jsonify({
        'success': True,
        'message': 'Email de recuperação enviado',
        'email_id': reset_email['id']
    })

@app.route('/api/external/send-notification', methods=['POST'])
def send_notification_email():
    """API para sites externos enviarem emails de notificação"""
    data = request.get_json()
    
    # Verificar API key
    api_key = request.headers.get('X-API-Key')
    if not api_key or api_key != 'gmail-verification-api-2024':
        return jsonify({'error': 'API key inválida'}), 401
    
    # Validar dados
    required_fields = ['to_email', 'site_name', 'subject', 'message']
    if not data or not all(field in data for field in required_fields):
        return jsonify({'error': 'Campos obrigatórios: to_email, site_name, subject, message'}), 400
    
    to_email = data['to_email']
    if to_email not in users_db:
        return jsonify({'error': 'Usuário não encontrado'}), 404
    
    # Gerar email de origem usando sistema de domínios
    company_name = data['site_name']
    from_email = generate_business_email(company_name, 'notificacoes')
    
    # Registrar empresa se não existir
    if company_name.lower().replace(' ', '') not in registered_companies:
        register_company_domain(company_name, {
            'type': 'notifications',
            'auto_registered': True
        })
    
    # Criar email de notificação
    notification_email = {
        'id': str(uuid.uuid4()),
        'from': from_email,
        'to': to_email,
        'subject': f"[{data['site_name']}] {data['subject']}",
        'body': f"""
{data['message']}

---
Este email foi enviado através do Sistema Gmail Independente.
Site: {data['site_name']}
        """.strip(),
        'date': datetime.now().isoformat(),
        'read': False,
        'starred': False,
        'folder': 'inbox',
        'notification': True,
        'site_origin': data['site_name']
    }
    
    emails_db.append(notification_email)
    save_data()
    
    return jsonify({
        'success': True,
        'message': 'Email de notificação enviado',
        'email_id': notification_email['id']
    })

@app.route('/api/external/send-advanced-verification', methods=['POST'])
def send_advanced_verification():
    """API para enviar verificações avançadas com recursos especiais"""
    data = request.get_json()
    
    # Verificar API key
    api_key = request.headers.get('X-API-Key')
    if not api_key or api_key != 'gmail-verification-api-2024':
        return jsonify({'error': 'API key inválida'}), 401
    
    # Validar dados
    required_fields = ['to_email', 'site_name', 'verification_code']
    if not data or not all(field in data for field in required_fields):
        return jsonify({'error': 'Campos obrigatórios: to_email, site_name, verification_code'}), 400
    
    to_email = data['to_email']
    if to_email not in users_db:
        return jsonify({'error': 'Usuário não encontrado'}), 404
    
    # Configurações avançadas
    verification_type = data.get('type', 'premium')  # premium, enterprise, vip
    theme = data.get('theme', 'modern')  # modern, classic, minimal
    language = data.get('language', 'pt-BR')
    custom_branding = data.get('custom_branding', False)
    
    # Templates por tipo
    if verification_type == 'premium':
        subject_emoji = '⭐'
        priority_level = 'high'
        highlight_color = '#ff6b35'
    elif verification_type == 'enterprise':
        subject_emoji = '🏢'
        priority_level = 'critical'
        highlight_color = '#673ab7'
    elif verification_type == 'vip':
        subject_emoji = '👑'
        priority_level = 'urgent'
        highlight_color = '#ff9800'
    else:
        subject_emoji = '🔐'
        priority_level = 'normal'
        highlight_color = '#4285f4'
    
    # Corpo do email premium
    advanced_body = f"""
{subject_emoji} VERIFICAÇÃO {verification_type.upper()} - {data['site_name']}

═══════════════════════════════════════
    ✨ ACESSO EXCLUSIVO SOLICITADO ✨
═══════════════════════════════════════

Olá!

Você está acessando recursos {verification_type} no {data['site_name']}.

🎯 CÓDIGO DE VERIFICAÇÃO PREMIUM:
╔══════════════════════════════════════╗
║             {data['verification_code']}             ║
╚══════════════════════════════════════╝

📊 DETALHES DA SESSÃO:
• Tipo: {verification_type.title()}
• Nível: {priority_level.title()}
• Tema: {theme.title()}
• Site: {data['site_name']}
• Timestamp: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}

🚀 ACESSO RÁPIDO:
{data.get('verification_url', f'https://{data["site_name"].lower()}.com/verify')}

🔒 RECURSOS INCLUSOS:
• ✅ Verificação instantânea
• ✅ Suporte prioritário
• ✅ Acesso a recursos premium
• ✅ Segurança avançada

⚡ ESTE É UM EMAIL PREMIUM COM ALTA PRIORIDADE

📧 Sistema Gmail Independente - Verificação Avançada
🆔 Tracking: {str(uuid.uuid4())[:8]}
    """.strip()
    
    # Gerar email de origem usando sistema de domínios
    company_name = data['site_name']
    from_email = generate_business_email(company_name, verification_type)
    
    # Registrar empresa se não existir
    if company_name.lower().replace(' ', '') not in registered_companies:
        register_company_domain(company_name, {
            'type': 'advanced_verification',
            'verification_type': verification_type,
            'auto_registered': True
        })
    
    # Criar email avançado
    advanced_email = {
        'id': str(uuid.uuid4()),
        'from': from_email,
        'to': to_email,
        'subject': f"{subject_emoji} Verificação {verification_type.title()} - {data['site_name']}",
        'body': advanced_body,
        'date': datetime.now().isoformat(),
        'read': False,
        'starred': True,  # Auto-favoritar verificações avançadas
        'folder': 'inbox',
        'verification': True,
        'verification_advanced': True,
        'verification_premium': True,
        'verification_type': verification_type,
        'verification_priority': priority_level,
        'verification_theme': theme,
        'verification_color': highlight_color,
        'highlighted': True,  # Auto-destacar
        'priority_highlight': True,
        'premium_badge': True,
        'site_origin': data['site_name'],
        'tracking_id': str(uuid.uuid4())[:8],
        'custom_branding': custom_branding
    }
    
    emails_db.append(advanced_email)
    save_data()
    
    return jsonify({
        'success': True,
        'message': f'Verificação {verification_type} enviada com sucesso',
        'email_id': advanced_email['id'],
        'tracking_id': advanced_email['tracking_id'],
        'type': verification_type,
        'priority': priority_level,
        'theme': theme
    })

@app.route('/api/external/check-user', methods=['POST'])
def check_user_exists():
    """API para verificar se um usuário existe no sistema"""
    data = request.get_json()
    
    # Verificar API key
    api_key = request.headers.get('X-API-Key')
    if not api_key or api_key != 'gmail-verification-api-2024':
        return jsonify({'error': 'API key inválida'}), 401
    
    email = data.get('email')
    if not email:
        return jsonify({'error': 'Email é obrigatório'}), 400
    
    exists = email in users_db
    user_info = None
    
    if exists:
        user = users_db[email]
        user_info = {
            'name': user['name'],
            'user_id': user['user_id'],
            'created_at': user.get('created_at')
        }
    
    return jsonify({
        'exists': exists,
        'user_info': user_info
    })

@app.route('/api/quick-login/accounts')
def get_quick_login_accounts():
    """API para obter todas as contas cadastradas para login rápido"""
    accounts_list = []
    
    for email, user_data in users_db.items():
        # Não incluir senhas por segurança, apenas informações básicas
        account_info = {
            'email': email,
            'name': user_data['name'],
            'user_id': user_data.get('user_id', 'N/A'),
            'profile_pic': user_data.get('profile_pic', f'https://ui-avatars.com/api/?name={user_data["name"]}&background=4285f4&color=fff'),
            'is_admin': user_data.get('is_admin', False),
            'created_at': user_data.get('created_at', datetime.now().isoformat()),
            'last_login': user_data.get('last_login', 'Nunca')
        }
        accounts_list.append(account_info)
    
    # Ordenar por data de criação mais recente
    accounts_list.sort(key=lambda x: x['created_at'], reverse=True)
    
    return jsonify({
        'success': True,
        'accounts': accounts_list,
        'total': len(accounts_list)
    })

@app.route('/api/quick-login/validate', methods=['POST'])
def validate_quick_login():
    """API para validar login rápido com email"""
    data = request.get_json()
    
    if not data or 'email' not in data:
        return jsonify({'error': 'Email é obrigatório'}), 400
    
    email = data['email']
    
    # Verificar se usuário existe
    if email not in users_db:
        return jsonify({'error': 'Usuário não encontrado'}), 404
    
    user = users_db[email]
    
    # Atualizar último login
    user['last_login'] = datetime.now().isoformat()
    save_data()
    
    # Criar sessão
    session['user_id'] = user['user_id']
    session['user_email'] = email
    session['is_admin'] = user.get('is_admin', False)
    
    print(f"Login rápido realizado: {email}, Admin: {user.get('is_admin', False)}")
    
    return jsonify({
        'success': True,
        'message': 'Login rápido realizado com sucesso',
        'user': {
            'email': email,
            'name': user['name'],
            'user_id': user['user_id'],
            'is_admin': user.get('is_admin', False),
            'profile_pic': user.get('profile_pic', '')
        }
    })

@app.route('/api/quick-login/recent')
def get_recent_accounts():
    """API para obter contas com login recente (últimas 5)"""
    recent_accounts = []
    
    # Filtrar contas que têm last_login
    for email, user_data in users_db.items():
        if 'last_login' in user_data and user_data['last_login'] != 'Nunca':
            account_info = {
                'email': email,
                'name': user_data['name'],
                'user_id': user_data.get('user_id', 'N/A'),
                'profile_pic': user_data.get('profile_pic', ''),
                'is_admin': user_data.get('is_admin', False),
                'last_login': user_data['last_login']
            }
            recent_accounts.append(account_info)
    
    # Ordenar por último login mais recente
    recent_accounts.sort(key=lambda x: x['last_login'], reverse=True)
    
    # Retornar apenas as 5 mais recentes
    recent_accounts = recent_accounts[:5]
    
    return jsonify({
        'success': True,
        'recent_accounts': recent_accounts,
        'total': len(recent_accounts)
    })

@app.route('/api/admin/companies')
def get_registered_companies():
    """API para obter empresas registradas (apenas admin)"""
    user = get_current_user()
    if not user or not user.get('is_admin'):
        return jsonify({'error': 'Acesso negado'}), 403
    
    companies_list = []
    for key, company in registered_companies.items():
        companies_list.append({
            'key': key,
            'name': company['name'],
            'subdomain': company['subdomain'],
            'registered_at': company['registered_at'],
            'email_types': company['email_types'],
            'auto_registered': company.get('info', {}).get('auto_registered', False)
        })
    
    return jsonify({
        'success': True,
        'companies': companies_list,
        'total': len(companies_list),
        'main_domain': MAIN_DOMAIN,
        'business_domain': BUSINESS_DOMAIN
    })

@app.route('/api/admin/register-company', methods=['POST'])
def manual_register_company():
    """API para registrar empresa manualmente (apenas admin)"""
    user = get_current_user()
    if not user or not user.get('is_admin'):
        return jsonify({'error': 'Acesso negado'}), 403
    
    data = request.get_json()
    company_name = data.get('company_name')
    
    if not company_name:
        return jsonify({'error': 'Nome da empresa é obrigatório'}), 400
    
    company_info = {
        'type': 'manual_registration',
        'registered_by': user['email'],
        'auto_registered': False,
        'description': data.get('description', ''),
        'contact_email': data.get('contact_email', '')
    }
    
    registered_company = register_company_domain(company_name, company_info)
    
    return jsonify({
        'success': True,
        'message': f'Empresa {company_name} registrada com sucesso',
        'company': registered_company
    })

@app.route('/api/reset-password/validate-token', methods=['POST'])
def validate_reset_token():
    """Validar token de redefinição de senha"""
    data = request.get_json()
    token = data.get('token')
    
    if not token:
        return jsonify({'error': 'Token é obrigatório'}), 400
    
    # Para demonstração, aceitar tokens com 8+ caracteres ou "exemplo"
    if token == 'exemplo' or len(token) >= 8:
        return jsonify({
            'success': True,
            'message': 'Token válido',
            'email_hint': '***@***.com'  # Ocultar email por segurança
        })
    
    return jsonify({'error': 'Token inválido ou expirado'}), 400

@app.route('/api/reset-password/change', methods=['POST'])
def change_password_with_token():
    """Redefinir senha usando token"""
    data = request.get_json()
    token = data.get('token')
    new_password = data.get('new_password')
    email = data.get('email')  # Email será fornecido no processo
    
    if not all([token, new_password, email]):
        return jsonify({'error': 'Token, email e nova senha são obrigatórios'}), 400
    
    # Validar token (simplificado para demonstração)
    if token != 'exemplo' and len(token) < 8:
        return jsonify({'error': 'Token inválido'}), 400
    
    # Verificar se usuário existe
    if email not in users_db:
        return jsonify({'error': 'Usuário não encontrado'}), 404
    
    # Atualizar senha
    users_db[email]['password'] = hashlib.md5(new_password.encode()).hexdigest()
    save_data()
    
    return jsonify({
        'success': True,
        'message': 'Senha redefinida com sucesso'
    })

@app.route('/api/setup-security', methods=['POST'])
def setup_security_questions():
    """Configurar perguntas de segurança"""
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    question1 = data.get('question1')
    answer1 = data.get('answer1')
    question2 = data.get('question2')
    answer2 = data.get('answer2')
    
    if not all([email, password, question1, answer1, question2, answer2]):
        return jsonify({'error': 'Todos os campos são obrigatórios'}), 400
    
    # Verificar credenciais
    if email not in users_db:
        return jsonify({'error': 'Usuário não encontrado'}), 404
    
    user = users_db[email]
    if user['password'] != hashlib.md5(password.encode()).hexdigest():
        return jsonify({'error': 'Senha incorreta'}), 401
    
    # Salvar perguntas de segurança
    user['security_questions'] = {
        'question1': question1,
        'answer1_hash': hashlib.md5(answer1.lower().encode()).hexdigest(),
        'question2': question2,
        'answer2_hash': hashlib.md5(answer2.lower().encode()).hexdigest(),
        'created_at': datetime.now().isoformat()
    }
    
    save_data()
    
    return jsonify({
        'success': True,
        'message': 'Perguntas de segurança configuradas com sucesso'
    })

@app.route('/api/register', methods=['POST'])
def register():
    """Registrar novo usuário com segurança"""
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    name = data.get('name')
    question1 = data.get('question1')
    answer1 = data.get('answer1')
    question2 = data.get('question2')
    answer2 = data.get('answer2')
    
    if not all([email, password, name]):
        return jsonify({'error': 'Email, senha e nome são obrigatórios'}), 400
    
    # Verificar perguntas de segurança apenas se pelo menos uma foi fornecida
    has_security_questions = any([question1, answer1, question2, answer2])
    if has_security_questions and not all([question1, answer1, question2, answer2]):
        return jsonify({'error': 'Se escolher usar perguntas de segurança, complete ambas'}), 400
    
    # Verificar se usuário já existe
    if email in users_db:
        return jsonify({'error': 'Usuário já existe'}), 409
    
    # Criar novo usuário
    user_id = f"user_{len(users_db) + 1:03d}"
    user_data = {
        'email': email,
        'name': name,
        'password': hashlib.md5(password.encode()).hexdigest(),
        'user_id': user_id,
        'created_at': datetime.now().isoformat(),
        'profile_pic': f'https://ui-avatars.com/api/?name={name}&background=4285f4&color=fff',
        'is_admin': False
    }
    
    # Adicionar perguntas de segurança apenas se foram fornecidas
    if has_security_questions:
        user_data['security_questions'] = {
            'question1': question1,
            'answer1_hash': hashlib.md5(answer1.lower().encode()).hexdigest(),
            'question2': question2,
            'answer2_hash': hashlib.md5(answer2.lower().encode()).hexdigest(),
            'created_at': datetime.now().isoformat()
        }
    
    users_db[email] = user_data
    
    save_data()
    
    return jsonify({
        'success': True,
        'message': 'Usuário criado com sucesso',
        'user_id': user_id
    })

@app.route('/api/domain-info/<domain>')
def get_domain_info(domain):
    """API para obter informações sobre um domínio específico"""
    # Verificar se é domínio principal
    if domain.endswith(f'.{MAIN_DOMAIN}'):
        return jsonify({
            'type': 'main_domain',
            'domain': MAIN_DOMAIN,
            'description': 'Domínio principal para usuários'
        })
    
    # Verificar se é subdomínio empresarial
    if domain.endswith(f'.{BUSINESS_DOMAIN}'):
        company_key = domain.replace(f'.{BUSINESS_DOMAIN}', '')
        if company_key in registered_companies:
            company = registered_companies[company_key]
            return jsonify({
                'type': 'business_domain',
                'company': company,
                'available_emails': [f"{email_type}@{domain}" for email_type in company['email_types']]
            })
    
    return jsonify({'error': 'Domínio não encontrado'}), 404

# Sistema de Token de Conta
token_requests = {}  # Armazenar solicitações de token
generated_tokens = {}  # Armazenar tokens gerados

def generate_token_request_id():
    """Gera ID único para solicitação de token"""
    import string
    import random
    return ''.join(random.choices(string.ascii_letters + string.digits, k=32))

def generate_user_token():
    """Gera token para usuário"""
    import string
    import random
    return ''.join(random.choices(string.ascii_letters + string.digits, k=64))

@app.route('/api/check-token-requests', methods=['POST'])
def check_token_requests():
    """Verificar emails de solicitação de token automaticamente"""
    # Verificar se há emails para o admin com assunto "token"
    admin_emails = get_user_emails(ADMIN_EMAIL, 'inbox')
    
    new_requests = 0
    for email in admin_emails:
        try:
            if not email.get('read') and 'token' in email.get('subject', '').lower():
                # Processar solicitação de token
                request_id = generate_token_request_id()
                
                # Salvar solicitação
                token_requests[request_id] = {
                    'email_id': email['id'],
                    'from_email': email['from'],
                    'request_time': datetime.now().isoformat(),
                    'processed': False
                }
                
                # Gerar URL do token
                token_url = f"{request.host_url}token?{request_id}?sistem"
                
                # Enviar resposta com link
                response_email = {
                    'id': str(uuid.uuid4()),
                    'from': ADMIN_EMAIL,
                    'to': email['from'],
                    'subject': f"✅ Link para Gerar Token - Sistema Gmail",
                    'body': f"""
Olá!

Recebemos sua solicitação para gerar um token de conta.

🔗 Para gerar seu token, acesse o link abaixo:
{token_url}

📋 INSTRUÇÕES:
• Clique no link acima
• Preencha suas informações de conta
• Seu token será gerado automaticamente
• Use o token para integrar com nossa API

⚠️ IMPORTANTE:
• Este link é pessoal e intransferível
• Válido por 24 horas
• Mantenha seu token em segurança

📧 Sistema Gmail Independente
🆔 ID da Solicitação: {request_id[:8]}

---
Este é um email automático do sistema.
                    """.strip(),
                    'date': datetime.now().isoformat(),
                    'read': False,
                    'starred': False,
                    'folder': 'inbox',
                    'token_response': True,
                    'request_id': request_id
                }
                
                emails_db.append(response_email)
                
                # Marcar email original como lido
                email['read'] = True
                
                new_requests += 1
                
        except Exception as e:
            print(f"Erro ao processar solicitação de token: {e}")
            continue
    
    if new_requests > 0:
        save_data()
    
    return jsonify({
        'success': True,
        'new_requests': new_requests,
        'message': f'{new_requests} novas solicitações processadas'
    })

@app.route('/token')
def token_page():
    """Página de geração de token"""
    # Extrair request_id da URL
    full_path = request.full_path
    if '?' in full_path:
        parts = full_path.split('?')
        if len(parts) >= 3 and parts[2] == 'sistem':
            request_id = parts[1]
            
            # Verificar se solicitação existe
            if request_id in token_requests:
                return send_from_directory('.', 'token-generator.html')
            else:
                return f"""
                <h1>❌ Link Inválido</h1>
                <p>Este link de geração de token não é válido ou já expirou.</p>
                <p><a href="/login.html">Voltar ao Login</a></p>
                """, 404
        else:
            return f"""
            <h1>⚠️ URL Malformada</h1>
            <p>O formato correto é: /token?ID?sistem</p>
            <p><a href="/login.html">Voltar ao Login</a></p>
            """, 400
    else:
        return f"""
        <h1>⚠️ Parâmetros Faltando</h1>
        <p>Esta página requer parâmetros específicos.</p>
        <p><a href="/login.html">Voltar ao Login</a></p>
        """, 400

@app.route('/api/generate-token', methods=['POST'])
def generate_account_token():
    """Gerar token para usuário"""
    data = request.get_json()
    
    # Extrair request_id da URL atual (passado pelo frontend)
    request_id = data.get('request_id')
    email = data.get('email')
    password = data.get('password')
    name = data.get('name')
    account_id = data.get('account_id')
    
    if not all([request_id, email, password, name]):
        return jsonify({'error': 'Todos os campos são obrigatórios'}), 400
    
    # Verificar se solicitação existe
    if request_id not in token_requests:
        return jsonify({'error': 'Solicitação de token inválida'}), 404
    
    # Verificar se usuário existe e senha está correta
    if email not in users_db:
        return jsonify({'error': 'Usuário não encontrado'}), 404
    
    user = users_db[email]
    if user['password'] != hashlib.md5(password.encode()).hexdigest():
        return jsonify({'error': 'Senha incorreta'}), 401
    
    # Verificar se email da solicitação corresponde ao usuário
    token_request = token_requests[request_id]
    if token_request['from_email'] != email:
        return jsonify({'error': 'Email não corresponde à solicitação'}), 403
    
    # Gerar token
    user_token = generate_user_token()
    
    # Salvar token gerado
    generated_tokens[user_token] = {
        'user_email': email,
        'user_name': name,
        'user_id': user['user_id'],
        'account_id': account_id or user['user_id'],
        'generated_at': datetime.now().isoformat(),
        'request_id': request_id,
        'active': True
    }
    
    # Marcar solicitação como processada
    token_requests[request_id]['processed'] = True
    token_requests[request_id]['token_generated'] = user_token
    
    # Enviar confirmação por email
    confirmation_email = {
        'id': str(uuid.uuid4()),
        'from': ADMIN_EMAIL,
        'to': email,
        'subject': f"🎉 Token Gerado com Sucesso - Sistema Gmail",
        'body': f"""
Olá {name}!

Seu token de conta foi gerado com sucesso!

🔑 SEU TOKEN:
{user_token}

📋 INFORMAÇÕES DO TOKEN:
• Nome: {name}
• Email: {email}
• ID da Conta: {account_id or user['user_id']}
• Gerado em: {datetime.now().strftime('%d/%m/%Y às %H:%M')}

🚀 COMO USAR:
1. Inclua o token no cabeçalho das requisições:
   Authorization: Bearer {user_token}

2. Ou use como parâmetro:
   ?token={user_token}

⚠️ SEGURANÇA:
• Mantenha este token em segurança
• Não compartilhe com terceiros
• Use apenas em aplicações confiáveis

📧 Sistema Gmail Independente
🆔 ID do Token: {user_token[:8]}...

---
Este token é válido e pode ser usado para acessar nossa API.
        """.strip(),
        'date': datetime.now().isoformat(),
        'read': False,
        'starred': True,
        'folder': 'inbox',
        'token_confirmation': True,
        'user_token': user_token
    }
    
    emails_db.append(confirmation_email)
    save_data()
    
    return jsonify({
        'success': True,
        'message': 'Token gerado com sucesso',
        'token': user_token,
        'user_info': {
            'name': name,
            'email': email,
            'user_id': user['user_id'],
            'account_id': account_id or user['user_id']
        }
    })

@app.route('/api/validate-token-request')
def validate_token_request():
    """Validar solicitação de token"""
    request_id = request.args.get('request_id')
    
    if not request_id:
        return jsonify({'error': 'ID da solicitação é obrigatório'}), 400
    
    if request_id not in token_requests:
        return jsonify({'error': 'Solicitação não encontrada'}), 404
    
    token_request = token_requests[request_id]
    
    return jsonify({
        'valid': True,
        'from_email': token_request['from_email'],
        'request_time': token_request['request_time'],
        'processed': token_request.get('processed', False)
    })

@app.route('/api/list-user-tokens')
def list_user_tokens():
    """Listar tokens do usuário atual"""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Usuário não logado'}), 401
    
    user_email = session.get('user_email')
    user_tokens = []
    
    for token, token_data in generated_tokens.items():
        if token_data['user_email'] == user_email and token_data.get('active', True):
            user_tokens.append({
                'token_preview': f"{token[:8]}...{token[-8:]}",
                'generated_at': token_data['generated_at'],
                'account_id': token_data.get('account_id'),
                'active': token_data.get('active', True)
            })
    
    return jsonify({
        'success': True,
        'tokens': user_tokens,
        'total': len(user_tokens)
    })

if __name__ == '__main__':
    print("📧 Sistema Gmail Independente iniciado!")
    print(f"👑 Admin: {ADMIN_EMAIL} (senha: admin123)")
    print(f"📬 Emails carregados: {len(emails_db)}")
    print(f"👥 Usuários registrados: {len(users_db)}")
    print(f"🔑 Sistema de Token de Conta ativo!")
    print(f"📝 Para solicitar token: envie email para {ADMIN_EMAIL} com assunto 'token'")
    print(f"🌐 Acesse: http://0.0.0.0:5000")
    
    app.run(host='0.0.0.0', port=5000, debug=True)
