
#!/usr/bin/env python3
"""
Sistema Completo de Recuperação de Senha
Integração com Gmail System API

Este arquivo contém um exemplo completo de como implementar
um sistema de recuperação de senha usando a API do Gmail System.
"""

import requests
import secrets
import hashlib
import sqlite3
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, render_template_string

# Configurações da API
GMAIL_API_URL = "https://37b18808-226f-4838-9cd0-06e8905de082-00-24jzov5xta9v4.spock.replit.dev"
GMAIL_API_KEY = "gmail-verification-api-2024"

class PasswordResetManager:
    def __init__(self, db_path="password_resets.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Inicializa banco de dados para tokens de reset"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Tabela de usuários (exemplo)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabela de tokens de reset
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS password_reset_tokens (
                id INTEGER PRIMARY KEY,
                user_email TEXT NOT NULL,
                token TEXT UNIQUE NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                used BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_email) REFERENCES users(email)
            )
        ''')
        
        # Inserir usuário de exemplo se não existir
        cursor.execute('''
            INSERT OR IGNORE INTO users (email, password_hash, name)
            VALUES (?, ?, ?)
        ''', ('suport.com@gmail.oficial', 
              hashlib.sha256('admin123'.encode()).hexdigest(),
              'Administrador Sistema'))
        
        conn.commit()
        conn.close()
    
    def user_exists(self, email):
        """Verifica se usuário existe"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT email FROM users WHERE email = ?', (email,))
        result = cursor.fetchone()
        
        conn.close()
        return result is not None
    
    def generate_reset_token(self):
        """Gera token seguro de 32 caracteres"""
        return secrets.token_urlsafe(32)
    
    def send_reset_email(self, email, site_name="Meu Site"):
        """Envia email de recuperação de senha"""
        
        # Verificar se usuário existe
        if not self.user_exists(email):
            return {
                'success': False, 
                'error': 'Email não encontrado em nossa base de dados'
            }
        
        # Gerar token
        reset_token = self.generate_reset_token()
        expires_at = datetime.now() + timedelta(hours=24)
        
        # Salvar token no banco
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Invalidar tokens anteriores
        cursor.execute('''
            UPDATE password_reset_tokens 
            SET used = TRUE 
            WHERE user_email = ? AND used = FALSE
        ''', (email,))
        
        # Inserir novo token
        cursor.execute('''
            INSERT INTO password_reset_tokens (user_email, token, expires_at)
            VALUES (?, ?, ?)
        ''', (email, reset_token, expires_at))
        
        conn.commit()
        conn.close()
        
        # Construir URL de reset
        reset_url = f"https://meusite.com/reset-password?token={reset_token}"
        
        # Enviar email via Gmail System API
        headers = {
            'Content-Type': 'application/json',
            'X-API-Key': GMAIL_API_KEY
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
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    'success': True,
                    'message': 'Email de recuperação enviado com sucesso',
                    'email_id': result.get('email_id'),
                    'reset_token': reset_token,  # Remover em produção
                    'expires_at': expires_at.isoformat()
                }
            else:
                error = response.json()
                return {
                    'success': False,
                    'error': f"Erro da API: {error.get('error', 'Erro desconhecido')}"
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f"Erro de conexão: {str(e)}"
            }
    
    def validate_token(self, token):
        """Valida token de reset"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT user_email, expires_at, used 
            FROM password_reset_tokens 
            WHERE token = ?
        ''', (token,))
        
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            return {'valid': False, 'error': 'Token inválido'}
        
        user_email, expires_at_str, used = result
        
        if used:
            return {'valid': False, 'error': 'Token já foi utilizado'}
        
        expires_at = datetime.fromisoformat(expires_at_str)
        if datetime.now() > expires_at:
            return {'valid': False, 'error': 'Token expirado'}
        
        return {
            'valid': True,
            'user_email': user_email,
            'expires_at': expires_at_str
        }
    
    def reset_password(self, token, new_password):
        """Redefine senha usando token válido"""
        
        # Validar token
        validation = self.validate_token(token)
        if not validation['valid']:
            return validation
        
        user_email = validation['user_email']
        
        # Hash da nova senha
        password_hash = hashlib.sha256(new_password.encode()).hexdigest()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Atualizar senha
            cursor.execute('''
                UPDATE users 
                SET password_hash = ? 
                WHERE email = ?
            ''', (password_hash, user_email))
            
            # Marcar token como usado
            cursor.execute('''
                UPDATE password_reset_tokens 
                SET used = TRUE 
                WHERE token = ?
            ''', (token,))
            
            conn.commit()
            
            return {
                'success': True,
                'message': 'Senha alterada com sucesso',
                'user_email': user_email
            }
            
        except Exception as e:
            conn.rollback()
            return {
                'success': False,
                'error': f"Erro ao atualizar senha: {str(e)}"
            }
        finally:
            conn.close()
    
    def cleanup_expired_tokens(self):
        """Remove tokens expirados do banco"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            DELETE FROM password_reset_tokens 
            WHERE expires_at < ? OR used = TRUE
        ''', (datetime.now(),))
        
        deleted_count = cursor.rowcount
        conn.commit()
        conn.close()
        
        return deleted_count

# Exemplo de aplicação Flask
app = Flask(__name__)
reset_manager = PasswordResetManager()

@app.route('/api/forgot-password', methods=['POST'])
def forgot_password():
    """API endpoint para solicitar reset de senha"""
    data = request.get_json()
    email = data.get('email')
    
    if not email:
        return jsonify({'error': 'Email é obrigatório'}), 400
    
    result = reset_manager.send_reset_email(email, "Minha Aplicação")
    
    if result['success']:
        return jsonify({
            'success': True,
            'message': 'Se o email existir, você receberá instruções de recuperação'
        })
    else:
        # Não revelar se email existe por segurança
        return jsonify({
            'success': True,
            'message': 'Se o email existir, você receberá instruções de recuperação'
        })

@app.route('/api/reset-password', methods=['POST'])
def reset_password():
    """API endpoint para redefinir senha"""
    data = request.get_json()
    token = data.get('token')
    new_password = data.get('new_password')
    
    if not token or not new_password:
        return jsonify({'error': 'Token e nova senha são obrigatórios'}), 400
    
    if len(new_password) < 6:
        return jsonify({'error': 'Senha deve ter pelo menos 6 caracteres'}), 400
    
    result = reset_manager.reset_password(token, new_password)
    
    if result['success']:
        return jsonify(result)
    else:
        return jsonify(result), 400

@app.route('/api/validate-reset-token', methods=['GET'])
def validate_reset_token():
    """API endpoint para validar token de reset"""
    token = request.args.get('token')
    
    if not token:
        return jsonify({'error': 'Token é obrigatório'}), 400
    
    result = reset_manager.validate_token(token)
    return jsonify(result)

# HTML Template para página de reset
RESET_PASSWORD_TEMPLATE = '''
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Redefinir Senha</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0;
            padding: 20px;
        }
        .reset-container {
            background: white;
            padding: 40px;
            border-radius: 16px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            max-width: 400px;
            width: 100%;
        }
        .form-group {
            margin-bottom: 20px;
        }
        label {
            display: block;
            margin-bottom: 8px;
            color: #555;
            font-weight: 500;
        }
        input {
            width: 100%;
            padding: 12px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 16px;
            box-sizing: border-box;
        }
        input:focus {
            outline: none;
            border-color: #4285f4;
        }
        .btn {
            width: 100%;
            background: #4285f4;
            color: white;
            border: none;
            padding: 14px;
            border-radius: 8px;
            font-size: 16px;
            cursor: pointer;
            font-weight: 500;
        }
        .btn:hover {
            background: #3367d6;
        }
        .message {
            padding: 12px;
            border-radius: 8px;
            margin-bottom: 20px;
            text-align: center;
        }
        .success {
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        .error {
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
    </style>
</head>
<body>
    <div class="reset-container">
        <h2>🔑 Redefinir Senha</h2>
        <div id="message"></div>
        
        <form id="resetForm">
            <div class="form-group">
                <label for="newPassword">Nova Senha:</label>
                <input type="password" id="newPassword" name="newPassword" required 
                       minlength="6" placeholder="Digite sua nova senha">
            </div>
            
            <div class="form-group">
                <label for="confirmPassword">Confirmar Senha:</label>
                <input type="password" id="confirmPassword" name="confirmPassword" required 
                       minlength="6" placeholder="Digite novamente sua nova senha">
            </div>
            
            <button type="submit" class="btn" id="resetBtn">
                Alterar Senha
            </button>
        </form>
    </div>

    <script>
        // Obter token da URL
        const urlParams = new URLSearchParams(window.location.search);
        const token = urlParams.get('token');
        
        if (!token) {
            showMessage('Token inválido ou expirado', 'error');
            document.getElementById('resetForm').style.display = 'none';
        } else {
            // Validar token
            validateToken(token);
        }
        
        async function validateToken(token) {
            try {
                const response = await fetch(`/api/validate-reset-token?token=${token}`);
                const result = await response.json();
                
                if (!result.valid) {
                    showMessage(result.error, 'error');
                    document.getElementById('resetForm').style.display = 'none';
                }
            } catch (error) {
                showMessage('Erro ao validar token', 'error');
            }
        }
        
        document.getElementById('resetForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const newPassword = document.getElementById('newPassword').value;
            const confirmPassword = document.getElementById('confirmPassword').value;
            const resetBtn = document.getElementById('resetBtn');
            
            if (newPassword !== confirmPassword) {
                showMessage('As senhas não coincidem', 'error');
                return;
            }
            
            resetBtn.disabled = true;
            resetBtn.textContent = 'Alterando...';
            
            try {
                const response = await fetch('/api/reset-password', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        token: token,
                        new_password: newPassword
                    })
                });
                
                const result = await response.json();
                
                if (response.ok) {
                    showMessage('Senha alterada com sucesso! Você pode fazer login agora.', 'success');
                    document.getElementById('resetForm').style.display = 'none';
                    
                    // Redirecionar após 3 segundos
                    setTimeout(() => {
                        window.location.href = '/login.html';
                    }, 3000);
                } else {
                    showMessage(result.error, 'error');
                }
            } catch (error) {
                showMessage('Erro ao alterar senha', 'error');
            } finally {
                resetBtn.disabled = false;
                resetBtn.textContent = 'Alterar Senha';
            }
        });
        
        function showMessage(message, type) {
            const messageDiv = document.getElementById('message');
            messageDiv.className = `message ${type}`;
            messageDiv.textContent = message;
        }
    </script>
</body>
</html>
'''

@app.route('/reset-password')
def reset_password_page():
    """Página de redefinição de senha"""
    return RESET_PASSWORD_TEMPLATE

# Exemplo de uso
if __name__ == "__main__":
    print("🔑 Sistema de Recuperação de Senha")
    print("=" * 50)
    
    # Teste 1: Enviar email de recuperação
    print("\n1. Enviando email de recuperação...")
    result = reset_manager.send_reset_email("suport.com@gmail.oficial", "Meu Site de Teste")
    
    if result['success']:
        print(f"   ✅ Email enviado! ID: {result.get('email_id')}")
        print(f"   🔗 Token: {result.get('reset_token')}")
        
        # Teste 2: Validar token
        print("\n2. Validando token...")
        validation = reset_manager.validate_token(result['reset_token'])
        
        if validation['valid']:
            print(f"   ✅ Token válido para: {validation['user_email']}")
            
            # Teste 3: Redefinir senha
            print("\n3. Redefinindo senha...")
            reset_result = reset_manager.reset_password(result['reset_token'], "nova_senha_123")
            
            if reset_result['success']:
                print(f"   ✅ Senha alterada para: {reset_result['user_email']}")
            else:
                print(f"   ❌ Erro: {reset_result['error']}")
        else:
            print(f"   ❌ Token inválido: {validation['error']}")
    else:
        print(f"   ❌ Erro: {result['error']}")
    
    # Limpeza
    print("\n4. Limpando tokens expirados...")
    deleted = reset_manager.cleanup_expired_tokens()
    print(f"   🗑️ {deleted} tokens removidos")
    
    print("\n" + "=" * 50)
    print("Para testar a API web, execute:")
    print("python exemplo_completo_reset_senha.py")
    print("E acesse: http://localhost:5000")
    
    # Iniciar servidor se executado diretamente
    if input("\nIniciar servidor web? (s/n): ").lower() == 's':
        app.run(debug=True, port=5001)
