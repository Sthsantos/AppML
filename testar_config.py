"""
Script para testar a configuração de indisponibilidade
"""
import sqlite3

def verificar_config():
    conn = sqlite3.connect('instance/database.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT * FROM configuracao WHERE chave = 'indisponibilidade_aberta'")
        config = cursor.fetchone()
        
        if config:
            print("✅ Configuração encontrada:")
            print(f"   ID: {config[0]}")
            print(f"   Chave: {config[1]}")
            print(f"   Valor: {config[2]}")
            print(f"   Status: {'ABERTO' if config[2].lower() == 'true' else 'FECHADO'}")
            print(f"   Descrição: {config[3]}")
            print(f"   Atualizado em: {config[4]}")
        else:
            print("❌ Configuração não encontrada!")
            
    except sqlite3.Error as e:
        print(f"❌ Erro: {e}")
    finally:
        conn.close()

if __name__ == '__main__':
    verificar_config()
