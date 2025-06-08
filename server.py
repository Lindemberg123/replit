
from flask import Flask, request, jsonify, send_from_directory, session, redirect, url_for
from flask_cors import CORS
import json
import os
import imaplib
import email
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from config import Config
import threading
import time

app = Flask(__name__)
CORS(app)
app.secret_key = Config.SECRET_KEY

# Configurações do Gmail
GMAIL_USER = Config.GMAIL_USER
GMAIL_PASSWORD = Config.GMAIL_PASSWORD
EMAILS_FILE = Config.EMAILS_FILE

# Armazenamento em memória para emails
emails_storage = {
    'inbox': [],
    'sent': [],
    'drafts': []
}

def connect_to_gmail_imap():
    """Conecta ao servidor IMAP do Gmail"""
    try:
        imap = imaplib.IMAP4_SSL('imap.gmail.com')
        imap.login(GMAIL_USER, GMAIL_PASSWORD)
        return imap
    except Exception as e:
        print(f"Erro ao conectar IMAP: {e}")
        return None

def fetch_emails():
    """Busca emails da caixa de entrada do Gmail"""
    imap = connect_to_gmail_imap()
    if not imap:
        return []
    
    try:
        imap.select('INBOX')
        _, messages = imap.search(None, 'ALL')
        
        emails = []
        for num in messages[0].split()[-10:]:  # Últimos 10 emails
            _, msg_data = imap.fetch(num, '(RFC822)')
            
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    
                    # Extrair informações do email
                    subject = msg['subject'] or 'Sem assunto'
                    from_email = msg['from']
                    date = msg['date']
                    
                    # Extrair corpo do email
                    body = ""
                    if msg.is_multipart():
                        for part in msg.walk():
                            if part.get_content_type() == "text/plain":
                                body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                                break
                    else:
                        body = msg.get_payload(decode=True).decode('utf-8', errors='ignore')
                    
                    emails.append({
                        'id': len(emails) + 1,
                        'subject': subject,
                        'from': from_email,
                        'to': GMAIL_USER,
                        'body': body,
                        'date': date,
                        'timestamp': datetime.now().isoformat(),
                        'read': False
                    })
        
        imap.close()
        imap.logout()
        return emails
        
    except Exception as e:
        print(f"Erro ao buscar emails: {e}")
        return []

def send_email(to_email, subject, body):
    """Envia email usando SMTP do Gmail"""
    try:
        msg = MIMEMultipart()
        msg['From'] = GMAIL_USER
        msg['To'] = to_email
        msg['Subject'] = subject
        
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(GMAIL_USER, GMAIL_PASSWORD)
        text = msg.as_string()
        server.sendmail(GMAIL_USER, to_email, text)
        server.quit()
        
        # Adicionar aos emails enviados
        sent_email = {
            'id': len(emails_storage['sent']) + 1,
            'subject': subject,
            'from': GMAIL_USER,
            'to': to_email,
            'body': body,
            'date': datetime.now().strftime('%a, %d %b %Y %H:%M:%S'),
            'timestamp': datetime.now().isoformat(),
            'read': True
        }
        emails_storage['sent'].append(sent_email)
        
        return True, "Email enviado com sucesso"
    except Exception as e:
        return False, f"Erro ao enviar email: {str(e)}"

def update_emails_periodically():
    """Atualiza emails periodicamente"""
    while True:
        try:
            new_emails = fetch_emails()
            emails_storage['inbox'] = new_emails
            time.sleep(30)  # Atualiza a cada 30 segundos
        except Exception as e:
            print(f"Erro na atualização automática: {e}")
            time.sleep(60)

# Iniciar thread para atualização automática
email_thread = threading.Thread(target=update_emails_periodically, daemon=True)
email_thread.start()

@app.route('/')
def index():
    """Página principal do Gmail"""
    return send_from_directory('.', 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    """Servir arquivos estáticos"""
    return send_from_directory('.', filename)

@app.route('/api/emails/inbox')
def get_inbox():
    """Obter emails da caixa de entrada"""
    return jsonify(emails_storage['inbox'])

@app.route('/api/emails/sent')
def get_sent():
    """Obter emails enviados"""
    return jsonify(emails_storage['sent'])

@app.route('/api/emails/drafts')
def get_drafts():
    """Obter rascunhos"""
    return jsonify(emails_storage['drafts'])

@app.route('/api/send-email', methods=['POST'])
def send_email_api():
    """Enviar email"""
    data = request.get_json()
    
    if not data or not all(k in data for k in ['to', 'subject', 'body']):
        return jsonify({'error': 'Dados obrigatórios: to, subject, body'}), 400
    
    success, message = send_email(data['to'], data['subject'], data['body'])
    
    if success:
        return jsonify({'success': True, 'message': message})
    else:
        return jsonify({'success': False, 'error': message}), 500

@app.route('/api/email/<int:email_id>')
def get_email_detail(email_id):
    """Obter detalhes de um email específico"""
    for folder in ['inbox', 'sent', 'drafts']:
        for email_item in emails_storage[folder]:
            if email_item['id'] == email_id:
                email_item['read'] = True
                return jsonify(email_item)
    
    return jsonify({'error': 'Email não encontrado'}), 404

@app.route('/api/email/<int:email_id>/delete', methods=['DELETE'])
def delete_email(email_id):
    """Deletar email"""
    for folder in ['inbox', 'sent', 'drafts']:
        emails_storage[folder] = [e for e in emails_storage[folder] if e['id'] != email_id]
    
    return jsonify({'success': True, 'message': 'Email deletado'})

@app.route('/api/save-draft', methods=['POST'])
def save_draft():
    """Salvar rascunho"""
    data = request.get_json()
    
    draft = {
        'id': len(emails_storage['drafts']) + 1,
        'subject': data.get('subject', ''),
        'to': data.get('to', ''),
        'body': data.get('body', ''),
        'timestamp': datetime.now().isoformat(),
        'read': True
    }
    
    emails_storage['drafts'].append(draft)
    return jsonify({'success': True, 'draft_id': draft['id']})

@app.route('/api/refresh-emails', methods=['POST'])
def refresh_emails():
    """Atualizar emails manualmente"""
    try:
        new_emails = fetch_emails()
        emails_storage['inbox'] = new_emails
        return jsonify({'success': True, 'count': len(new_emails)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/user-info')
def get_user_info():
    """Obter informações do usuário"""
    return jsonify({
        'email': GMAIL_USER,
        'name': GMAIL_USER.split('@')[0].title(),
        'inbox_count': len(emails_storage['inbox']),
        'sent_count': len(emails_storage['sent']),
        'drafts_count': len(emails_storage['drafts'])
    })

if __name__ == '__main__':
    # Carregar emails iniciais
    emails_storage['inbox'] = fetch_emails()
    
    print("📧 Sistema Gmail Completo iniciado!")
    print(f"👤 Usuário: {GMAIL_USER}")
    print(f"📬 Emails na caixa de entrada: {len(emails_storage['inbox'])}")
    print(f"🌐 Acesse: http://0.0.0.0:5000")
    
    app.run(host='0.0.0.0', port=5000, debug=True)
