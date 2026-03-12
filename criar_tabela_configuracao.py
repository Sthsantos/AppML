"""
Script para criar tabela de configuração do sistema
"""
import sqlite3
from datetime import datetime

def criar_tabela_configuracao():
    """Cria a tabela de configuração e adiciona registro padrão."""
    conn = sqlite3.connect('instance/database.db')
    cursor = conn.cursor()
    
    try:
        # Criar tabela configuracao
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS configuracao (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chave VARCHAR(100) UNIQUE NOT NULL,
                valor VARCHAR(200) NOT NULL,
                descricao VARCHAR(300),
                atualizado_em TIMESTAMP
            )
        ''')
        
        # Verificar se já existe configuração de indisponibilidade
        cursor.execute("SELECT * FROM configuracao WHERE chave = 'indisponibilidade_aberta'")
        existe = cursor.fetchone()
        
        if not existe:
            # Adicionar configuração padrão (fechado)
            cursor.execute('''
                INSERT INTO configuracao (chave, valor, descricao, atualizado_em)
                VALUES (?, ?, ?, ?)
            ''', (
                'indisponibilidade_aberta',
                'false',
                'Controla se membros podem registrar indisponibilidades',
                datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
            ))
            print("✅ Configuração padrão criada (período FECHADO)")
        else:
            print("ℹ️  Configuração já existe no banco de dados")
        
        conn.commit()
        print("✅ Tabela 'configuracao' criada/verificada com sucesso!")
        
        # Exibir configuração atual
        cursor.execute("SELECT * FROM configuracao WHERE chave = 'indisponibilidade_aberta'")
        config = cursor.fetchone()
        if config:
            print(f"\n📋 Configuração atual:")
            print(f"   Chave: {config[1]}")
            print(f"   Valor: {config[2]}")
            print(f"   Status: {'ABERTO' if config[2].lower() == 'true' else 'FECHADO'}")
            print(f"   Descrição: {config[3]}")
            print(f"   Atualizado em: {config[4]}")
        
    except sqlite3.Error as e:
        print(f"❌ Erro ao criar tabela: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    criar_tabela_configuracao()
