
from flask import Flask, request, jsonify, send_from_directory
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
CONTACTS_FILE = 'contacts.json'

# Armazenamento em memória
current_user = None
users_db = {}
emails_db = []
contacts_db = []

def load_data():
    """Carrega dados dos arquivos JSON"""
    global users_db, emails_db, contacts_db
    
    # Carregar usuários
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r', encoding='utf-8') as f:
            users_db = json.load(f)
    
    # Carregar emails
    if os.path.exists(EMAILS_FILE):
        with open(EMAILS_FILE, 'r', encoding='utf-8') as f:
            emails_db = json.load(f)
    
    # Carregar contatos
    if os.path.exists(CONTACTS_FILE):
        with open(CONTACTS_FILE, 'r', encoding='utf-8') as f:
            contacts_db = json.load(f)

def save_data():
    """Salva dados nos arquivos JSON"""
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(users_db, f, ensure_ascii=False, indent=2)
    
    with open(EMAILS_FILE, 'w', encoding='utf-8') as f:
        json.dump(emails_db, f, ensure_ascii=False, indent=2)
    
    with open(CONTACTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(contacts_db, f, ensure_ascii=False, indent=2)

def create_sample_user():
    """Cria usuário de exemplo para demonstração"""
    sample_email = "usuario@gmail.com"
    if sample_email not in users_db:
        users_db[sample_email] = {
            'email': sample_email,
            'name': 'Usuário Exemplo',
            'password': hashlib.md5('123456'.encode()).hexdigest(),
            'created_at': datetime.now().isoformat(),
            'profile_pic': 'https://ui-avatars.com/api/?name=Usuario+Exemplo&background=4285f4&color=fff'
        }
        
        # Criar emails de exemplo
        sample_emails = [
            {
                'id': str(uuid.uuid4()),
                'from': 'contato@empresa.com',
                'to': sample_email,
                'subject': 'Bem-vindo ao nosso sistema!',
                'body': 'Olá! Bem-vindo ao nosso sistema de email. Esperamos que você tenha uma ótima experiência usando nossa plataforma.',
                'date': (datetime.now() - timedelta(hours=2)).isoformat(),
                'read': False,
                'starred': False,
                'folder': 'inbox'
            },
            {
                'id': str(uuid.uuid4()),
                'from': 'suporte@sistema.com',
                'to': sample_email,
                'subject': 'Configuração da sua conta',
                'body': 'Sua conta foi configurada com sucesso. Você já pode começar a usar todos os recursos disponíveis.',
                'date': (datetime.now() - timedelta(hours=5)).isoformat(),
                'read': False,
                'starred': True,
                'folder': 'inbox'
            },
            {
                'id': str(uuid.uuid4()),
                'from': sample_email,
                'to': 'cliente@exemplo.com',
                'subject': 'Resposta sobre o projeto',
                'body': 'Obrigado pelo seu interesse. Vamos analisar sua proposta e retornar em breve.',
                'date': (datetime.now() - timedelta(hours=1)).isoformat(),
                'read': True,
                'starred': False,
                'folder': 'sent'
            }
        ]
        
        emails_db.extend(sample_emails)
        save_data()

def get_user_emails(user_email, folder='inbox'):
    """Obtém emails do usuário por pasta"""
    user_emails = []
    for email in emails_db:
        if folder == 'inbox' and email['to'] == user_email:
            user_emails.append(email)
        elif folder == 'sent' and email['from'] == user_email:
            user_emails.append(email)
        elif folder == 'drafts' and email.get('folder') == 'drafts' and email['from'] == user_email:
            user_emails.append(email)
        elif folder == 'starred' and email.get('starred') and (email['to'] == user_email or email['from'] == user_email):
            user_emails.append(email)
    
    return sorted(user_emails, key=lambda x: x['date'], reverse=True)

def simulate_incoming_emails():
    """Simula recebimento de novos emails"""
    sample_senders = [
        'newsletter@empresa.com',
        'promocoes@loja.com',
        'suporte@sistema.com',
        'contato@parceiro.com'
    ]
    
    subjects = [
        'Novidades da semana',
        'Oferta especial para você',
        'Atualização importante',
        'Convite para evento'
    ]
    
    bodies = [
        'Confira as novidades desta semana em nosso site.',
        'Aproveite nossa oferta especial com desconto de 50%.',
        'Importante: Atualizamos nossos termos de uso.',
        'Você está convidado para nosso evento especial.'
    ]
    
    while True:
        try:
            time.sleep(60)  # Simula novo email a cada 60 segundos
            
            if users_db:
                user_email = list(users_db.keys())[0]
                
                new_email = {
                    'id': str(uuid.uuid4()),
                    'from': sample_senders[len(emails_db) % len(sample_senders)],
                    'to': user_email,
                    'subject': subjects[len(emails_db) % len(subjects)],
                    'body': bodies[len(emails_db) % len(bodies)],
                    'date': datetime.now().isoformat(),
                    'read': False,
                    'starred': False,
                    'folder': 'inbox'
                }
                
                emails_db.append(new_email)
                save_data()
                
        except Exception as e:
            print(f"Erro ao simular email: {e}")

# Inicializar dados
load_data()
create_sample_user()

# Thread para simular emails
email_thread = threading.Thread(target=simulate_incoming_emails, daemon=True)
email_thread.start()

@app.route('/')
def index():
    """Página principal"""
    return send_from_directory('.', 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    """Servir arquivos estáticos"""
    return send_from_directory('.', filename)

@app.route('/api/user-info')
def get_user_info():
    """Obter informações do usuário"""
    user_email = list(users_db.keys())[0] if users_db else "usuario@gmail.com"
    user = users_db.get(user_email, {})
    
    inbox_count = len(get_user_emails(user_email, 'inbox'))
    sent_count = len(get_user_emails(user_email, 'sent'))
    drafts_count = len(get_user_emails(user_email, 'drafts'))
    
    return jsonify({
        'email': user_email,
        'name': user.get('name', 'Usuário'),
        'inbox_count': inbox_count,
        'sent_count': sent_count,
        'drafts_count': drafts_count,
        'profile_pic': user.get('profile_pic', '')
    })

@app.route('/api/emails/<folder>')
def get_emails(folder):
    """Obter emails por pasta"""
    user_email = list(users_db.keys())[0] if users_db else "usuario@gmail.com"
    emails = get_user_emails(user_email, folder)
    return jsonify(emails)

@app.route('/api/email/<email_id>')
def get_email_detail(email_id):
    """Obter detalhes de um email específico"""
    for email in emails_db:
        if email['id'] == email_id:
            email['read'] = True
            save_data()
            return jsonify(email)
    
    return jsonify({'error': 'Email não encontrado'}), 404

@app.route('/api/send-email', methods=['POST'])
def send_email():
    """Enviar email"""
    data = request.get_json()
    
    if not data or not all(k in data for k in ['to', 'subject', 'body']):
        return jsonify({'error': 'Dados obrigatórios: to, subject, body'}), 400
    
    user_email = list(users_db.keys())[0] if users_db else "usuario@gmail.com"
    
    new_email = {
        'id': str(uuid.uuid4()),
        'from': user_email,
        'to': data['to'],
        'subject': data['subject'],
        'body': data['body'],
        'date': datetime.now().isoformat(),
        'read': True,
        'starred': False,
        'folder': 'sent'
    }
    
    emails_db.append(new_email)
    save_data()
    
    return jsonify({'success': True, 'message': 'Email enviado com sucesso'})

@app.route('/api/save-draft', methods=['POST'])
def save_draft():
    """Salvar rascunho"""
    data = request.get_json()
    user_email = list(users_db.keys())[0] if users_db else "usuario@gmail.com"
    
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
    global emails_db
    emails_db = [e for e in emails_db if e['id'] != email_id]
    save_data()
    
    return jsonify({'success': True, 'message': 'Email deletado'})

@app.route('/api/email/<email_id>/star', methods=['POST'])
def star_email(email_id):
    """Marcar/desmarcar email como favorito"""
    for email in emails_db:
        if email['id'] == email_id:
            email['starred'] = not email.get('starred', False)
            save_data()
            return jsonify({'success': True, 'starred': email['starred']})
    
    return jsonify({'error': 'Email não encontrado'}), 404

@app.route('/api/refresh-emails', methods=['POST'])
def refresh_emails():
    """Atualizar lista de emails"""
    user_email = list(users_db.keys())[0] if users_db else "usuario@gmail.com"
    inbox_emails = get_user_emails(user_email, 'inbox')
    
    return jsonify({'success': True, 'count': len(inbox_emails)})

@app.route('/api/search', methods=['POST'])
def search_emails():
    """Buscar emails"""
    data = request.get_json()
    query = data.get('query', '').lower()
    user_email = list(users_db.keys())[0] if users_db else "usuario@gmail.com"
    
    results = []
    for email in emails_db:
        if (email['to'] == user_email or email['from'] == user_email) and (
            query in email['subject'].lower() or 
            query in email['body'].lower() or 
            query in email['from'].lower()
        ):
            results.append(email)
    
    return jsonify(results)

if __name__ == '__main__':
    print("📧 Sistema Gmail Independente iniciado!")
    print(f"👤 Usuário exemplo: usuario@gmail.com")
    print(f"📬 Emails carregados: {len(emails_db)}")
    print(f"🌐 Acesse: http://0.0.0.0:5000")
    
    app.run(host='0.0.0.0', port=5000, debug=True)
