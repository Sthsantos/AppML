"""Script para criar um usuário membro (não-admin) para testes"""
import sys
import os

# Adicionar o diretório ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db, User, Member

def criar_usuario_teste():
    with app.app_context():
        # Verificar se já existe na tabela Member
        existing_member = Member.query.filter_by(email='membro@teste.com').first()
        
        if existing_member:
            print("⚠️  Membro membro@teste.com já existe!")
            print(f"   Nome: {existing_member.name}")
            print(f"   Instrumento: {existing_member.instrument}")
            print("\n🔄 Atualizando senha para '123456'...")
            existing_member.set_password('123456')
            db.session.commit()
            print("✅ Senha atualizada!")
        else:
            print("🔨 Criando novo membro para teste...")
            novo_membro = Member(
                name='Maria Silva',
                email='membro@teste.com',
                instrument='Vocalista',
                phone='(11) 98765-4321'
            )
            novo_membro.set_password('123456')
            db.session.add(novo_membro)
            db.session.commit()
            print("✅ Membro criado com sucesso!")
        
        print("\n" + "=" * 60)
        print("CREDENCIAIS PARA TESTE (Membro Comum - NÃO ADMIN)")
        print("=" * 60)
        print("📧 Email: membro@teste.com")
        print("🔑 Senha: 123456")
        print("👤 Tipo: Membro (sem privilégios de administrador)")
        print("🎤 Nome: Maria Silva")
        print("🎵 Instrumento: Vocalista")
        print("=" * 60)
        
        # Listar todos os membros
        print("\n📋 TODOS OS MEMBROS NO SISTEMA:")
        print("-" * 60)
        members = Member.query.all()
        for m in members:
            status = "⚠️ SUSPENSO" if m.suspended else "✅ ATIVO"
            print(f"{status} | {m.email} | {m.name} | {m.instrument}")
        
        # Listar todos os usuários admin
        print("\n👑 USUÁRIOS ADMIN NO SISTEMA:")
        print("-" * 60)
        users = User.query.filter_by(is_admin=True).all()
        if users:
            for u in users:
                print(f"👑 ADMIN | {u.email}")
        else:
            print("Nenhum usuário admin encontrado")

if __name__ == '__main__':
    criar_usuario_teste()
