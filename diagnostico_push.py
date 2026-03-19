"""
Script de diagnóstico para Push Notifications
Verifica se tudo está configurado corretamente
"""
import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

def diagnostico_push():
    """Executa diagnóstico completo do sistema de push notifications."""
    
    print("\n" + "=" * 60)
    print("🔍 DIAGNÓSTICO: Sistema de Push Notifications")
    print("=" * 60 + "\n")
    
    erros = []
    avisos = []
    
    # 1. Verificar VAPID Keys
    print("1️⃣ Verificando VAPID Keys...")
    vapid_public = os.environ.get('VAPID_PUBLIC_KEY')
    vapid_private = os.environ.get('VAPID_PRIVATE_KEY')
    vapid_email = os.environ.get('VAPID_CLAIMS_EMAIL')
    
    if not vapid_public:
        erros.append("❌ VAPID_PUBLIC_KEY não encontrada no .env")
    else:
        print(f"   ✅ VAPID_PUBLIC_KEY: {vapid_public[:20]}...")
    
    if not vapid_private:
        erros.append("❌ VAPID_PRIVATE_KEY não encontrada no .env")
    else:
        # Verificar se é uma chave PEM válida
        if "BEGIN PRIVATE KEY" in vapid_private:
            print(f"   ✅ VAPID_PRIVATE_KEY: Formato PEM válido")
        else:
            erros.append("❌ VAPID_PRIVATE_KEY não está em formato PEM")
    
    if not vapid_email:
        avisos.append("⚠️  VAPID_CLAIMS_EMAIL não configurado (usando padrão)")
    else:
        print(f"   ✅ VAPID_CLAIMS_EMAIL: {vapid_email}")
    
    # 2. Verificar biblioteca pywebpush
    print("\n2️⃣ Verificando biblioteca pywebpush...")
    try:
        import pywebpush
        print(f"   ✅ pywebpush instalada")
    except ImportError:
        erros.append("❌ pywebpush não está instalada. Execute: pip install pywebpush==1.14.0")
    
    # 3. Verificar py-vapid
    print("\n3️⃣ Verificando biblioteca py-vapid...")
    try:
        import py_vapid
        print(f"   ✅ py-vapid instalada")
    except ImportError:
        avisos.append("⚠️  py-vapid não encontrada (será instalada automaticamente com pywebpush)")
    
    # 4. Verificar arquivos do sistema
    print("\n4️⃣ Verificando arquivos do sistema...")
    
    arquivos_necessarios = [
        'static/js/push-manager.js',
        'static/sw.js',
        'migrate_add_push_subscription.py',
        'gerar_vapid_keys.py'
    ]
    
    for arquivo in arquivos_necessarios:
        if os.path.exists(arquivo):
            print(f"   ✅ {arquivo}")
        else:
            erros.append(f"❌ Arquivo não encontrado: {arquivo}")
    
    # 5. Verificar banco de dados
    print("\n5️⃣ Verificando banco de dados...")
    try:
        from app import app, db, PushSubscription
        with app.app_context():
            # Verificar se a tabela existe
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            
            if 'push_subscription' in inspector.get_table_names():
                print(f"   ✅ Tabela 'push_subscription' existe")
                
                # Contar subscrições
                count = PushSubscription.query.count()
                print(f"   📊 {count} subscrição(ões) registrada(s)")
            else:
                erros.append("❌ Tabela 'push_subscription' não existe. Execute: python migrate_add_push_subscription.py")
    except Exception as e:
        avisos.append(f"⚠️  Não foi possível verificar banco de dados: {e}")
    
    # 6. Verificar Service Worker
    print("\n6️⃣ Verificando Service Worker...")
    try:
        with open('static/sw.js', 'r', encoding='utf-8') as f:
            conteudo = f.read()
            if 'push' in conteudo and 'notificationclick' in conteudo:
                print(f"   ✅ Service Worker com handlers de push")
            else:
                erros.append("❌ Service Worker não tem handlers de push/notificationclick")
    except Exception as e:
        erros.append(f"❌ Erro ao ler sw.js: {e}")
    
    # Resumo
    print("\n" + "=" * 60)
    print("📋 RESUMO DO DIAGNÓSTICO")
    print("=" * 60 + "\n")
    
    if not erros and not avisos:
        print("🎉 TUDO PERFEITO! Sistema de push notifications está pronto.")
        print("\n📱 Próximos passos:")
        print("   1. Inicie o servidor: python app.py")
        print("   2. Acesse /perfil no navegador")
        print("   3. Clique em 'Ativar Notificações'")
        print("   4. Teste com o botão 'Enviar Teste'")
    else:
        if erros:
            print("❌ ERROS ENCONTRADOS:")
            for erro in erros:
                print(f"   {erro}")
        
        if avisos:
            print("\n⚠️  AVISOS:")
            for aviso in avisos:
                print(f"   {aviso}")
        
        print("\n💡 AÇÕES NECESSÁRIAS:")
        if any("VAPID" in e for e in erros):
            print("   - Execute: python gerar_vapid_keys.py")
            print("   - Adicione as chaves ao arquivo .env")
        
        if any("pywebpush" in e for e in erros):
            print("   - Execute: pip install pywebpush==1.14.0")
        
        if any("push_subscription" in e for e in erros):
            print("   - Execute: python migrate_add_push_subscription.py")
    
    print("\n" + "=" * 60 + "\n")
    
    return len(erros) == 0

if __name__ == '__main__':
    diagnostico_push()
