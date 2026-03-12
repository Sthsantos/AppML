import sqlite3

# Conectar ao banco de dados
db_path = 'instance/ministry.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("ESTRUTURA DA TABELA INDISPONIBILIDADE")
print("=" * 60)

# Verificar estrutura da tabela
cursor.execute("PRAGMA table_info(indisponibilidade)")
columns = cursor.fetchall()

if columns:
    print("\nColunas:")
    for col in columns:
        print(f"  - {col[1]} ({col[2]})")
else:
    print("Tabela não encontrada ou vazia")

# Contar registros
cursor.execute("SELECT COUNT(*) FROM indisponibilidade")
count = cursor.fetchone()[0]
print(f"\nTotal de registros: {count}")

# Pegar primeiros 5 registros
if count > 0:
    print("\nPrimeiros 5 registros:")
    cursor.execute("SELECT * FROM indisponibilidade LIMIT 5")
    rows = cursor.fetchall()
    for row in rows:
        print(f"  {row}")

conn.close()
