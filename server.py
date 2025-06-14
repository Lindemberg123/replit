
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
# Configurar CORS para produção
CORS(app, supports_credentials=True, origins=["*"])
app.secret_key = 'gmail-system-secret-key-2024'

# Configurações do sistema
USERS_FILE = 'users.json'
EMAILS_FILE = 'emails.json'
ADMIN_EMAIL = 'admin@nayemail.com'

# Sistema de domínios personalizados
MAIN_DOMAIN = 'nayemail.com'
BUSINESS_DOMAIN = 'nay.com'

# Categorias de emails
EMAIL_CATEGORIES = {
    'primary': 'Principal',
    'social': 'Social',
    'promotions': 'Promoções',
    'updates': 'Atualizações',
    'forums': 'Fóruns',
    'work': 'Trabalho',
    'personal': 'Pessoal'
}

# Configurações de funcionalidades
FEATURES = {
    'smart_compose': True,
    'smart_reply': True,
    'snooze': True,
    'schedule_send': True,
    'undo_send': True,
    'confidential_mode': True,
    'offline_mode': True,
    'multiple_inboxes': True,
    'filters': True,
    'labels': True,
    'attachments': True,
    'themes': True
}
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
        'name': 'Administrador NayEmail',
        'password': hashlib.md5('admin123'.encode()).hexdigest(),
        'created_at': datetime.now().isoformat() if ADMIN_EMAIL not in users_db else users_db[ADMIN_EMAIL].get('created_at', datetime.now().isoformat()),
        'profile_pic': 'https://ui-avatars.com/api/?name=NayEmail+Admin&background=6c63ff&color=fff',
        'is_admin': True,
        'user_id': 'admin_001',
        'theme': 'default',
        'language': 'pt-BR',
        'signature': 'Administrador NayEmail\nSistema de Email Inteligente'
    }
    save_data()

def create_demo_emails():
    """Criar emails de demonstração para conta demo"""
    demo_email = 'vídeo@n'
    
    # Verificar se já existem emails demo
    existing_demo = [e for e in emails_db if e.get('to') == demo_email or e.get('demo_email')]
    if len(existing_demo) > 0:
        return
    
    demo_emails = [
        {
            'id': str(uuid.uuid4()),
            'from': 'sistema@nayemail.com',
            'to': demo_email,
            'subject': '🎉 Bem-vindo ao NayEmail!',
            'body': '''Olá!

Bem-vindo ao Sistema NayEmail - a nova geração de emails inteligentes!

🚀 PRINCIPAIS FUNCIONALIDADES:
• IA Conversacional integrada
• Verificação avançada de segurança
• Templates inteligentes
• Sincronização multi-dispositivo
• Interface moderna e responsiva

🤖 EXPERIMENTE A IA:
Clique no banner da IA para conversar com nossa assistente inteligente.

📧 COMPOSE INTELIGENTE:
Use nossos templates e sugestões de IA para escrever emails profissionais.

💡 DICA: Explore todas as funcionalidades usando os menus laterais!

Bem-vindo à revolução dos emails!

Sistema NayEmail
            ''',
            'date': datetime.now().isoformat(),
            'read': False,
            'starred': True,
            'folder': 'inbox',
            'highlighted': True,
            'demo_email': True
        },
        {
            'id': str(uuid.uuid4()),
            'from': 'verificacao@empresademo.nay.com',
            'to': demo_email,
            'subject': '🔐 Código de Verificação - Empresa Demo',
            'body': '''Olá!

Seu código de verificação é: 123456

Este código é válido por 10 minutos.

Se você não solicitou esta verificação, ignore este email.

Atenciosamente,
Empresa Demo
Sistema de Verificação Automática
            ''',
            'date': (datetime.now() - timedelta(minutes=5)).isoformat(),
            'read': False,
            'starred': False,
            'folder': 'inbox',
            'verification': True,
            'verification_advanced': True,
            'verification_type': 'account',
            'verification_priority': 'high',
            'demo_email': True
        },
        {
            'id': str(uuid.uuid4()),
            'from': 'IA@nayemail.com',
            'to': demo_email,
            'subject': '🤖 Sua Assistente IA está pronta!',
            'body': '''Olá!

A NayAI, sua assistente inteligente, está configurada e pronta para uso!

💬 COMO USAR:
• Clique no banner da IA na interface principal
• Ou envie um email para IA@nayemail.com
• Faça perguntas sobre o sistema
• Peça ajuda com emails
• Tenha conversas naturais

🎯 EXEMPLOS DO QUE POSSO FAZER:
• Explicar funcionalidades do sistema
• Ajudar a compor emails
• Responder dúvidas técnicas
• Dar dicas de produtividade
• Conversar sobre qualquer assunto

Estou aqui para ajudar 24/7!

NayAI - Assistente Inteligente
Powered by NayEmail System
            ''',
            'date': (datetime.now() - timedelta(hours=1)).isoformat(),
            'read': False,
            'starred': False,
            'folder': 'inbox',
            'ai_chat_log': True,
            'demo_email': True
        }
    ]
    
    emails_db.extend(demo_emails)
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
    
    # Verificar se emails_db existe e é uma lista
    if not emails_db or not isinstance(emails_db, list):
        print(f"emails_db não inicializado corretamente: {type(emails_db)}")
        return []
    
    for email in emails_db:
        try:
            # Verificar se email é um dicionário válido
            if not isinstance(email, dict):
                continue
                
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
    
    try:
        return sorted(user_emails, key=lambda x: x.get('date', ''), reverse=True)
    except Exception as e:
        print(f"Erro ao ordenar emails: {e}")
        return user_emails

