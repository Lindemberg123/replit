
#!/usr/bin/env python3
"""
Exemplo de Integração com Sistema Gmail Independente
Execute este script para testar todas as funcionalidades da API
"""

import requests
import json
import time
from datetime import datetime

# Configuração da API
BASE_URL = "https://37b18808-226f-4838-9cd0-06e8905de082-00-24jzov5xta9v4.spock.replit.dev"
API_KEY = "gmail-verification-api-2024"

headers = {
    "Content-Type": "application/json",
    "X-API-Key": API_KEY
}

def print_separator(title):
    print(f"\n{'='*50}")
    print(f"  {title}")
    print('='*50)

def print_response(response):
    print(f"Status: {response.status_code}")
    try:
        data = response.json()
        print(f"Resposta: {json.dumps(data, indent=2, ensure_ascii=False)}")
        return data
    except:
        print(f"Resposta: {response.text}")
        return None

def test_check_user():
    print_separator("🔍 VERIFICAÇÃO DE USUÁRIO")
    
    response = requests.post(f"{BASE_URL}/api/external/check-user", 
                           headers=headers,
                           json={"email": "suport.com@gmail.oficial"})
    
    return print_response(response)

def test_basic_verification():
    print_separator("📧 VERIFICAÇÃO BÁSICA")
    
    response = requests.post(f"{BASE_URL}/api/external/send-verification",
                           headers=headers,
                           json={
                               "to_email": "suport.com@gmail.oficial",
                               "site_name": "Teste API Python",
                               "verification_code": f"PY{int(time.time()) % 10000}",
                               "verification_url": "https://meusite.com/verify?token=abc123",
                               "priority": "high",
                               "type": "security",
                               "expires_in": 3600
                           })
    
    return print_response(response)

def test_premium_verification():
    print_separator("⭐ VERIFICAÇÃO PREMIUM")
    
    response = requests.post(f"{BASE_URL}/api/external/send-advanced-verification",
                           headers=headers,
                           json={
                               "to_email": "suport.com@gmail.oficial",
                               "site_name": "App Premium Python",
                               "verification_code": f"PREM{int(time.time()) % 1000}",
                               "type": "premium",
                               "theme": "modern",
                               "verification_url": "https://premium.com/verify"
                           })
    
    return print_response(response)

def test_enterprise_verification():
    print_separator("🏢 VERIFICAÇÃO EMPRESARIAL")
    
    response = requests.post(f"{BASE_URL}/api/external/send-advanced-verification",
                           headers=headers,
                           json={
                               "to_email": "suport.com@gmail.oficial",
                               "site_name": "Empresa Corp",
                               "verification_code": f"ENT{int(time.time()) % 1000}",
                               "type": "enterprise",
                               "theme": "classic",
                               "custom_branding": True
                           })
    
    return print_response(response)

def test_password_reset():
    print_separator("🔐 RECUPERAÇÃO DE SENHA")
    
    response = requests.post(f"{BASE_URL}/api/external/send-reset-password",
                           headers=headers,
                           json={
                               "to_email": "suport.com@gmail.oficial",
                               "site_name": "Sistema Teste",
                               "reset_token": f"RST{int(time.time())}",
                               "reset_url": "https://sistema.com/reset-password"
                           })
    
    return print_response(response)

def test_notification():
    print_separator("🔔 NOTIFICAÇÃO")
    
    response = requests.post(f"{BASE_URL}/api/external/send-notification",
                           headers=headers,
                           json={
                               "to_email": "suport.com@gmail.oficial",
                               "site_name": "App Notificações",
                               "subject": "Nova mensagem importante",
                               "message": f"Esta é uma notificação de teste enviada em {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"
                           })
    
    return print_response(response)

def test_quick_login():
    print_separator("⚡ LOGIN RÁPIDO")
    
    # Obter contas disponíveis
    print("📋 Obtendo contas disponíveis...")
    response = requests.get(f"{BASE_URL}/api/quick-login/accounts")
    accounts_data = print_response(response)
    
    time.sleep(1)
    
    # Testar login rápido
    print("\n🚀 Testando login rápido...")
    response = requests.post(f"{BASE_URL}/api/quick-login/validate",
                           headers={"Content-Type": "application/json"},
                           json={"email": "suport.com@gmail.oficial"})
    
    return print_response(response)

def main():
    print("🧪 TESTE COMPLETO DA API - Sistema Gmail Independente")
    print(f"🌐 URL Base: {BASE_URL}")
    print(f"🔑 API Key: {API_KEY[:20]}...")
    
    try:
        # Executar todos os testes
        test_check_user()
        time.sleep(2)
        
        test_basic_verification()
        time.sleep(2)
        
        test_premium_verification()
        time.sleep(2)
        
        test_enterprise_verification()
        time.sleep(2)
        
        test_password_reset()
        time.sleep(2)
        
        test_notification()
        time.sleep(2)
        
        test_quick_login()
        
        print_separator("✅ TODOS OS TESTES CONCLUÍDOS")
        print("✨ API funcionando corretamente!")
        print("📧 Verifique os emails recebidos no sistema")
        print(f"🔗 Acesse: {BASE_URL}")
        
    except Exception as e:
        print_separator("❌ ERRO NO TESTE")
        print(f"Erro: {e}")
        print("Verifique se o servidor está rodando e a URL está correta")

if __name__ == "__main__":
    main()
