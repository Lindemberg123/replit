
#!/usr/bin/env python3
"""
Exemplo de integração com o Sistema Gmail Independente
Este script mostra como usar a API externa para enviar emails de verificação
"""

import requests
import json
import random
import string

# Configurações
GMAIL_API_URL = "http://localhost:5000"  # Altere para sua URL do Replit
API_KEY = "gmail-verification-api-2024"

def generate_verification_code(length=6):
    """Gera um código de verificação aleatório"""
    return ''.join(random.choices(string.digits, k=length))

def generate_token(length=32):
    """Gera um token aleatório"""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def check_user_exists(email):
    """Verifica se um usuário existe no sistema Gmail"""
    headers = {
        'Content-Type': 'application/json',
        'X-API-Key': API_KEY
    }
    
    data = {'email': email}
    
    try:
        response = requests.post(
            f"{GMAIL_API_URL}/api/external/check-user",
            json=data,
            headers=headers
        )
        
        if response.status_code == 200:
            result = response.json()
            return result['exists'], result.get('user_info')
        else:
            print(f"Erro ao verificar usuário: {response.status_code}")
            return False, None
            
    except Exception as e:
        print(f"Erro na requisição: {e}")
        return False, None

def send_verification_email(email, site_name):
    """Envia email de verificação"""
    # Primeiro verificar se o usuário existe
    exists, user_info = check_user_exists(email)
    
    if not exists:
        print(f"❌ Usuário {email} não encontrado no sistema")
        return False
    
    print(f"✅ Usuário encontrado: {user_info['name']}")
    
    # Gerar código e URL de verificação
    verification_code = generate_verification_code()
    verification_url = f"https://meusite.com/verify?email={email}&code={verification_code}"
    
    headers = {
        'Content-Type': 'application/json',
        'X-API-Key': API_KEY
    }
    
    data = {
        'to_email': email,
        'site_name': site_name,
        'verification_code': verification_code,
        'verification_url': verification_url
    }
    
    try:
        response = requests.post(
            f"{GMAIL_API_URL}/api/external/send-verification",
            json=data,
            headers=headers
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Email de verificação enviado!")
            print(f"   Email ID: {result['email_id']}")
            print(f"   Código: {verification_code}")
            return True
        else:
            error = response.json()
            print(f"❌ Erro: {error['error']}")
            return False
            
    except Exception as e:
        print(f"❌ Erro na requisição: {e}")
        return False

def send_password_reset(email, site_name):
    """Envia email de recuperação de senha"""
    # Verificar se usuário existe
    exists, user_info = check_user_exists(email)
    
    if not exists:
        print(f"❌ Usuário {email} não encontrado")
        return False
    
    # Gerar token de recuperação
    reset_token = generate_token()
    reset_url = f"https://meusite.com/reset-password?token={reset_token}"
    
    headers = {
        'Content-Type': 'application/json',
        'X-API-Key': API_KEY
    }
    
    data = {
        'to_email': email,
        'site_name': site_name,
        'reset_token': reset_token,
        'reset_url': reset_url
    }
    
    try:
        response = requests.post(
            f"{GMAIL_API_URL}/api/external/send-reset-password",
            json=data,
            headers=headers
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Email de recuperação enviado!")
            print(f"   Token: {reset_token}")
            return True
        else:
            error = response.json()
            print(f"❌ Erro: {error['error']}")
            return False
            
    except Exception as e:
        print(f"❌ Erro na requisição: {e}")
        return False

def send_notification(email, site_name, subject, message):
    """Envia email de notificação"""
    headers = {
        'Content-Type': 'application/json',
        'X-API-Key': API_KEY
    }
    
    data = {
        'to_email': email,
        'site_name': site_name,
        'subject': subject,
        'message': message
    }
    
    try:
        response = requests.post(
            f"{GMAIL_API_URL}/api/external/send-notification",
            json=data,
            headers=headers
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Notificação enviada!")
            return True
        else:
            error = response.json()
            print(f"❌ Erro: {error['error']}")
            return False
            
    except Exception as e:
        print(f"❌ Erro na requisição: {e}")
        return False

def main():
    """Exemplo de uso da API"""
    print("🚀 Testando integração com Sistema Gmail Independente")
    print("=" * 60)
    
    # Email para testar (use um email que existe no sistema)
    test_email = "suport.com@gmail.oficial"  # Email do admin
    site_name = "Meu Site de Teste"
    
    print(f"📧 Testando com email: {test_email}")
    print()
    
    # Teste 1: Verificar se usuário existe
    print("1️⃣ Verificando se usuário existe...")
    exists, user_info = check_user_exists(test_email)
    if exists:
        print(f"✅ Usuário existe: {user_info['name']} (ID: {user_info['user_id']})")
    else:
        print("❌ Usuário não encontrado")
        return
    
    print()
    
    # Teste 2: Enviar email de verificação
    print("2️⃣ Enviando email de verificação...")
    send_verification_email(test_email, site_name)
    print()
    
    # Teste 3: Enviar email de recuperação
    print("3️⃣ Enviando email de recuperação de senha...")
    send_password_reset(test_email, site_name)
    print()
    
    # Teste 4: Enviar notificação
    print("4️⃣ Enviando notificação...")
    send_notification(
        test_email,
        site_name,
        "Bem-vindo ao nosso sistema!",
        "Obrigado por se cadastrar! Aproveite todos os recursos disponíveis."
    )
    print()
    
    print("✅ Todos os testes concluídos!")
    print("📬 Verifique a caixa de entrada no Sistema Gmail para ver os emails enviados")

if __name__ == "__main__":
    main()
