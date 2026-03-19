#!/usr/bin/env python3
"""Testa criação de aviso via API diretamente."""
import requests
import json

def testar_aviso():
    print("\n" + "="*60)
    print("  TESTANDO CRIAÇÃO DE AVISO VIA API")
    print("="*60 + "\n")
    
    # URL do servidor
    url = "http://localhost:5000/add_aviso"
    
    # Dados do aviso
    dados = {
        "title": "🧪 Teste de Notificação Push",
        "message": "Este é um teste automático para verificar se as notificações push estão funcionando corretamente!",
        "priority": "high"
    }
    
    print("📤 Enviando requisição POST para /add_aviso...")
    print(f"   Título: {dados['title']}")
    print(f"   Prioridade: {dados['priority']}\n")
    
    try:
        # Fazer login primeiro
        print("🔐 Fazendo login...")
        session = requests.Session()
        login_response = session.post(
            "http://localhost:5000/login",
            data={
                "email": "admin@ministry.com",
                "password": "admin123"
            },
            allow_redirects=False
        )
        
        if login_response.status_code in [200, 302]:
            print("   ✅ Login realizado!\n")
            
            # Criar aviso
            print("📝 Criando aviso...")
            response = session.post(
                url,
                json=dados,
                headers={"Content-Type": "application/json"}
            )
            
            print(f"   Status Code: {response.status_code}")
            print(f"   Resposta: {response.text}\n")
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    print("✅ AVISO CRIADO COM SUCESSO!")
                    print("\n⚠️ AGORA OLHE O TERMINAL DO FLASK!")
                    print("   Deve ter aparecido os logs de envio de notificação.\n")
                    print("📱 Verifique se recebeu a notificação push!\n")
                else:
                    print(f"❌ Erro: {result.get('message')}\n")
            else:
                print(f"❌ Erro HTTP {response.status_code}\n")
        else:
            print(f"   ❌ Falha no login (Status: {login_response.status_code})\n")
            
    except Exception as e:
        print(f"❌ Erro: {e}\n")
        import traceback
        traceback.print_exc()
    
    print("="*60 + "\n")

if __name__ == '__main__':
    testar_aviso()
