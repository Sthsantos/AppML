#!/usr/bin/env python3
"""Gera VAPID keys e atualiza .env automaticamente."""
import subprocess
import sys
import os

def instalar_py_vapid():
    """Instala py-vapid se necessário."""
    try:
        import py_vapid
        print("✅ py-vapid já instalado")
        return True
    except ImportError:
        print("📦 Instalando py-vapid...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "py-vapid"])
            print("✅ py-vapid instalado com sucesso!")
            return True
        except Exception as e:
            print(f"❌ Erro ao instalar py-vapid: {e}")
            return False

def gerar_e_atualizar():
    """Gera novas VAPID keys e atualiza o .env."""
    if not instalar_py_vapid():
        return
    
    from py_vapid import Vapid
    import base64
    from cryptography.hazmat.primitives import serialization
    
    print("\n" + "="*60)
    print("  GERANDO NOVAS VAPID KEYS")
    print("="*60 + "\n")
    
    # Gerar keys
    vapid = Vapid()
    vapid.generate_keys()
    
    # Extrair public key em formato URL-safe base64
    public_bytes = vapid.public_key.public_bytes(
        encoding=serialization.Encoding.X962,
        format=serialization.PublicFormat.UncompressedPoint
    )
    public_key = base64.urlsafe_b64encode(public_bytes).decode('utf-8').rstrip('=')
    
    # Extrair private key em formato PEM
    private_key_pem = vapid.private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    ).decode('utf-8')
    
    print(f"✅ Keys geradas com sucesso!")
    print(f"\n📌 Public Key:\n{public_key}\n")
    
    # Atualizar .env
    env_path = ".env"
    
    try:
        # Ler .env atual
        with open(env_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Atualizar as linhas VAPID
        new_lines = []
        for line in lines:
            if line.startswith('VAPID_PUBLIC_KEY='):
                new_lines.append(f'VAPID_PUBLIC_KEY={public_key}\n')
            elif line.startswith('VAPID_PRIVATE_KEY='):
                # Salvar a private key em uma linha única (escapando quebras de linha)
                private_key_escaped = private_key_pem.replace('\n', '\\n')
                new_lines.append(f'VAPID_PRIVATE_KEY={private_key_escaped}\n')
            else:
                new_lines.append(line)
        
        # Salvar .env atualizado
        with open(env_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        
        print(f"✅ Arquivo .env atualizado com sucesso!")
        print(f"\n" + "="*60)
        print("  PRÓXIMOS PASSOS")
        print("="*60)
        print("\n1. Reinicie o servidor Flask (Ctrl+C e python app.py)")
        print("2. IMPORTANTE: Você precisa REATIVAR as notificações no navegador!")
        print("   - Vá em http://localhost:5000/perfil")
        print("   - DESATIVE o toggle de notificações")
        print("   - ATIVE novamente (permita quando pedir)")
        print("3. Teste criando um aviso")
        print("\n" + "="*60 + "\n")
        
    except Exception as e:
        print(f"❌ Erro ao atualizar .env: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    gerar_e_atualizar()