# Inicializar dados
load_data()
load_companies_data()
create_admin_user()
create_demo_emails()

@app.route('/')
def index():
    """Página principal com verificação de login"""
    user = get_current_user()
    if not user:
        return redirect('/login.html')
    
    # Verificar se é conta demo e deve mostrar trailer
    if user.get('demo_account') and user.get('show_trailer'):
        return send_from_directory('.', 'trailer-demo.html')
    
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
    
    # Verificar se conta está banida
    if user.get('disabled', False):
        return jsonify({'error': 'Sua conta foi banida. Entre em contato com o suporte.', 'banned': True}), 403
    
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
    try:
        user = get_current_user()
        if not user:
            return jsonify({'error': 'Usuário não logado'}), 401
        
        user_email = session.get('user_email')
        
        # Garantir que emails_db está inicializado
        if not emails_db:
            print("emails_db não inicializado, carregando dados...")
            load_data()
        
        # Calcular contadores com tratamento de erro
        try:
            inbox_count = len([e for e in get_user_emails(user_email, 'inbox') if not e.get('read')])
            sent_count = len(get_user_emails(user_email, 'sent'))
            drafts_count = len(get_user_emails(user_email, 'drafts'))
        except Exception as e:
            print(f"Erro ao calcular contadores: {e}")
            inbox_count = sent_count = drafts_count = 0
        
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
    except Exception as e:
        print(f"Erro em get_user_info: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

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
            'last_login': user_data.get('last_login', 'Nunca'),
            'disabled': user_data.get('disabled', False)
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
    
    # Verificar se conta está banida
    if user.get('disabled', False):
        return jsonify({'error': 'Conta banida', 'banned': True}), 403
    
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

@app.route('/ai-chat')
def ai_chat_page():
    """Página de chat com IA"""
    chat_id = request.args.get('chat_id')
    if not chat_id:
        return "ID da conversa não fornecido", 400
    return send_from_directory('.', 'ai-chat.html')

@app.route('/trailer-demo.html')
def trailer_demo_page():
    """Página de trailer/demo do sistema"""
    return send_from_directory('.', 'trailer-demo.html')

@app.route('/api/ai-chat', methods=['POST'])
def ai_chat_api():
    """API para chat com IA"""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Usuário não logado'}), 401
    
    data = request.get_json()
    chat_id = data.get('chat_id')
    user_message = data.get('message')
    close_chat = data.get('close_chat', False)
    
    if not chat_id or not user_message:
        return jsonify({'error': 'Chat ID e mensagem são obrigatórios'}), 400
    
    # Detectar comando para fechar chat
    close_commands = ['fechar', 'finalizar', 'encerrar', 'sair', 'terminar', 'acabar', 'fim', 'tchau', 'bye']
    should_close = close_chat or any(cmd in user_message.lower() for cmd in close_commands)
    
    # Salvar mensagem do usuário
    save_chat_message(chat_id, user['email'], 'user', user_message)
    
    # Gerar resposta da IA
    ai_response = generate_ai_response(user_message, should_close)
    
    # Salvar resposta da IA
    save_chat_message(chat_id, 'IA@nayemail.com', 'ai', ai_response)
    
    # Se deve fechar, gerar e enviar relatório
    if should_close:
        try:
            generate_and_send_chat_transcript(user, chat_id)
        except Exception as e:
            print(f"Erro ao gerar relatório: {e}")
    
    # Enviar email para IA sobre a nova mensagem
    send_ai_notification_email(user, chat_id, user_message, ai_response)
    
    return jsonify({
        'success': True,
        'ai_response': ai_response,
        'chat_id': chat_id,
        'close_chat': should_close
    })

def generate_ai_response(user_message, should_close=False):
    """Gera resposta inteligente baseada na mensagem do usuário"""
    message_lower = user_message.lower()
    
    # Detectar comando para fechar chat
    if should_close or any(word in message_lower for word in ['fechar', 'finalizar', 'encerrar', 'sair', 'terminar', 'acabar', 'fim', 'tchau', 'bye']):
        return "🔄 Entendido! Finalizando nossa conversa e enviando relatório completo por email. Obrigada por usar a NayAI! 👋"
    
    # Perguntas sobre o sistema NayEmail
    elif any(word in message_lower for word in ['sistema', 'nayemail', 'funcionalidade', 'como usar', 'rotas', 'acesso']):
        system_responses = [
            "📧 O NayEmail é um sistema completo de emails! Principais funcionalidades:\n• Envio e recebimento de emails\n• Organização por pastas\n• Sistema de favoritos\n• Chat com IA (eu!)\n• Painel administrativo\n• Verificações de segurança\n\nQual funcionalidade específica te interessa?",
            "🎯 Sobre o sistema NayEmail posso explicar:\n• Para enviar emails: use o botão 'Escrever'\n• Para organizar: arraste emails para pastas\n• Para conversar comigo: clique no banner da IA\n• Admin: acesse com admin@nayemail.com\n\nPrecisa de ajuda com algo específico?",
            "⚡ O NayEmail tem muitas funcionalidades:\n• Emails com verificação avançada\n• Sistema de tokens para API\n• Chat inteligente (comigo!)\n• Temas personalizáveis\n• Modo offline\n• Filtros automáticos\n\nSobre qual quer saber mais?"
        ]
        import random
        return random.choice(system_responses)
    
    # Respostas contextuais
    elif any(word in message_lower for word in ['olá', 'oi', 'hello', 'hey']):
        responses = [
            "Olá! 👋 Sou a NayAI, assistente do sistema NayEmail. Como posso ajudar você hoje?",
            "Oi! 😊 Bem-vindo ao chat com a NayAI! Posso ajudar com dúvidas sobre o sistema ou só conversar.",
            "Hey! 🤖 Sou sua assistente inteligente do NayEmail. Em que posso ser útil?"
        ]
    elif any(word in message_lower for word in ['ajuda', 'help', 'socorro', 'duvida', 'dúvida']):
        responses = [
            "🆘 Claro! Posso ajudar com:\n• Como usar o NayEmail\n• Enviar/receber emails\n• Funcionalidades do sistema\n• Ou qualquer dúvida!\n\nO que precisa saber?",
            "💡 Estou aqui para ajudar! Sou especialista em:\n• Sistema NayEmail\n• Envio de emails\n• Organização de mensagens\n• Funcionalidades avançadas\n\nQual sua dúvida?",
            "🚀 Sempre pronta para ajudar! Posso explicar sobre:\n• Como navegar no sistema\n• Recursos disponíveis\n• Dicas e truques\n• Resolução de problemas\n\nMe conte o que precisa!"
        ]
    elif any(word in message_lower for word in ['email', 'e-mail', 'gmail', 'enviar', 'receber']):
        responses = [
            "📬 Sobre emails no NayEmail:\n• Para enviar: clique em 'Escrever'\n• Para organizar: use as pastas da barra lateral\n• Para favoritar: clique na estrela\n• Para buscar: use a caixa de pesquisa\n\nQual operação específica quer fazer?",
            "✉️ O sistema de emails é bem completo:\n• Caixa de entrada, enviados, rascunhos\n• Sistema de estrelas e destaques\n• Verificações de segurança\n• Recuperação de senha\n\nPrecisa de ajuda com alguma função?",
            "📧 No NayEmail você pode:\n• Compor emails ricos\n• Agendar envios\n• Usar respostas inteligentes\n• Organizar por categorias\n• Fazer backup das conversas\n\nQuer saber como fazer algo específico?"
        ]
    elif any(word in message_lower for word in ['obrigado', 'obrigada', 'thanks', 'valeu', 'brigadão']):
        responses = [
            "😊 De nada! Fico feliz em ajudar com o NayEmail. Se tiver mais dúvidas, é só chamar!",
            "🌟 Por nada! É um prazer ser sua assistente. Estou sempre aqui quando precisar!",
            "💙 Que bom que pude ajudar! Continue explorando o NayEmail, tem muitas funcionalidades legais!"
        ]
    elif any(word in message_lower for word in ['tchau', 'bye', 'até', 'fui', 'xau']):
        responses = [
            "👋 Até logo! Foi ótimo conversar com você. Volte sempre que quiser usar a NayAI!",
            "😊 Tchau! Estarei aqui quando precisar de ajuda com o NayEmail. Tenha um ótimo dia!",
            "🌟 Até mais! Espero ter ajudado. Continue aproveitando o sistema NayEmail!"
        ]
    elif '?' in user_message:
        responses = [
            "🤔 Interessante pergunta! Vou fazer o meu melhor para responder sobre o NayEmail ou qualquer dúvida que tenha.",
            "💭 Boa pergunta! Como assistente do NayEmail, posso ajudar com informações do sistema ou outras questões.",
            "🧠 Deixe-me pensar na melhor resposta... Sobre o que especificamente quer saber?"
        ]
    else:
        responses = [
            "💭 Interessante! Pode me contar mais? Sou especialista no NayEmail e adoro conversar!",
            "😊 Entendi! Como posso ajudar melhor? Posso explicar sobre o sistema ou só bater papo.",
            "🤝 Compreendo. Há algo específico sobre o NayEmail que posso esclarecer?",
            "✨ Legal! Quer saber algo sobre o sistema de emails ou prefere conversar sobre outro assunto?",
            "🎯 Entendo seu ponto! Como assistente do NayEmail, posso ajudar com qualquer dúvida do sistema."
        ]
    
    import random
    return random.choice(responses)

def save_chat_message(chat_id, user_email, sender_type, message):
    """Salva mensagem do chat em arquivo"""
    chat_data = {
        'chat_id': chat_id,
        'user_email': user_email,
        'sender_type': sender_type,
        'message': message,
        'timestamp': datetime.now().isoformat()
    }
    
    # Carregar conversas existentes
    chat_file = 'ai_chats.json'
    chats = []
    if os.path.exists(chat_file):
        with open(chat_file, 'r', encoding='utf-8') as f:
            chats = json.load(f)
    
    chats.append(chat_data)
    
    # Salvar de volta
    with open(chat_file, 'w', encoding='utf-8') as f:
        json.dump(chats, f, ensure_ascii=False, indent=2)

def generate_and_send_chat_transcript(user, chat_id):
    """Gerar e enviar relatório completo da conversa"""
    try:
        # Carregar todas as mensagens do chat
        chat_file = 'ai_chats.json'
        all_chats = []
        if os.path.exists(chat_file):
            with open(chat_file, 'r', encoding='utf-8') as f:
                all_chats = json.load(f)
        
        # Filtrar mensagens deste chat específico
        chat_messages = [msg for msg in all_chats if msg.get('chat_id') == chat_id]
        chat_messages.sort(key=lambda x: x.get('timestamp', ''))
        
        if not chat_messages:
            return
        
        # Gerar relatório detalhado
        start_time = chat_messages[0]['timestamp'] if chat_messages else datetime.now().isoformat()
        end_time = chat_messages[-1]['timestamp'] if chat_messages else datetime.now().isoformat()
        total_messages = len(chat_messages)
        
        # Criar transcript formatado
        transcript_lines = []
        for msg in chat_messages:
            timestamp = datetime.fromisoformat(msg['timestamp']).strftime('%H:%M:%S')
            sender_icon = '👤' if msg['sender_type'] == 'user' else '🤖'
            sender_name = user['name'] if msg['sender_type'] == 'user' else 'NayAI'
            transcript_lines.append(f"[{timestamp}] {sender_icon} {sender_name}: {msg['message']}")
        
        transcript_text = '\n\n'.join(transcript_lines)
        
        # Calcular estatísticas
        user_messages = [msg for msg in chat_messages if msg['sender_type'] == 'user']
        ai_messages = [msg for msg in chat_messages if msg['sender_type'] == 'ai']
        
        chat_duration = "N/A"
        if len(chat_messages) >= 2:
            start_dt = datetime.fromisoformat(start_time)
            end_dt = datetime.fromisoformat(end_time)
            duration_seconds = (end_dt - start_dt).total_seconds()
            chat_duration = f"{int(duration_seconds // 60)}m {int(duration_seconds % 60)}s"
        
        # Corpo do email do relatório
        report_body = f"""
📊 RELATÓRIO COMPLETO DA CONVERSA COM NAYAI

╔══════════════════════════════════════════════════════════════╗
║                    📋 INFORMAÇÕES GERAIS                     ║
╚══════════════════════════════════════════════════════════════╝

👤 Usuário: {user['name']} ({user['email']})
🆔 ID da Conversa: {chat_id}
📅 Data de início: {datetime.fromisoformat(start_time).strftime('%d/%m/%Y')}
⏰ Horário de início: {datetime.fromisoformat(start_time).strftime('%H:%M:%S')}
⏰ Horário de término: {datetime.fromisoformat(end_time).strftime('%H:%M:%S')}
⏱️ Duração total: {chat_duration}

╔══════════════════════════════════════════════════════════════╗
║                     📈 ESTATÍSTICAS                          ║
╚══════════════════════════════════════════════════════════════╝

💬 Total de mensagens: {total_messages}
👤 Mensagens do usuário: {len(user_messages)}
🤖 Respostas da IA: {len(ai_messages)}
📊 Taxa de resposta: {len(ai_messages)/len(user_messages)*100:.1f}% (IA sempre responde)

╔══════════════════════════════════════════════════════════════╗
║                  💬 TRANSCRIPT COMPLETO                      ║
╚══════════════════════════════════════════════════════════════╝

{transcript_text}

╔══════════════════════════════════════════════════════════════╗
║                     📝 RESUMO FINAL                          ║
╚══════════════════════════════════════════════════════════════╝

✅ Conversa finalizada com sucesso
📧 Relatório gerado automaticamente
🔒 Dados salvos com segurança
🤖 NayAI sempre disponível para novas conversas

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 COMO INICIAR NOVA CONVERSA:
• Clique no banner da IA no sistema
• Ou envie email para IA@nayemail.com
• IA sempre pronta para ajudar!

📧 Relatório gerado pelo Sistema NayEmail
🆔 ID do Relatório: {str(uuid.uuid4())[:8]}
📅 Gerado em: {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}

        """.strip()
        
        # Enviar relatório por email
        report_email = {
            'id': str(uuid.uuid4()),
            'from': 'sistema@nayemail.com',
            'to': user['email'],
            'subject': f"📊 Relatório Completo - Conversa NayAI ({chat_id[:8]})",
            'body': report_body,
            'date': datetime.now().isoformat(),
            'read': False,
            'starred': True,
            'folder': 'inbox',
            'chat_transcript': True,
            'chat_id': chat_id,
            'priority': 'high'
        }
        
        emails_db.append(report_email)
        save_data()
        
        print(f"Relatório de chat enviado para {user['email']}: {chat_id}")
        
    except Exception as e:
        print(f"Erro ao gerar relatório de chat: {e}")

def send_ai_notification_email(user, chat_id, user_message, ai_response):
    """Enviar notificação para a IA sobre nova mensagem"""
    try:
        ai_email = {
            'id': str(uuid.uuid4()),
            'from': 'sistema@nayemail.com',
            'to': 'IA@nayemail.com',
            'subject': f'💬 Nova conversa com {user["name"]} - Chat {chat_id[:8]}',
            'body': f"""
🤖 NOVA INTERAÇÃO COM IA

👤 Usuário: {user['name']} ({user['email']})
🆔 Chat ID: {chat_id}
📅 Data: {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}

💬 MENSAGEM DO USUÁRIO:
{user_message}

🤖 RESPOSTA DA IA:
{ai_response}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 ESTATÍSTICAS:
• Status: Conversa ativa
• Plataforma: NayEmail IA Assistant
• Tipo: Chat em tempo real

🔗 Sistema NayEmail - IA Conversacional
            """.strip(),
            'date': datetime.now().isoformat(),
            'read': False,
            'starred': False,
            'folder': 'inbox',
            'ai_chat_log': True,
            'chat_id': chat_id
        }
        
        emails_db.append(ai_email)
        save_data()
        
    except Exception as e:
        print(f"Erro ao enviar notificação para IA: {e}")

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

@app.route('/api/revoke-token', methods=['POST'])
def revoke_token():
    """Revogar/desativar um token de acesso"""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Usuário não logado'}), 401
    
    data = request.get_json()
    token_preview = data.get('token_preview')  # Formato: "abc12345...xyz67890"
    
    if not token_preview:
        return jsonify({'error': 'Preview do token é obrigatório'}), 400
    
    user_email = session.get('user_email')
    revoked_count = 0
    
    # Encontrar e desativar token baseado no preview
    for token, token_data in generated_tokens.items():
        if (token_data['user_email'] == user_email and 
            token_preview == f"{token[:8]}...{token[-8:]}"):
            
            token_data['active'] = False
            token_data['revoked_at'] = datetime.now().isoformat()
            revoked_count += 1
            break
    
    if revoked_count > 0:
        save_data()
        return jsonify({
            'success': True,
            'message': 'Token revogado com sucesso'
        })
    else:
        return jsonify({'error': 'Token não encontrado'}), 404

@app.route('/api/mark-trailer-seen', methods=['POST'])
def mark_trailer_seen():
    """Marcar trailer como visto para conta demo"""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Usuário não logado'}), 401
    
    user_email = session.get('user_email')
    if user_email in users_db and users_db[user_email].get('demo_account'):
        users_db[user_email]['show_trailer'] = False
        users_db[user_email]['trailer_seen_at'] = datetime.now().isoformat()
        save_data()
        
        return jsonify({
            'success': True,
            'message': 'Trailer marcado como visto'
        })
    
    return jsonify({'error': 'Conta não é demo'}), 400

@app.route('/api/login-with-token', methods=['POST'])
def login_with_token():
    """Login usando token de acesso com verificação de captcha"""
    data = request.get_json()
    token = data.get('token')
    captcha_verified = data.get('captcha_verified', False)
    
    if not token:
        return jsonify({'error': 'Token é obrigatório'}), 400
    
    if not captcha_verified:
        return jsonify({'error': 'Verificação de segurança não completada'}), 400
    
    # Verificar se token existe e está ativo
    if token not in generated_tokens:
        return jsonify({'error': 'Token inválido ou não encontrado'}), 401
    
    token_data = generated_tokens[token]
    
    if not token_data.get('active', True):
        return jsonify({'error': 'Token foi desativado'}), 401
    
    # Verificar se usuário ainda existe
    user_email = token_data['user_email']
    if user_email not in users_db:
        return jsonify({'error': 'Usuário associado ao token não existe mais'}), 404
    
    user = users_db[user_email]
    
    # Criar sessão
    session['user_id'] = user['user_id']
    session['user_email'] = user_email
    session['is_admin'] = user.get('is_admin', False)
    session['login_method'] = 'token'
    session['token_used'] = token[:16] + '...'  # Registrar parte do token usado
    
    # Atualizar último login
    user['last_login'] = datetime.now().isoformat()
    
    # Registrar uso do token
    token_data['last_used'] = datetime.now().isoformat()
    token_data['usage_count'] = token_data.get('usage_count', 0) + 1
    
    save_data()
    
    print(f"Login por token realizado: {user_email}, Admin: {user.get('is_admin', False)}, Token: {token[:8]}...")
    
    # Enviar email de notificação de login por token
    login_notification = {
        'id': str(uuid.uuid4()),
        'from': 'sistema@gmail.oficial',
        'to': user_email,
        'subject': f"🔐 Login por Token Realizado - {datetime.now().strftime('%d/%m/%Y %H:%M')}",
        'body': f"""
Olá {user['name']}!

Um login foi realizado em sua conta usando um token de acesso.

📋 DETALHES DO LOGIN:
• Data: {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}
• Método: Token de Acesso
• Token usado: {token[:8]}...{token[-8:]}
• Verificação: Re-captcha aprovado
• ID da Conta: {user['user_id']}

🔒 SEGURANÇA:
• Se não foi você, altere sua senha imediatamente
• Considere revogar tokens desnecessários
• Monitore atividades suspeitas em sua conta

📧 Este é um email automático do Sistema Gmail Independente
🆔 ID da Sessão: {session.get('user_id')}

---
Para sua segurança, sempre verifique logins não autorizados.
        """.strip(),
        'date': datetime.now().isoformat(),
        'read': False,
        'starred': False,
        'folder': 'inbox',
        'token_login_notification': True,
        'security_alert': True
    }
    
    emails_db.append(login_notification)
    save_data()
    
    return jsonify({
        'success': True,
        'message': 'Login por token realizado com sucesso',
        'user': {
            'email': user_email,
            'name': user['name'],
            'user_id': user['user_id'],
            'is_admin': user.get('is_admin', False)
        },
        'login_method': 'token',
        'token_info': {
            'preview': f"{token[:8]}...{token[-8:]}",
            'last_used': token_data['last_used'],
            'usage_count': token_data['usage_count']
        }
    })

# Novas funcionalidades para NayEmail
@app.route('/api/categories')
def get_categories():
    """Obter categorias de email"""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Usuário não logado'}), 401
    
    return jsonify(EMAIL_CATEGORIES)

@app.route('/api/email/<email_id>/categorize', methods=['POST'])
def categorize_email(email_id):
    """Categorizar email"""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Usuário não logado'}), 401
    
    data = request.get_json()
    category = data.get('category')
    
    if category not in EMAIL_CATEGORIES:
        return jsonify({'error': 'Categoria inválida'}), 400
    
    user_email = session.get('user_email')
    
    for email in emails_db:
        if email.get('id') == email_id and (email.get('to') == user_email or email.get('from') == user_email):
            email['category'] = category
            save_data()
            return jsonify({'success': True, 'category': category})
    
    return jsonify({'error': 'Email não encontrado'}), 404

@app.route('/api/email/<email_id>/snooze', methods=['POST'])
def snooze_email(email_id):
    """Adiar email"""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Usuário não logado'}), 401
    
    data = request.get_json()
    snooze_until = data.get('snooze_until')
    
    user_email = session.get('user_email')
    
    for email in emails_db:
        if email.get('id') == email_id and (email.get('to') == user_email or email.get('from') == user_email):
            email['snoozed'] = True
            email['snooze_until'] = snooze_until
            save_data()
            return jsonify({'success': True, 'snooze_until': snooze_until})
    
    return jsonify({'error': 'Email não encontrado'}), 404

@app.route('/api/schedule-email', methods=['POST'])
def schedule_email():
    """Agendar envio de email"""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Usuário não logado'}), 401
    
    data = request.get_json()
    schedule_time = data.get('schedule_time')
    
    if not schedule_time:
        return jsonify({'error': 'Horário de agendamento obrigatório'}), 400
    
    user_email = session.get('user_email')
    
    scheduled_email = {
        'id': str(uuid.uuid4()),
        'from': user_email,
        'to': data['to'],
        'subject': data['subject'],
        'body': data['body'],
        'scheduled_for': schedule_time,
        'status': 'scheduled',
        'created_at': datetime.now().isoformat()
    }
    
    # Salvar em arquivo de emails agendados
    scheduled_emails = []
    if os.path.exists('scheduled_emails.json'):
        with open('scheduled_emails.json', 'r', encoding='utf-8') as f:
            scheduled_emails = json.load(f)
    
    scheduled_emails.append(scheduled_email)
    
    with open('scheduled_emails.json', 'w', encoding='utf-8') as f:
        json.dump(scheduled_emails, f, ensure_ascii=False, indent=2)
    
    return jsonify({'success': True, 'scheduled_id': scheduled_email['id']})

@app.route('/api/smart-compose', methods=['POST'])
def smart_compose():
    """Composição inteligente de email"""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Usuário não logado'}), 401
    
    data = request.get_json()
    context = data.get('context', '')
    
    # Sugestões inteligentes baseadas no contexto
    suggestions = []
    
    if 'reunião' in context.lower() or 'meeting' in context.lower():
        suggestions = [
            "Vamos agendar uma reunião para discutir este assunto.",
            "Podemos marcar uma call para alinhar os detalhes?",
            "Que tal uma reunião presencial para definir os próximos passos?"
        ]
    elif 'obrigado' in context.lower() or 'thanks' in context.lower():
        suggestions = [
            "Obrigado pelo seu tempo e dedicação.",
            "Agradeço a atenção dispensada a este assunto.",
            "Muito obrigado pela colaboração."
        ]
    elif 'prazo' in context.lower() or 'deadline' in context.lower():
        suggestions = [
            "Precisamos alinhar o prazo para esta entrega.",
            "Qual seria um prazo realista para concluirmos?",
            "Podemos estender o deadline se necessário."
        ]
    else:
        suggestions = [
            "Espero que esteja tudo bem com você.",
            "Fico à disposição para qualquer esclarecimento.",
            "Aguardo seu retorno quando possível."
        ]
    
    return jsonify({'suggestions': suggestions})

@app.route('/api/smart-reply', methods=['POST'])
def smart_reply():
    """Respostas inteligentes"""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Usuário não logado'}), 401
    
    data = request.get_json()
    email_content = data.get('email_content', '').lower()
    
    # Gerar respostas inteligentes baseadas no conteúdo
    replies = []
    
    if 'pergunta' in email_content or '?' in email_content:
        replies = [
            "Sim, posso ajudar com isso.",
            "Deixe-me verificar e retorno em breve.",
            "Ótima pergunta! Vou pesquisar e te respondo."
        ]
    elif 'obrigado' in email_content or 'thanks' in email_content:
        replies = [
            "De nada! Fico feliz em ajudar.",
            "Por nada! Estou sempre à disposição.",
            "Foi um prazer ajudar!"
        ]
    elif 'urgente' in email_content or 'urgent' in email_content:
        replies = [
            "Entendi a urgência, vou priorizar este assunto.",
            "Vou tratar isso com prioridade máxima.",
            "Compreendo. Vou resolver isso imediatamente."
        ]
    else:
        replies = [
            "Obrigado pelo email!",
            "Recebi e vou analisar.",
            "Perfeito, entendi!"
        ]
    
    return jsonify({'replies': replies})

@app.route('/api/themes')
def get_themes():
    """Obter temas disponíveis"""
    themes = {
        'default': {
            'name': 'NayEmail Padrão',
            'primary_color': '#6c63ff',
            'secondary_color': '#4caf50',
            'background': '#ffffff',
            'text_color': '#333333'
        },
        'dark': {
            'name': 'Modo Escuro',
            'primary_color': '#bb86fc',
            'secondary_color': '#03dac6',
            'background': '#121212',
            'text_color': '#ffffff'
        },
        'blue': {
            'name': 'Azul Profissional',
            'primary_color': '#1976d2',
            'secondary_color': '#2196f3',
            'background': '#f5f5f5',
            'text_color': '#333333'
        },
        'green': {
            'name': 'Verde Natureza',
            'primary_color': '#388e3c',
            'secondary_color': '#4caf50',
            'background': '#e8f5e8',
            'text_color': '#2e7d32'
        }
    }
    
    return jsonify(themes)

@app.route('/api/user/theme', methods=['POST'])
def set_user_theme():
    """Definir tema do usuário"""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Usuário não logado'}), 401
    
    data = request.get_json()
    theme = data.get('theme', 'default')
    
    user_email = session.get('user_email')
    users_db[user_email]['theme'] = theme
    save_data()
    
    return jsonify({'success': True, 'theme': theme})

@app.route('/api/filters')
def get_filters():
    """Obter filtros do usuário"""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Usuário não logado'}), 401
    
    user_email = session.get('user_email')
    user_data = users_db.get(user_email, {})
    filters = user_data.get('filters', [])
    
    return jsonify(filters)

@app.route('/api/filters', methods=['POST'])
def create_filter():
    """Criar novo filtro"""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Usuário não logado'}), 401
    
    data = request.get_json()
    
    filter_config = {
        'id': str(uuid.uuid4()),
        'name': data.get('name'),
        'criteria': data.get('criteria'),  # from, subject, has_words, etc.
        'action': data.get('action'),      # mark_read, star, label, etc.
        'created_at': datetime.now().isoformat()
    }
    
    user_email = session.get('user_email')
    if 'filters' not in users_db[user_email]:
        users_db[user_email]['filters'] = []
    
    users_db[user_email]['filters'].append(filter_config)
    save_data()
    
    return jsonify({'success': True, 'filter': filter_config})

@app.route('/api/features')
def get_features():
    """Obter funcionalidades disponíveis"""
    return jsonify(FEATURES)

if __name__ == '__main__':
    print("📧 NayEmail - Sistema de Email Inteligente iniciado!")
    print(f"👑 Admin: {ADMIN_EMAIL} (senha: admin123)")
    print(f"📬 Emails carregados: {len(emails_db)}")
    print(f"👥 Usuários registrados: {len(users_db)}")
    print(f"🔑 Sistema de Token de Conta ativo!")
    print(f"🎨 Temas e funcionalidades avançadas disponíveis!")
    print(f"🤖 IA para composição inteligente ativa!")
    print(f"📝 Para solicitar token: envie email para {ADMIN_EMAIL} com assunto 'token'")
    print(f"🌐 Acesse: http://0.0.0.0:5000")
    
    app.run(host='0.0.0.0', port=5000, debug=True)
