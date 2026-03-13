"""
Script de migração para separar role 'lider' em 'lider_banda' e 'lider_ministerio'.

Este script converte todos os usuários e membros com role='lider' para 'lider_banda' por padrão.
Se necessário, você pode alterar manualmente depois através da interface de administração.

Executar com: python migrate_split_lider_roles.py
"""

from app import app, db, User, Member
from sqlalchemy import text

def migrate_lider_roles():
    """Converte role 'lider' para 'lider_banda'."""
    
    with app.app_context():
        print("\n" + "="*60)
        print("MIGRAÇÃO: Separar Líder em Líder de Banda e Líder de Ministério")
        print("="*60 + "\n")
        
        # Verificar e atualizar tabela User
        print("📋 Verificando usuários (User)...")
        users_with_lider = User.query.filter_by(role='lider').all()
        
        if users_with_lider:
            print(f"   Encontrados {len(users_with_lider)} usuários com role='lider'")
            for user in users_with_lider:
                user.role = 'lider_banda'  # Convertendo para líder de banda por padrão
                print(f"   ✓ {user.email} → lider_banda")
            
            db.session.commit()
            print(f"   ✅ {len(users_with_lider)} usuários atualizados\n")
        else:
            print("   ℹ️  Nenhum usuário com role='lider' encontrado\n")
        
        # Verificar e atualizar tabela Member
        print("📋 Verificando membros (Member)...")
        members_with_lider = Member.query.filter_by(role='lider').all()
        
        if members_with_lider:
            print(f"   Encontrados {len(members_with_lider)} membros com role='lider'")
            for member in members_with_lider:
                member.role = 'lider_banda'  # Convertendo para líder de banda por padrão
                print(f"   ✓ {member.name} ({member.email}) → lider_banda")
            
            db.session.commit()
            print(f"   ✅ {len(members_with_lider)} membros atualizados\n")
        else:
            print("   ℹ️  Nenhum membro com role='lider' encontrado\n")
        
        # Estatísticas finais
        print("="*60)
        print("📊 ESTATÍSTICAS FINAIS")
        print("="*60)
        
        # Contar todos os roles em User
        print("\n🔐 Distribuição de permissões (User):")
        user_stats = db.session.query(User.role, db.func.count(User.id)).group_by(User.role).all()
        for role, count in user_stats:
            role_label = {
                'admin': 'Administrador',
                'pastor': 'Pastor',
                'lider_banda': 'Líder de Banda',
                'lider_ministerio': 'Líder de Ministério',
                'ministro': 'Ministro de Louvor',
                'membro': 'Membro'
            }.get(role, role)
            print(f"   {role_label}: {count}")
        
        # Contar todos os roles em Member
        print("\n👥 Distribuição de permissões (Member):")
        member_stats = db.session.query(Member.role, db.func.count(Member.id)).group_by(Member.role).all()
        for role, count in member_stats:
            role_label = {
                'admin': 'Administrador',
                'pastor': 'Pastor',
                'lider_banda': 'Líder de Banda',
                'lider_ministerio': 'Líder de Ministério',
                'ministro': 'Ministro de Louvor',
                'membro': 'Membro'
            }.get(role, role)
            print(f"   {role_label}: {count}")
        
        print("\n" + "="*60)
        print("✅ MIGRAÇÃO CONCLUÍDA COM SUCESSO!")
        print("="*60)
        print("\n💡 NOTA: Todos os líderes foram convertidos para 'Líder de Banda'.")
        print("   Se algum usuário deveria ser 'Líder de Ministério', você pode")
        print("   alterar manualmente pela interface de administração.\n")

if __name__ == '__main__':
    try:
        migrate_lider_roles()
    except Exception as e:
        print(f"\n❌ ERRO durante a migração: {e}")
        import traceback
        traceback.print_exc()
