"""
Script de migração universal (SQLite + PostgreSQL).
Adiciona colunas de confirmação à tabela Escala no Render.

Uso no Render Shell:
    python migrate_db_render.py
"""
from app import app, db
import os

def get_db_type():
    """Detecta se está usando SQLite ou PostgreSQL."""
    db_url = os.environ.get('DATABASE_URL', '')
    if 'postgresql' in db_url or 'postgres' in db_url:
        return 'postgresql'
    return 'sqlite'

def check_column_exists_postgres(conn, table_name, column_name):
    """Verifica se coluna existe no PostgreSQL."""
    query = db.text("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = :table AND column_name = :column
    """)
    result = conn.execute(query, {'table': table_name, 'column': column_name}).fetchone()
    return result is not None

def check_column_exists_sqlite(conn, table_name, column_name):
    """Verifica se coluna existe no SQLite."""
    result = conn.execute(db.text(f"PRAGMA table_info({table_name})")).fetchall()
    columns = [row[1] for row in result]
    return column_name in columns

def migrate_add_confirmacao():
    """Adiciona colunas de confirmação à tabela Escala."""
    with app.app_context():
        db_type = get_db_type()
        print(f"🔄 Iniciando migração no {db_type.upper()}...")
        
        # Criar tabelas se não existirem
        db.create_all()
        
        try:
            # Usar begin() para transação adequada
            with db.engine.begin() as conn:
                # Escolher função de verificação baseada no tipo de banco
                if db_type == 'postgresql':
                    check_exists = check_column_exists_postgres
                else:
                    check_exists = check_column_exists_sqlite
                
                changes_made = False
                
                # Adicionar status_confirmacao se não existir
                if not check_exists(conn, 'escala', 'status_confirmacao'):
                    print("⚙️  Adicionando coluna 'status_confirmacao'...")
                    if db_type == 'postgresql':
                        conn.execute(db.text(
                            "ALTER TABLE escala ADD COLUMN status_confirmacao VARCHAR(20) DEFAULT 'pendente'"
                        ))
                    else:
                        conn.execute(db.text(
                            "ALTER TABLE escala ADD COLUMN status_confirmacao VARCHAR(20) DEFAULT 'pendente'"
                        ))
                    print("✅ Coluna 'status_confirmacao' adicionada")
                    changes_made = True
                else:
                    print("ℹ️  Coluna 'status_confirmacao' já existe")
                
                # Adicionar data_confirmacao se não existir
                if not check_exists(conn, 'escala', 'data_confirmacao'):
                    print("⚙️  Adicionando coluna 'data_confirmacao'...")
                    if db_type == 'postgresql':
                        conn.execute(db.text(
                            "ALTER TABLE escala ADD COLUMN data_confirmacao TIMESTAMP NULL"
                        ))
                    else:
                        conn.execute(db.text(
                            "ALTER TABLE escala ADD COLUMN data_confirmacao DATETIME NULL"
                        ))
                    print("✅ Coluna 'data_confirmacao' adicionada")
                    changes_made = True
                else:
                    print("ℹ️  Coluna 'data_confirmacao' já existe")
                
                # Adicionar observacao_confirmacao se não existir
                if not check_exists(conn, 'escala', 'observacao_confirmacao'):
                    print("⚙️  Adicionando coluna 'observacao_confirmacao'...")
                    conn.execute(db.text(
                        "ALTER TABLE escala ADD COLUMN observacao_confirmacao TEXT NULL"
                    ))
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
                    
                    # Contar escalas atualizadas
                    count_result = conn.execute(db.text("SELECT COUNT(*) FROM escala")).fetchone()
                    total = count_result[0] if count_result else 0
                    print(f"✅ {total} escalas atualizadas com status 'pendente'")
                
                print("\n🎉 Migração concluída com sucesso!")
                
        except Exception as e:
            print(f"\n❌ Erro na migração: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        return True

if __name__ == '__main__':
    success = migrate_add_confirmacao()
    if not success:
        print("\n⚠️  Migração falhou!")
        exit(1)
    else:
        print("\n✅ Migração executada com sucesso!")
        print("\n📌 REINICIE a aplicação no Render para aplicar mudanças")
        exit(0)
