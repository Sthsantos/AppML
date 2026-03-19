"""
Script de migração para adicionar campos de confirmação de presença à tabela Escala.
Execute este script uma vez para atualizar o banco de dados existente.

Uso:
    python migrate_add_confirmacao.py
"""
from app import app, db

def migrate_add_confirmacao():
    """Adiciona colunas de confirmação à tabela Escala se não existirem."""
    with app.app_context():
        print("🔄 Iniciando migração - Adicionar campos de confirmação...")
        
        # Verificar se precisa criar as tabelas
        db.create_all()
        
        try:
            with db.engine.connect() as conn:
                # Verificar se as colunas já existem
                result = conn.execute(db.text("PRAGMA table_info(escala)")).fetchall()
                columns = [row[1] for row in result]
                
                changes_made = False
                
                # Adicionar status_confirmacao se não existir
                if 'status_confirmacao' not in columns:
                    print("⚙️  Adicionando coluna 'status_confirmacao'...")
                    conn.execute(db.text(
                        "ALTER TABLE escala ADD COLUMN status_confirmacao VARCHAR(20) DEFAULT 'pendente'"
                    ))
                    conn.commit()
                    print("✅ Coluna 'status_confirmacao' adicionada")
                    changes_made = True
                else:
                    print("ℹ️  Coluna 'status_confirmacao' já existe")
                
                # Adicionar data_confirmacao se não existir
                if 'data_confirmacao' not in columns:
                    print("⚙️  Adicionando coluna 'data_confirmacao'...")
                    conn.execute(db.text(
                        "ALTER TABLE escala ADD COLUMN data_confirmacao DATETIME NULL"
                    ))
                    conn.commit()
                    print("✅ Coluna 'data_confirmacao' adicionada")
                    changes_made = True
                else:
                    print("ℹ️  Coluna 'data_confirmacao' já existe")
                
                # Adicionar observacao_confirmacao se não existir
                if 'observacao_confirmacao' not in columns:
                    print("⚙️  Adicionando coluna 'observacao_confirmacao'...")
                    conn.execute(db.text(
                        "ALTER TABLE escala ADD COLUMN observacao_confirmacao TEXT NULL"
                    ))
                    conn.commit()
                    print("✅ Coluna 'observacao_confirmacao' adicionada")
                    changes_made = True
                else:
                    print("ℹ️  Coluna 'observacao_confirmacao' já existe")
                
                if changes_made:
                    # Atualizar escalas existentes para status pendente
                    print("⚙️  Atualizando escalas existentes...")
                    conn.execute(db.text(
                        "UPDATE escala SET status_confirmacao = 'pendente' WHERE status_confirmacao IS NULL"
                    ))
                    conn.commit()
                    
                    # Contar total de escalas atualizadas
                    count_result = conn.execute(db.text("SELECT COUNT(*) FROM escala")).fetchone()
                    total_escalas = count_result[0] if count_result else 0
                    print(f"✅ {total_escalas} escalas atualizadas com status 'pendente'")
                
                print("\n🎉 Migração concluída com sucesso!")
                print("\n📋 Próximos passos:")
                print("   1. Reiniciar a aplicação Flask")
                print("   2. Acessar 'Minhas Escalas' como membro para testar confirmações")
                print("   3. Acessar 'Escalas' como admin e clicar em 'Status' para ver dashboard")
                
        except Exception as e:
            print(f"\n❌ Erro ao migrar tabela Escala: {e}")
            import traceback
            traceback.print_exc()
            db.session.rollback()
            return False
        
        return True

if __name__ == '__main__':
    success = migrate_add_confirmacao()
    if not success:
        print("\n⚠️  A migração falhou. Verifique os erros acima.")
        exit(1)
    else:
        print("\n✅ Script executado com sucesso!")
        exit(0)
