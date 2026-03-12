"""
Script para verificar e corrigir o administrador do sistema
"""

import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

# Obter o diretório base
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'instance', 'ministry.db')

# Criar aplicação Flask mínima
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_PATH}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Definir modelo User
class User(db.Model):
    """Modelo para usuários administradores."""
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

    def set_password(self, password):
        """Define a senha como hash."""
        self.password = generate_password_hash(password)

    def check_password(self, password):
        """Verifica se a senha fornecida corresponde ao hash armazenado."""
        return check_password_hash(self.password, password)

def verificar_admin():
    """Verifica o administrador e exibe suas informações"""
    
    with app.app_context():
        print("\n" + "=" * 80)
        print("VERIFICAÇÃO DO ADMINISTRADOR")
        print("=" * 80)
        
        # Buscar admin
        admin_email = "admin@ministeriodelouvor.com"
        admin = User.query.filter_by(email=admin_email).first()
        
        if admin:
            print(f"\n✅ Administrador encontrado:")
            print(f"   ID: {admin.id}")
            print(f"   Email: {admin.email}")
            print(f"   É Admin: {admin.is_admin}")
            print(f"   Hash da Senha: {admin.password[:50]}...")
            
            # Testar senha
            senha_teste = "admin123"
            if admin.check_password(senha_teste):
                print(f"\n✅ Senha '{senha_teste}' está CORRETA!")
            else:
                print(f"\n❌ Senha '{senha_teste}' está INCORRETA!")
                print("\n🔧 Redefinindo senha para 'admin123'...")
                admin.set_password("admin123")
                db.session.commit()
                print("✅ Senha redefinida com sucesso!")
            
            # Verificar se é admin
            if not admin.is_admin:
                print("\n⚠️  Campo is_admin é FALSE!")
                print("🔧 Corrigindo para TRUE...")
                admin.is_admin = True
                db.session.commit()
                print("✅ Campo is_admin corrigido!")
        else:
            print(f"\n❌ Administrador NÃO encontrado com email: {admin_email}")
            print("\n🔧 Criando novo administrador...")
            
            new_admin = User(email=admin_email)
            new_admin.set_password("admin123")
            new_admin.is_admin = True
            db.session.add(new_admin)
            db.session.commit()
            
            print("✅ Administrador criado com sucesso!")
            print(f"   Email: {admin_email}")
            print(f"   Senha: admin123")
        
        # Verificar todos os usuários
        print("\n" + "-" * 80)
        print("TODOS OS USUÁRIOS NO BANCO:")
        print("-" * 80)
        
        all_users = User.query.all()
        if all_users:
            for user in all_users:
                print(f"   • ID: {user.id} | Email: {user.email} | Admin: {user.is_admin}")
        else:
            print("   (Nenhum usuário encontrado)")
        
        print("\n" + "=" * 80)
        print("CREDENCIAIS PARA LOGIN:")
        print("=" * 80)
        print(f"   Email: admin@ministeriodelouvor.com")
        print(f"   Senha: admin123")
        print("=" * 80 + "\n")

if __name__ == '__main__':
    verificar_admin()
