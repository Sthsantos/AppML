"""
Script de migração para criar a tabela de Push Notifications.

Execute este script para adicionar a tabela push_subscription ao banco de dados.

Uso:
    python migrate_add_push_subscription.py
"""

from app import app, db
from sqlalchemy import inspect

def migrate_add_push_subscription():
    """Cria a tabela push_subscription no banco de dados."""
    
    with app.app_context():
        inspector = inspect(db.engine)
        
        # Verificar se a tabela já existe
        if 'push_subscription' in inspector.get_table_names():
            print("ℹ️  A tabela 'push_subscription' já existe no banco de dados.")
            print("✅ Nenhuma alteração necessária.")
            return
        
        print("⚙️  Criando tabela 'push_subscription'...")
        
        try:
            # Criar a tabela usando SQLAlchemy
            from app import PushSubscription
            
            # Criar a tabela
            PushSubscription.__table__.create(db.engine)
            
            print("✅ Tabela 'push_subscription' criada com sucesso!")
            print("\nEstrutura da tabela:")
            print("  - id (INTEGER, PRIMARY KEY)")
            print("  - user_id (INTEGER, FK → user.id)")
            print("  - member_id (INTEGER, FK → member.id)")
            print("  - endpoint (TEXT, UNIQUE, NOT NULL)")
            print("  - p256dh_key (TEXT, NOT NULL)")
            print("  - auth_key (TEXT, NOT NULL)")
            print("  - device_info (VARCHAR(500))")
            print("  - created_at (DATETIME)")
            print("  - last_used (DATETIME)")
            print("  - is_active (BOOLEAN)")
            
            print("\n📋 Próximos passos:")
            print("  1. Verifique se as VAPID keys estão configuradas no .env")
            print("  2. Execute 'python gerar_vapid_keys.py' se ainda não tiver as keys")
            print("  3. Acesse /perfil no sistema e ative as notificações push")
            
        except Exception as e:
            print(f"❌ Erro ao criar tabela: {e}")
            print("\nDetalhes do erro:")
            import traceback
            traceback.print_exc()
            return

if __name__ == '__main__':
    print("=" * 60)
    print("MIGRAÇÃO: Adicionar suporte a Push Notifications")
    print("=" * 60)
    print()
    
    migrate_add_push_subscription()
    
    print()
    print("=" * 60)
