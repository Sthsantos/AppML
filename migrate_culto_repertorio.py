"""
Script de migração para criar a tabela culto_repertorio
Relacionamento many-to-many entre Culto e Repertorio
"""

import sqlite3
import os

# Caminho do banco de dados
db_path = os.path.join(os.path.dirname(__file__), 'instance', 'ministry.db')

print("=" * 60)
print("MIGRAÇÃO: Adicionando tabela culto_repertorio")
print("=" * 60)

try:
    # Conectar ao banco
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Verificar se a tabela já existe
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='culto_repertorio'
    """)
    
    if cursor.fetchone():
        print("✓ Tabela 'culto_repertorio' já existe!")
    else:
        # Criar a tabela de associação
        cursor.execute("""
            CREATE TABLE culto_repertorio (
                culto_id INTEGER NOT NULL,
                repertorio_id INTEGER NOT NULL,
                "order" INTEGER DEFAULT 0,
                PRIMARY KEY (culto_id, repertorio_id),
                FOREIGN KEY (culto_id) REFERENCES culto(id),
                FOREIGN KEY (repertorio_id) REFERENCES repertorio(id)
            )
        """)
        
        conn.commit()
        print("✓ Tabela 'culto_repertorio' criada com sucesso!")
    
    # Verificar estrutura da tabela
    cursor.execute("PRAGMA table_info(culto_repertorio)")
    columns = cursor.fetchall()
    
    print("\n📋 Estrutura da tabela:")
    print("-" * 60)
    for col in columns:
        print(f"   {col[1]:20s} {col[2]:15s} {'NOT NULL' if col[3] else ''}")
    print("-" * 60)
    
    # Contar registros
    cursor.execute("SELECT COUNT(*) FROM culto_repertorio")
    count = cursor.fetchone()[0]
    print(f"\n📊 Registros na tabela: {count}")
    
    conn.close()
    
    print("\n" + "=" * 60)
    print("✅ MIGRAÇÃO CONCLUÍDA COM SUCESSO!")
    print("=" * 60)
    print("\nPróximos passos:")
    print("1. Reinicie o servidor Flask (python app.py)")
    print("2. Acesse a página de Escalas")
    print("3. Clique no botão 'Músicas' em qualquer escala")
    print("4. Selecione músicas do repertório para o culto")
    print()

except sqlite3.Error as e:
    print(f"\n❌ Erro na migração: {e}")
    print("\nVerifique se:")
    print("1. O arquivo ministry.db existe em 'instance/'")
    print("2. O banco não está sendo usado por outro processo")
    print("3. Você tem permissões de escrita no diretório")

except Exception as e:
    print(f"\n❌ Erro inesperado: {e}")
