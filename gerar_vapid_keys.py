"""
Script para gerar chaves VAPID para Push Notifications.
Execute este script uma vez para gerar as chaves e adicione-as ao .env

Uso:
    python gerar_vapid_keys.py
"""
import json
import base64

def generate_vapid_keys():
    """Gera um par de chaves VAPID (pública e privada)."""
    try:
        from py_vapid import Vapid
        from cryptography.hazmat.primitives import serialization
        
        # Gerar chaves
        vapid = Vapid()
        vapid.generate_keys()
        
        # Exportar chave pública no formato correto (base64 url-safe)
        public_key_bytes = vapid.public_key.public_bytes(
            encoding=serialization.Encoding.X962,
            format=serialization.PublicFormat.UncompressedPoint
        )
        public_key_base64 = base64.urlsafe_b64encode(public_key_bytes).strip(b'=').decode('utf-8')
        
        # Exportar chave privada no formato PEM
        private_key_bytes = vapid.private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        private_key_pem = private_key_bytes.decode('utf-8')
        
        print("\n" + "=" * 60)
        print("🔑 CHAVES VAPID GERADAS COM SUCESSO!")
        print("=" * 60)
        print("\n📋 COPIE estas chaves para seu arquivo .env:")
        print("-" * 60)
        print(f"\nVAPID_PUBLIC_KEY={public_key_base64}")
        print(f"VAPID_PRIVATE_KEY={private_key_pem}")
        print(f"VAPID_CLAIMS_EMAIL=mailto:admin@ministry.com")
        print("-" * 60)
        
        # Salvar em arquivo para referência
        with open('vapid_keys.json', 'w') as f:
            json.dump({
                'public_key': public_key_base64,
                'private_key': private_key_pem,
                'claims_email': 'mailto:admin@ministry.com'
            }, f, indent=4)
        
        print("\n✅ Chaves também salvas em 'vapid_keys.json' para backup")
        print("\n⚠️  IMPORTANTE:")
        print("   1. Adicione estas chaves ao arquivo .env")
        print("   2. NUNCA compartilhe a PRIVATE_KEY publicamente")
        print("   3. Adicione 'vapid_keys.json' ao .gitignore")
        print("   4. Guarde estas chaves em local seguro")
        print("\n" + "=" * 60)
        
        return {'public_key': public_key_base64, 'private_key': private_key_pem}
        
    except Exception as e:
        print(f"\n❌ Erro ao gerar chaves VAPID: {e}")
        print("\n💡 Certifique-se de ter instalado: pip install pywebpush")
        import traceback
        traceback.print_exc()
        return None

if __name__ == '__main__':
    print("\n🔐 Gerador de Chaves VAPID para Push Notifications\n")
    generate_vapid_keys()
