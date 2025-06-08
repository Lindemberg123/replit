
"""
Gmail API Pro Configuration
Configure your Gmail credentials here
"""

import os

class Config:
    # Gmail SMTP Configuration
    SMTP_SERVER = "smtp.gmail.com"
    SMTP_PORT = 587
    
    # Configure these with your Gmail credentials
    GMAIL_USER = os.environ.get('GMAIL_USER', 'your-email@gmail.com')
    GMAIL_PASSWORD = os.environ.get('GMAIL_APP_PASSWORD', 'your-app-password')
    
    # API Configuration
    API_KEY = os.environ.get('API_KEY', 'gmail-api-pro-key-2024')
    
    # Database
    EMAILS_FILE = "emails_data.json"
    
    # Security
    SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-here')

# Instructions for Gmail App Password:
"""
Para configurar o Gmail:

1. Ative a verificação em 2 etapas na sua conta Google
2. Vá para: https://myaccount.google.com/apppasswords
3. Selecione "App" -> "Outro (nome personalizado)"
4. Digite "Gmail API Pro"
5. Use a senha de 16 dígitos gerada no lugar da sua senha normal

Configure as variáveis de ambiente:
- GMAIL_USER: seu-email@gmail.com
- GMAIL_APP_PASSWORD: senha-de-16-digitos-do-app
- API_KEY: sua-chave-api-personalizada (opcional)
"""
