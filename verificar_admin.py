#!/usr/bin/env python3
"""Verifica se o usuário tem permissão de admin."""
from app import app, db, User

def verificar_permissao():
    with app.app_context():
        print("\n" + "="*50)
        print("  VERIFICANDO PERMISSÕES")
        print("="*50 + "\n")
        
        user = User.query.get(2)
        
        if not user:
            print("❌ Usuário ID 2 não encontrado!")
            return
        
        print(f"👤 Usuário: {user.email}")
        print(f"🔑 Role: {user.role}")
        print(f"🔐 is_admin: {user.is_admin}")
        
        if user.role in ['admin', 'lider_louvor', 'lider_geral']:
            print("\n✅ VOCÊ TEM PERMISSÃO para criar avisos!")
        else:
            print("\n❌ SEM PERMISSÃO - Precisa ser admin ou líder")
            print("\n🔧 Corrigindo permissão...")
            user.role = 'admin'
            db.session.commit()
            print("✅ Agora você é ADMIN!")
        
        print("\n" + "="*50)

if __name__ == '__main__':
    verificar_permissao()
