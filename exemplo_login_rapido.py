
import requests
import json
from datetime import datetime

class QuickLoginClient:
    def __init__(self, base_url="http://0.0.0.0:5000"):
        """
        Cliente para integração com o Sistema de Login Rápido
        
        Args:
            base_url: URL base do sistema Gmail (ex: https://seu-repl.replit.dev)
        """
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
    
    def get_all_accounts(self):
        """
        Busca todas as contas cadastradas no sistema
        
        Returns:
            dict: Lista de contas disponíveis ou erro
        """
        try:
            response = self.session.get(f"{self.base_url}/api/quick-login/accounts")
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"Erro HTTP {response.status_code}"}
                
        except Exception as e:
            return {"error": f"Erro de conexão: {str(e)}"}
    
    def get_recent_accounts(self):
        """
        Busca as 5 contas com login mais recente
        
        Returns:
            dict: Lista de contas recentes ou erro
        """
        try:
            response = self.session.get(f"{self.base_url}/api/quick-login/recent")
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"Erro HTTP {response.status_code}"}
                
        except Exception as e:
            return {"error": f"Erro de conexão: {str(e)}"}
    
    def validate_quick_login(self, email):
        """
        Realiza login rápido com uma conta específica
        
        Args:
            email: Email da conta para fazer login
            
        Returns:
            dict: Dados do usuário logado ou erro
        """
        try:
            data = {"email": email}
            
            response = self.session.post(
                f"{self.base_url}/api/quick-login/validate",
                json=data,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"Erro: {response.json().get('error', 'Erro desconhecido')}"}
                
        except Exception as e:
            return {"error": f"Erro de conexão: {str(e)}"}

class QuickLoginInterface:
    def __init__(self, client):
        """
        Interface de linha de comando para o sistema de login rápido
        
        Args:
            client: Instância do QuickLoginClient
        """
        self.client = client
    
    def format_last_login(self, last_login):
        """Formatar data do último login"""
        if not last_login or last_login == 'Nunca':
            return 'Nunca'
        
        try:
            login_date = datetime.fromisoformat(last_login.replace('Z', '+00:00'))
            now = datetime.now()
            diff = now - login_date.replace(tzinfo=None)
            
            if diff.days == 0:
                if diff.seconds < 3600:
                    return f"{diff.seconds // 60} minutos atrás"
                else:
                    return f"{diff.seconds // 3600} horas atrás"
            elif diff.days == 1:
                return "Ontem"
            else:
                return f"{diff.days} dias atrás"
        except:
            return str(last_login)
    
    def display_accounts(self, accounts_data):
        """
        Exibe lista de contas formatada
        
        Args:
            accounts_data: Dados das contas retornados pela API
        """
        if "error" in accounts_data:
            print(f"❌ {accounts_data['error']}")
            return []
        
        accounts = accounts_data.get('accounts', [])
        
        if not accounts:
            print("📭 Nenhuma conta encontrada no sistema")
            return []
        
        print(f"\n🔐 {accounts_data.get('total', len(accounts))} conta(s) disponível(is):")
        print("=" * 60)
        
        for i, account in enumerate(accounts, 1):
            admin_badge = " 👑 ADMIN" if account.get('is_admin', False) else ""
            last_login = self.format_last_login(account.get('last_login'))
            
            print(f"{i}. {account['name']}{admin_badge}")
            print(f"   📧 {account['email']}")
            print(f"   🆔 {account.get('user_id', 'N/A')}")
            print(f"   ⏰ Último acesso: {last_login}")
            print(f"   📅 Criado em: {account.get('created_at', 'N/A')[:10]}")
            print()
        
        return accounts
    
    def choose_account_interactive(self):
        """
        Interface interativa para escolher uma conta
        
        Returns:
            dict: Dados da conta escolhida ou None
        """
        print("🚀 Sistema de Login Rápido - Gmail Independente")
        print("=" * 50)
        
        # Buscar contas
        print("📡 Carregando contas disponíveis...")
        accounts_data = self.client.get_all_accounts()
        
        accounts = self.display_accounts(accounts_data)
        
        if not accounts:
            return None
        
        # Escolher conta
        while True:
            try:
                choice = input(f"\n🎯 Escolha uma conta (1-{len(accounts)}) ou 'q' para sair: ").strip()
                
                if choice.lower() == 'q':
                    print("👋 Saindo...")
                    return None
                
                account_index = int(choice) - 1
                
                if 0 <= account_index < len(accounts):
                    return accounts[account_index]
                else:
                    print(f"❌ Número inválido. Digite de 1 a {len(accounts)}")
                    
            except ValueError:
                print("❌ Digite um número válido ou 'q' para sair")
    
    def perform_login(self, account):
        """
        Realizar login com a conta escolhida
        
        Args:
            account: Dados da conta escolhida
            
        Returns:
            dict: Resultado do login
        """
        print(f"\n🔐 Fazendo login como {account['name']} ({account['email']})...")
        
        result = self.client.validate_quick_login(account['email'])
        
        if "error" in result:
            print(f"❌ Erro no login: {result['error']}")
            return result
        
        if result.get('success'):
            user = result.get('user', {})
            print(f"\n✅ Login realizado com sucesso!")
            print(f"👤 Nome: {user.get('name')}")
            print(f"📧 Email: {user.get('email')}")
            print(f"🆔 ID: {user.get('user_id')}")
            
            if user.get('is_admin'):
                print("👑 Privilégios de administrador ativados")
            
            print(f"💬 {result.get('message', 'Login concluído')}")
            return result
        
        return {"error": "Resposta inesperada do servidor"}

