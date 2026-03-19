"""
Script de teste manual para verificar o sistema de Push Notifications
Execute este script enquanto o servidor está rodando
"""
import requests
import json

def testar_push_system():
    """Testa os endpoints de push notifications."""
    
    base_url = "http://127.0.0.1:5000"
    
    print("\n" + "=" * 60)
    print("🧪 TESTE MANUAL: Push Notifications")
    print("=" * 60 + "\n")
    
    # Teste 1: Verificar chave pública VAPID
    print("1️⃣ Testando endpoint /get_vapid_public_key...")
    try:
        response = requests.get(f"{base_url}/get_vapid_public_key", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Status: {response.status_code}")
            print(f"   ✅ Chave pública: {data.get('publicKey', 'N/A')[:30]}...")
        else:
            print(f"   ❌ Status: {response.status_code}")
            print(f"   ❌ Resposta: {response.text}")
    except Exception as e:
        print(f"   ❌ Erro: {e}")
    
    # Teste 2: Verificar se perfil.html está acessível
    print("\n2️⃣ Testando acesso à página /perfil...")
    try:
        # Nota: Precisará estar logado para ver esta página
        response = requests.get(f"{base_url}/perfil", timeout=5, allow_redirects=False)
        if response.status_code in [200, 302]:
            print(f"   ✅ Status: {response.status_code} (página existe)")
            if response.status_code == 302:
                print(f"   ℹ️  Redirecionamento para login (esperado se não logado)")
        else:
            print(f"   ❌ Status: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Erro: {e}")
    
    # Teste 3: Verificar se push-manager.js está acessível
    print("\n3️⃣ Testando arquivo /static/js/push-manager.js...")
    try:
        response = requests.get(f"{base_url}/static/js/push-manager.js", timeout=5)
        if response.status_code == 200:
            content = response.text
            print(f"   ✅ Status: {response.status_code}")
            print(f"   ✅ Tamanho: {len(content)} bytes")
            
            # Verificar se tem as funções principais
            if 'PushManager' in content:
                print(f"   ✅ Contém objeto PushManager")
            if 'subscribe' in content:
                print(f"   ✅ Contém função subscribe")
            if 'updateUI' in content:
                print(f"   ✅ Contém função updateUI")
        else:
            print(f"   ❌ Status: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Erro: {e}")
    
    # Teste 4: Verificar Service Worker
    print("\n4️⃣ Testando Service Worker /static/sw.js...")
    try:
        response = requests.get(f"{base_url}/static/sw.js", timeout=5)
        if response.status_code == 200:
            content = response.text
            print(f"   ✅ Status: {response.status_code}")
            
            # Verificar handlers de push
            if "addEventListener('push'" in content:
                print(f"   ✅ Contém handler de 'push'")
            else:
                print(f"   ❌ Handler 'push' não encontrado")
            
            if "addEventListener('notificationclick'" in content:
                print(f"   ✅ Contém handler de 'notificationclick'")
            else:
                print(f"   ❌ Handler 'notificationclick' não encontrado")
        else:
            print(f"   ❌ Status: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Erro: {e}")
    
    # Instruções para teste manual
    print("\n" + "=" * 60)
    print("📋 INSTRUÇÕES PARA TESTE MANUAL NO NAVEGADOR")
    print("=" * 60)
    print("\n1️⃣ Abra o navegador e vá para: http://127.0.0.1:5000/perfil")
    print("   (Faça login se necessário)")
    print("\n2️⃣ Abra o Console do Desenvolvedor:")
    print("   - Chrome/Edge: F12 → Console")
    print("   - Firefox: F12 → Console")
    print("\n3️⃣ Digite no console:")
    print("   console.log(window.PushManager)")
    print("   → Deve mostrar o objeto PushManager")
    print("\n4️⃣ Verifique se aparece a seção 'Notificações Push' na página")
    print("\n5️⃣ Procure por mensagens de erro no console começando com '[Push]'")
    print("\n6️⃣ Se não aparecer a seção, verifique:")
    print("   - Se push-manager.js foi carregado (aba Network → JS)")
    print("   - Se há erros JavaScript no console")
    print("   - Se o Service Worker está ativo (Application → Service Workers)")
    
    print("\n" + "=" * 60)
    print("🔍 COMANDOS DE TESTE NO CONSOLE DO NAVEGADOR")
    print("=" * 60)
    print("\nCole estes comandos no console para diagnosticar:")
    print("\n// 1. Verificar se PushManager existe")
    print("console.log('PushManager:', window.PushManager);")
    print("\n// 2. Verificar Service Worker")
    print("navigator.serviceWorker.ready.then(sw => console.log('SW:', sw));")
    print("\n// 3. Verificar suporte a notificações")
    print("console.log('Notification permission:', Notification.permission);")
    print("\n// 4. Testar busca da chave VAPID")
    print("fetch('/get_vapid_public_key').then(r => r.json()).then(d => console.log('VAPID:', d));")
    print("\n// 5. Verificar se elementos existem")
    print("console.log('Toggle:', document.getElementById('pushNotificationToggle'));")
    print("console.log('Status:', document.getElementById('pushStatus'));")
    
    print("\n" + "=" * 60 + "\n")

if __name__ == '__main__':
    print("\n⚠️  IMPORTANTE: O servidor Flask deve estar rodando!")
    print("Execute em outro terminal: python app.py\n")
    
    input("Pressione ENTER quando o servidor estiver rodando...")
    testar_push_system()
