"""
🔍 DIAGNÓSTICO DE BANCO DE DADOS
Este script verifica qual banco de dados está configurado e sua situação.
"""

import os
from app import app, db
import sys

def diagnostico():
    print("\n" + "="*60)
    print("🔍 DIAGNÓSTICO DO BANCO DE DADOS")
    print("="*60 + "\n")
    
    # 1. Verificar variável de ambiente
    database_url = os.environ.get('DATABASE_URL')
    
    print("📌 VARIÁVEL DE AMBIENTE 'DATABASE_URL':")
    if database_url:
        # Ocultar senha
        if '@' in database_url:
            parts = database_url.split('@')
            user_part = parts[0].split('://')[0] + '://' + parts[0].split('://')[1].split(':')[0] + ':***'
            masked_url = user_part + '@' + parts[1]
            print(f"   ✅ Configurada: {masked_url}")
        else:
            print(f"   ✅ Configurada: {database_url}")
    else:
        print("   ❌ NÃO configurada (usando SQLite padrão)")
    
    print()
    
    # 2. Verificar configuração do app
    app_db_uri = app.config['SQLALCHEMY_DATABASE_URI']
    
    print("📌 BANCO CONFIGURADO NO APP:")
    if 'sqlite' in app_db_uri.lower():
        print("   ⚠️  SQLite (arquivo local)")
        print(f"   📁 Localização: {app_db_uri.replace('sqlite:///', '')}")
        print()
        print("   🔴 ATENÇÃO: SQLite NÃO é recomendado para produção no Render!")
        print("   🔴 Os dados serão PERDIDOS quando o app dormir!")
        print()
        print("   ➡️  Solução: Configure PostgreSQL seguindo SOLUCAO_DADOS_PERDIDOS.md")
        resultado = "PROBLEMA"
    elif 'postgresql' in app_db_uri.lower() or 'postgres' in app_db_uri.lower():
        # Ocultar senha
        if '@' in app_db_uri:
            parts = app_db_uri.split('@')
            user_part = parts[0].split('://')[0] + '://' + parts[0].split('://')[1].split(':')[0] + ':***'
            masked_uri = user_part + '@' + parts[1]
            print(f"   ✅ PostgreSQL: {masked_uri}")
        else:
            print(f"   ✅ PostgreSQL: {app_db_uri}")
        print()
        print("   🟢 EXCELENTE! PostgreSQL está configurado corretamente!")
        print("   🟢 Seus dados são PERSISTENTES e NÃO serão perdidos!")
        resultado = "OK"
    else:
        print(f"   ⚠️  Desconhecido: {app_db_uri}")
        resultado = "DESCONHECIDO"
    
    print()
    
    # 3. Verificar conexão com banco
    print("📌 TESTE DE CONEXÃO:")
    try:
        with app.app_context():
            # Tentar executar uma query simples
            db.session.execute(db.text('SELECT 1'))
            print("   ✅ Conexão com banco bem-sucedida!")
    except Exception as e:
        print(f"   ❌ ERRO ao conectar: {e}")
        resultado = "ERRO"
    
    print()
    
    # 4. Verificar tabelas
    print("📌 TABELAS NO BANCO:")
    try:
        with app.app_context():
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            
            if tables:
                print(f"   ✅ {len(tables)} tabelas encontradas:")
                for table in sorted(tables):
                    print(f"      - {table}")
            else:
                print("   ⚠️  Nenhuma tabela encontrada!")
                print("   ℹ️  Execute: python app.py para criar as tabelas")
    except Exception as e:
        print(f"   ❌ ERRO ao listar tabelas: {e}")
    
    print()
    
    # 5. Resumo final
    print("="*60)
    print("📊 RESUMO:")
    print("="*60)
    
    if resultado == "OK":
        print("✅ Status: TUDO OK!")
        print("✅ Banco: PostgreSQL configurado corretamente")
        print("✅ Seus dados estão seguros e persistentes")
        print()
        print("📌 Próximos passos:")
        print("   1. Certifique-se de ter cadastrado os dados necessários")
        print("   2. Altere a senha do admin se ainda não fez")
        print("   3. Monitore o uso do PostgreSQL no dashboard do Render")
        
    elif resultado == "PROBLEMA":
        print("🔴 Status: PROBLEMA IDENTIFICADO!")
        print("🔴 Banco: SQLite (dados serão perdidos no Render)")
        print()
        print("📌 AÇÃO NECESSÁRIA:")
        print("   1. Abra o arquivo: SOLUCAO_DADOS_PERDIDOS.md")
        print("   2. Siga o PASSO A PASSO para configurar PostgreSQL")
        print("   3. Leva apenas 5-10 minutos!")
        print()
        print("⚠️  URGENTE: Seus dados serão perdidos quando o app dormir!")
        
    else:
        print("⚠️  Status: Situação desconhecida ou erro")
        print("📞 Verifique os logs acima para mais detalhes")
    
    print("="*60 + "\n")
    
    return resultado == "OK"

if __name__ == '__main__':
    try:
        sucesso = diagnostico()
        sys.exit(0 if sucesso else 1)
    except Exception as e:
        print(f"\n❌ ERRO FATAL: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
