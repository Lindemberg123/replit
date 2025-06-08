
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import json
import os
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import Config

app = Flask(__name__)
CORS(app)

# Use configuration from config.py
API_KEY = Config.API_KEY
EMAILS_FILE = Config.EMAILS_FILE
SMTP_SERVER = Config.SMTP_SERVER
SMTP_PORT = Config.SMTP_PORT
GMAIL_USER = Config.GMAIL_USER
GMAIL_PASSWORD = Config.GMAIL_PASSWORD

def authenticate_request():
    """Check if request has valid API key"""
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return False
    
    token = auth_header.split(' ')[1]
    return token == API_KEY

def load_emails():
    """Load emails from JSON file"""
    if os.path.exists(EMAILS_FILE):
        try:
            with open(EMAILS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    return []

def save_emails(emails):
    """Save emails to JSON file"""
    with open(EMAILS_FILE, 'w', encoding='utf-8') as f:
        json.dump(emails, f, ensure_ascii=False, indent=2)

def send_gmail(to_email, subject, message):
    """Send email using Gmail SMTP"""
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = GMAIL_USER
        msg['To'] = to_email
        msg['Subject'] = subject
        
        # Add body to email
        msg.attach(MIMEText(message, 'plain', 'utf-8'))
        
        # Connect to server and send email
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(GMAIL_USER, GMAIL_PASSWORD)
        text = msg.as_string()
        server.sendmail(GMAIL_USER, to_email, text)
        server.quit()
        
        return True, "Email enviado com sucesso"
    except Exception as e:
        return False, f"Erro ao enviar email: {str(e)}"

# Routes

@app.route('/')
def index():
    """Serve the main HTML page"""
    return send_from_directory('.', 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    """Serve static files"""
    return send_from_directory('.', filename)

@app.route('/api/send-email', methods=['POST'])
def send_email():
    """Send email via API"""
    if not authenticate_request():
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['to', 'subject', 'message']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing required field: {field}'}), 400
    
    to_email = data['to']
    subject = data['subject']
    message = data['message']
    
    # Send email
    success, result_message = send_gmail(to_email, subject, message)
    
    if success:
        # Save email to database
        emails = load_emails()
        email_record = {
            'id': len(emails) + 1,
            'to': to_email,
            'from': GMAIL_USER,
            'subject': subject,
            'message': message,
            'timestamp': datetime.now().isoformat(),
            'status': 'sent'
        }
        emails.append(email_record)
        save_emails(emails)
        
        return jsonify({
            'success': True,
            'message': result_message,
            'email_id': email_record['id']
        }), 200
    else:
        return jsonify({
            'success': False,
            'error': result_message
        }), 500

@app.route('/api/emails', methods=['GET'])
def get_emails():
    """Get all emails"""
    if not authenticate_request():
        return jsonify({'error': 'Unauthorized'}), 401
    
    emails = load_emails()
    return jsonify(emails), 200

@app.route('/api/email/<int:email_id>', methods=['GET'])
def get_email(email_id):
    """Get specific email by ID"""
    if not authenticate_request():
        return jsonify({'error': 'Unauthorized'}), 401
    
    emails = load_emails()
    email = next((e for e in emails if e['id'] == email_id), None)
    
    if email:
        return jsonify(email), 200
    else:
        return jsonify({'error': 'Email not found'}), 404

@app.route('/api/config', methods=['POST'])
def update_config():
    """Update Gmail configuration"""
    if not authenticate_request():
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.get_json()
    
    # This is a placeholder for configuration updates
    # In production, you'd want to securely store credentials
    return jsonify({
        'success': True,
        'message': 'Configuration updated successfully'
    }), 200

@app.route('/api/status', methods=['GET'])
def api_status():
    """Get API status"""
    return jsonify({
        'status': 'online',
        'version': '1.0.0',
        'service': 'Gmail API Pro',
        'timestamp': datetime.now().isoformat()
    }), 200

@app.route('/api/docs', methods=['GET'])
def api_docs():
    """API Documentation"""
    docs = {
        'title': 'Gmail API Pro Documentation',
        'version': '1.0.0',
        'endpoints': {
            'POST /api/send-email': {
                'description': 'Send email',
                'parameters': {
                    'to': 'string (required) - Recipient email',
                    'subject': 'string (required) - Email subject',
                    'message': 'string (required) - Email content'
                },
                'headers': {
                    'Authorization': 'Bearer {API_KEY}',
                    'Content-Type': 'application/json'
                }
            },
            'GET /api/emails': {
                'description': 'Get all emails',
                'headers': {
                    'Authorization': 'Bearer {API_KEY}'
                }
            },
            'GET /api/email/{id}': {
                'description': 'Get specific email',
                'headers': {
                    'Authorization': 'Bearer {API_KEY}'
                }
            }
        }
    }
    return jsonify(docs), 200

if __name__ == '__main__':
    # Create emails file if it doesn't exist
    if not os.path.exists(EMAILS_FILE):
        save_emails([])
    
    print("🚀 Gmail API Pro Server iniciado!")
    print(f"📧 API Key: {API_KEY}")
    print(f"🌐 Acesse: http://0.0.0.0:5000")
    print(f"📚 Documentação: http://0.0.0.0:5000/api/docs")
    
    app.run(host='0.0.0.0', port=5000, debug=True)
