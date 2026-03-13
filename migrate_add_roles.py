"""
Script de migração para adicionar campo 'role' às tabelas User e Member.
Execute este script uma vez para atualizar o banco de dados existente.
"""
from app import app, db, User, Member, ROLE_ADMIN, ROLE_MEMBRO

def migrate_add_roles():
    """Adiciona coluna 'role' às tabelas User e Member se não existir."""
    with app.app_context():
        # Verificar se precisa criar as tabelas
        db.create_all()
        
        # Tentar adicionar a coluna role em User se não existir
        try:
            # SQLite não suporta ALTER COLUMN diretamente, então usamos raw SQL
            with db.engine.connect() as conn:
                # Verificar se a coluna já existe
                result = conn.execute(db.text("PRAGMA table_info(user)")).fetchall()
                columns = [row[1] for row in result]
                
                if 'role' not in columns:
                    print("⚙️ Adicionando coluna 'role' na tabela User...")
                    conn.execute(db.text("ALTER TABLE user ADD COLUMN role VARCHAR(20) DEFAULT 'membro'"))
                    conn.commit()
                    print("✅ Coluna 'role' adicionada à tabela User")
                else:
                    print("ℹ️ Coluna 'role' já existe na tabela User")
                
                # Atualizar users existentes
                print("⚙️ Atualizando roles dos usuários existentes...")
                users = User.query.all()
                for user in users:
                    if not user.role or user.role == 'membro':
                        # Se is_admin é True, definir como admin
                        if user.is_admin:
                            user.role = ROLE_ADMIN
                        else:
                            user.role = ROLE_MEMBRO
                db.session.commit()
                print(f"✅ {len(users)} usuários atualizados")
                
        except Exception as e:
            print(f"⚠️ Erro ao migrar tabela User: {e}")
            db.session.rollback()
        
        # Tentar adicionar a coluna role em Member se não existir
        try:
            with db.engine.connect() as conn:
                # Verificar se a coluna já existe
                result = conn.execute(db.text("PRAGMA table_info(member)")).fetchall()
                columns = [row[1] for row in result]
                
                if 'role' not in columns:
                    print("⚙️ Adicionando coluna 'role' na tabela Member...")
                    conn.execute(db.text("ALTER TABLE member ADD COLUMN role VARCHAR(20) DEFAULT 'membro'"))
                    conn.commit()
                    print("✅ Coluna 'role' adicionada à tabela Member")
                else:
                    print("ℹ️ Coluna 'role' já existe na tabela Member")
                
                # Atualizar members existentes
                print("⚙️ Atualizando roles dos membros existentes...")
                members = Member.query.all()
                for member in members:
                    if not member.role or member.role == 'membro':
                        # Se is_admin é True, definir como admin (improvável para Member)
                        if member.is_admin:
                            member.role = ROLE_ADMIN
                        else:
                            member.role = ROLE_MEMBRO
                db.session.commit()
                print(f"✅ {len(members)} membros atualizados")
                
        except Exception as e:
            print(f"⚠️ Erro ao migrar tabela Member: {e}")
            db.session.rollback()
        
        print("\n✅ Migração concluída com sucesso!")
        print("\nNíveis de permissão disponíveis:")
        print("  - admin: Administrador (acesso total)")
        print("  - pastor: Pastor (acesso pleno)")
        print("  - lider: Líder (acesso pleno)")
        print("  - ministro: Ministro de Louvor (gerencia músicas das próprias escalas)")
        print("  - membro: Membro comum (acesso limitado)")

if __name__ == '__main__':
    print("=" * 60)
    print("MIGRAÇÃO: Adicionar campo 'role' às tabelas User e Member")
    print("=" * 60)
    migrate_add_roles()
