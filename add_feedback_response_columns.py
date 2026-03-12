"""
Script para adicionar campos de resposta à tabela Feedback
"""
import sqlite3
import os

# Caminho do banco de dados
db_path = os.path.join('instance', 'ministry.db')

if not os.path.exists(db_path):
    print(f"❌ Banco de dados não encontrado em: {db_path}")
    exit(1)

print(f"📂 Conectando ao banco de dados: {db_path}")

# Conectar ao banco de dados
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("\n🔍 Verificando estrutura atual da tabela Feedback...")

# Verificar colunas existentes
cursor.execute("PRAGMA table_info(feedback)")
columns = cursor.fetchall()
existing_columns = [col[1] for col in columns]

print(f"Colunas existentes: {', '.join(existing_columns)}")

# Adicionar novas colunas se não existirem
columns_to_add = [
    ('response', 'TEXT'),
    ('responded_at', 'DATETIME'),
    ('responded_by', 'INTEGER')
]

for column_name, column_type in columns_to_add:
    if column_name not in existing_columns:
        print(f"\n➕ Adicionando coluna '{column_name}' ({column_type})...")
        try:
            cursor.execute(f"ALTER TABLE feedback ADD COLUMN {column_name} {column_type}")
            print(f"✅ Coluna '{column_name}' adicionada com sucesso!")
        except sqlite3.Error as e:
            print(f"⚠️ Erro ao adicionar '{column_name}': {e}")
    else:
        print(f"✓ Coluna '{column_name}' já existe")

# Commit e fechar
conn.commit()
conn.close()

print("\n✅ Migração concluída com sucesso!")
print("\n🔍 Verificando estrutura final...")

# Verificar novamente
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute("PRAGMA table_info(feedback)")
columns = cursor.fetchall()

print("\nEstrutura da tabela Feedback:")
for col in columns:
    print(f"  - {col[1]} ({col[2]})")

conn.close()
