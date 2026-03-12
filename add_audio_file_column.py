"""
Script para adicionar a coluna audio_file à tabela repertorio.
Execute este script uma vez para migrar o banco de dados.
"""
import sqlite3
import os

# Caminho do banco de dados
DB_PATH = os.path.join('instance', 'ministry.db')

def add_audio_file_column():
    """Adiciona a coluna audio_file à tabela repertorio se ainda não existir."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Verifica se a coluna já existe
        cursor.execute("PRAGMA table_info(repertorio)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'audio_file' not in columns:
            # Adiciona a coluna
            cursor.execute("ALTER TABLE repertorio ADD COLUMN audio_file VARCHAR(300)")
            conn.commit()
            print("✅ Coluna 'audio_file' adicionada com sucesso à tabela 'repertorio'.")
        else:
            print("ℹ️  Coluna 'audio_file' já existe na tabela 'repertorio'.")
    
    except sqlite3.Error as e:
        print(f"❌ Erro ao adicionar coluna: {e}")
        conn.rollback()
    
    finally:
        conn.close()

if __name__ == '__main__':
    if os.path.exists(DB_PATH):
        print(f"📁 Banco de dados encontrado: {DB_PATH}")
        add_audio_file_column()
    else:
        print(f"❌ Banco de dados não encontrado em: {DB_PATH}")
        print("   O banco será criado automaticamente quando você iniciar a aplicação.")
