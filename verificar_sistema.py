"""
Script de Verificação de Saúde do Sistema
Verifica se todos os componentes estão funcionando corretamente
"""
import os
import sqlite3
from pathlib import Path

def check_file_exists(filepath, description):
    """Verifica se um arquivo existe."""
    exists = os.path.exists(filepath)
    status = "✅" if exists else "❌"
    print(f"{status} {description}: {filepath}")
    return exists

def check_directory_exists(dirpath, description):
    """Verifica se um diretório existe."""
    exists = os.path.isdir(dirpath)
    status = "✅" if exists else "❌"
    print(f"{status} {description}: {dirpath}")
    return exists

def check_database():
    """Verifica a integridade do banco de dados."""
    db_path = os.path.join('instance', 'ministry.db')
    
    if not os.path.exists(db_path):
        print("❌ Banco de dados não encontrado!")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Verificar tabelas essenciais
        tables = [
            'user', 'culto', 'escala', 'indisponibilidade',
            'repertorio', 'feedback', 'aviso', 'configuracao'
        ]
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        existing_tables = [row[0] for row in cursor.fetchall()]
        
        print("\n📊 TABELAS DO BANCO DE DADOS:")
        all_ok = True
        for table in tables:
            if table in existing_tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"  ✅ {table}: {count} registros")
            else:
                print(f"  ❌ {table}: NÃO ENCONTRADA")
                all_ok = False
        
        # Verificar coluna audio_file em repertorio
        cursor.execute("PRAGMA table_info(repertorio)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'audio_file' in columns:
            print(f"  ✅ Coluna 'audio_file' existe em 'repertorio'")
        else:
            print(f"  ❌ Coluna 'audio_file' NÃO ENCONTRADA em 'repertorio'")
            all_ok = False
        
        conn.close()
        return all_ok
    
    except Exception as e:
        print(f"❌ Erro ao verificar banco de dados: {e}")
        return False

def main():
    """Executa verificação completa do sistema."""
    print("=" * 60)
    print("🔍 VERIFICAÇÃO DE SAÚDE DO SISTEMA")
    print("=" * 60)
    
    print("\n📁 ARQUIVOS PRINCIPAIS:")
    files_ok = True
    files_ok &= check_file_exists('app.py', 'Aplicação principal')
    files_ok &= check_file_exists('requirements.txt', 'Dependências')
    files_ok &= check_file_exists('run_app.bat', 'Script de inicialização')
    
    print("\n📂 DIRETÓRIOS:")
    dirs_ok = True
    dirs_ok &= check_directory_exists('instance', 'Pasta instance')
    dirs_ok &= check_directory_exists('static', 'Pasta static')
    dirs_ok &= check_directory_exists('static/uploads', 'Pasta de uploads 🆕')
    dirs_ok &= check_directory_exists('static/js', 'Pasta JavaScript')
    dirs_ok &= check_directory_exists('templates', 'Pasta templates')
    
    print("\n🎨 TEMPLATES:")
    templates_ok = True
    templates = [
        'base.html', 'index.html', 'login.html', 'dashboard.html',
        'membros.html', 'cultos.html', 'escalas.html',
        'indisponibilidade.html', 'repertorio.html', 'avisos.html', 'feedback.html'
    ]
    for template in templates:
        templates_ok &= check_file_exists(f'templates/{template}', f'Template {template}')
    
    print("\n💾 BANCO DE DADOS:")
    db_ok = check_database()
    
    print("\n📊 JAVASCRIPT E CSS:")
    assets_ok = True
    assets_ok &= check_file_exists('static/js/script.js', 'Script principal')
    assets_ok &= check_file_exists('static/styles.css', 'Estilos CSS')
    assets_ok &= check_file_exists('static/manifest.json', 'Manifest PWA')
    assets_ok &= check_file_exists('static/sw.js', 'Service Worker')
    
    # Verificar arquivos de upload
    print("\n📁 ARQUIVOS DE UPLOAD:")
    uploads_path = 'static/uploads'
    if os.path.exists(uploads_path):
        audio_files = [f for f in os.listdir(uploads_path) if not f.startswith('.')]
        print(f"  📊 Total de arquivos de áudio: {len(audio_files)}")
        if audio_files:
            total_size = sum(os.path.getsize(os.path.join(uploads_path, f)) for f in audio_files)
            print(f"  💾 Espaço utilizado: {total_size / (1024*1024):.2f} MB")
    
    # Resultado final
    print("\n" + "=" * 60)
    all_ok = files_ok and dirs_ok and templates_ok and db_ok and assets_ok
    
    if all_ok:
        print("✅ SISTEMA 100% FUNCIONAL!")
        print("🚀 Pronto para uso em produção!")
    else:
        print("⚠️  ALGUNS PROBLEMAS ENCONTRADOS")
        print("📝 Verifique os itens marcados com ❌")
    
    print("=" * 60)
    
    return all_ok

if __name__ == '__main__':
    import sys
    result = main()
    sys.exit(0 if result else 1)
