
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

@app.route('/<path:filename>')
def serve_static(filename):
    """Servir arquivos estáticos"""
    return send_from_directory('.', filename)

@app.route('/api/login', methods=['POST'])
def login():
    """Login do usuário"""
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({'error': 'Email e senha são obrigatórios'}), 400
    
    # Verificar se usuário existe
    if email not in users_db:
        # Não permitir criação automática de novos usuários
        # Apenas o admin já existe
        return jsonify({'error': 'Usuário não encontrado. Use suport.com@gmail.oficial para admin'}), 401
    
    # Verificar senha
    user = users_db[email]
    if user['password'] != hashlib.md5(password.encode()).hexdigest():
        return jsonify({'error': 'Senha incorreta'}), 401
    
    # Criar sessão
    session['user_id'] = user['user_id']
    session['user_email'] = email
    session['is_admin'] = user.get('is_admin', False)
    
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
    """API para sites externos enviarem emails de verificação"""
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
    
    # Criar email de verificação
    verification_email = {
        'id': str(uuid.uuid4()),
        'from': f"verificacao@{data['site_name'].lower().replace(' ', '')}.com",
        'to': to_email,
        'subject': f"Verificação de conta - {data['site_name']}",
        'body': f"""
Olá!

Você solicitou verificação de conta no site {data['site_name']}.

Seu código de verificação é: {data['verification_code']}

Ou clique no link abaixo para verificar automaticamente:
{data['verification_url']}

Se você não solicitou esta verificação, ignore este email.

Este email foi enviado através do Sistema Gmail Independente.
        """.strip(),
        'date': datetime.now().isoformat(),
        'read': False,
        'starred': False,
        'folder': 'inbox',
        'verification': True,
        'site_origin': data['site_name']
    }
    
    emails_db.append(verification_email)
    save_data()
    
    return jsonify({
        'success': True,
        'message': 'Email de verificação enviado',
        'email_id': verification_email['id']
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
    
    # Criar email de recuperação
    reset_email = {
        'id': str(uuid.uuid4()),
        'from': f"suporte@{data['site_name'].lower().replace(' ', '')}.com",
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
    
    # Criar email de notificação
    notification_email = {
        'id': str(uuid.uuid4()),
        'from': f"notificacoes@{data['site_name'].lower().replace(' ', '')}.com",
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

if __name__ == '__main__':
    print("📧 Sistema Gmail Independente iniciado!")
    print(f"👑 Admin: {ADMIN_EMAIL} (senha: admin123)")
    print(f"📬 Emails carregados: {len(emails_db)}")
    print(f"👥 Usuários registrados: {len(users_db)}")
    print(f"🌐 Acesse: http://0.0.0.0:5000")
    
    app.run(host='0.0.0.0', port=5000, debug=True)