def example_integration():
    """
    Exemplo completo de integração com o sistema de login rápido
    """
    # Configurar cliente (substitua pela URL do seu Repl)
    client = QuickLoginClient("http://0.0.0.0:5000")  # ou https://seu-repl.replit.dev
    interface = QuickLoginInterface(client)
    
    print("🎯 EXEMPLO: Integração com Sistema de Login Rápido")
    print("=" * 55)
    
    # Escolher conta interativamente
    chosen_account = interface.choose_account_interactive()
    
    if chosen_account:
        # Realizar login
        login_result = interface.perform_login(chosen_account)
        
        if login_result.get('success'):
            print("\n🎉 Agora você pode usar os dados do usuário logado em seu sistema!")
            
            # Exemplo de como usar os dados do usuário
            user_data = login_result.get('user', {})
            print("\n📋 Dados disponíveis para seu sistema:")
            print(f"   - Email: {user_data.get('email')}")
            print(f"   - Nome: {user_data.get('name')}")
            print(f"   - ID único: {user_data.get('user_id')}")
            print(f"   - É admin: {user_data.get('is_admin', False)}")
            
            return user_data
        else:
            print("\n❌ Falha no login. Tente novamente.")
            return None
    
    return None

def quick_login_for_external_site(site_name, redirect_url=None):
    """
    Função simplificada para sites externos usarem o login rápido
    
    Args:
        site_name: Nome do site que está integrando
        redirect_url: URL para redirecionar após login (opcional)
        
    Returns:
        dict: Dados do usuário logado ou None
    """
    print(f"🌐 Login rápido para: {site_name}")
    print("=" * (20 + len(site_name)))
    
    client = QuickLoginClient("http://0.0.0.0:5000")  # Configure sua URL aqui
    interface = QuickLoginInterface(client)
    
    # Buscar apenas contas recentes para experiência mais rápida
    print("⚡ Carregando contas recentes...")
    recent_data = client.get_recent_accounts()
    
    if "error" in recent_data or not recent_data.get('recent_accounts'):
        print("📭 Nenhuma conta recente encontrada. Carregando todas as contas...")
        recent_data = client.get_all_accounts()
        recent_data['recent_accounts'] = recent_data.get('accounts', [])
    
    # Mostrar apenas as 3 mais recentes para login rápido
    accounts = recent_data.get('recent_accounts', [])[:3]
    
    if not accounts:
        print("❌ Nenhuma conta disponível para login rápido")
        return None
    
    print(f"\n⚡ Login rápido disponível para {len(accounts)} conta(s):")
    
    for i, account in enumerate(accounts, 1):
        admin_badge = " 👑" if account.get('is_admin', False) else ""
        print(f"{i}. {account['name']}{admin_badge} ({account['email']})")
    
    # Escolher rapidamente
    while True:
        try:
            choice = input(f"\n🚀 Escolha (1-{len(accounts)}) ou 'v' para ver todas: ").strip()
            
            if choice.lower() == 'v':
                # Mostrar interface completa
                return example_integration()
            
            account_index = int(choice) - 1
            
            if 0 <= account_index < len(accounts):
                chosen_account = accounts[account_index]
                
                # Login direto
                result = client.validate_quick_login(chosen_account['email'])
                
                if result.get('success'):
                    user = result.get('user', {})
                    print(f"\n✅ Bem-vindo ao {site_name}, {user.get('name')}!")
                    
                    if redirect_url:
                        print(f"🔗 Redirecionando para: {redirect_url}")
                    
                    return user
                else:
                    print(f"❌ Erro: {result.get('error', 'Falha no login')}")
                    return None
            else:
                print(f"❌ Escolha entre 1 e {len(accounts)}")
                
        except ValueError:
            print("❌ Digite um número válido")

if __name__ == "__main__":
    print("🔐 Sistema de Login Rápido - Cliente Python")
    print("=" * 45)
    print()
    print("Escolha uma opção:")
    print("1. Exemplo completo com interface interativa")
    print("2. Login rápido simplificado")
    print("3. Teste de conexão com a API")
    print()
    
    choice = input("Digite sua escolha (1-3): ").strip()
    
    if choice == "1":
        # Exemplo completo
        user_data = example_integration()
        
        if user_data:
            print(f"\n🎯 LOGIN CONCLUÍDO! Usuário: {user_data.get('name')}")
        
    elif choice == "2":
        # Login rápido para site externo
        site_name = input("Digite o nome do seu site: ").strip() or "Meu Site"
        user_data = quick_login_for_external_site(site_name)
        
        if user_data:
            print(f"\n🎯 USUÁRIO LOGADO: {user_data}")
    
    elif choice == "3":
        # Teste de conexão
        print("🧪 Testando conexão com a API...")
        client = QuickLoginClient("http://0.0.0.0:5000")
        
        result = client.get_all_accounts()
        
        if "error" in result:
            print(f"❌ Erro: {result['error']}")
        else:
            print(f"✅ Conexão OK! {result.get('total', 0)} conta(s) encontrada(s)")
            
            for account in result.get('accounts', [])[:3]:
                print(f"   - {account['name']} ({account['email']})")
    
    else:
        print("❌ Opção inválida")
    
    print("\n👋 Obrigado por usar o Sistema de Login Rápido!")
