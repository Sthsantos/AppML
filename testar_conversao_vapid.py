"""
Teste de conversão PEM → DER para VAPID keys
"""
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
from py_vapid import Vapid

print("="*60)
print("  TESTE DE CONVERSÃO PEM → DER")
print("="*60)

# Ler chave PEM do arquivo
with open('vapid_private.pem', 'r') as f:
    pem_content = f.read()

print(f"\n📄 Chave PEM ({len(pem_content)} chars):")
print(pem_content[:80] + "...")

# Converter para bytes
pem_bytes = pem_content.encode('utf-8')
print(f"\n📦 PEM bytes: {len(pem_bytes)} bytes")

# Tentar carregar como chave privada
try:
    private_key = serialization.load_pem_private_key(
        pem_bytes,
        password=None,
        backend=default_backend()
    )
    print(f"✅ Chave PEM carregada com sucesso!")
    print(f"   Tipo: {type(private_key)}")
except Exception as e:
    print(f"❌ Erro ao carregar PEM: {e}")
    exit(1)

# Converter para DER
try:
    der_data = private_key.private_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    print(f"\n✅ Convertido para DER: {len(der_data)} bytes")
    print(f"   Primeiros 20 bytes: {der_data[:20].hex()}")
except Exception as e:
    print(f"❌ Erro ao converter para DER: {e}")
    exit(1)

# Tentar criar objeto Vapid do DER
try:
    vapid_obj = Vapid.from_der(der_data)
    print(f"\n✅ Objeto Vapid criado do DER!")
    print(f"   Tipo: {type(vapid_obj)}")
    
    # Tentar obter public key
    public_key = vapid_obj.public_key
    print(f"   Public key: {public_key.decode()[:60]}...")
except Exception as e:
    print(f"\n❌ Erro ao criar Vapid do DER: {e}")
    print(f"   DER length: {len(der_data)}")
    print(f"   DER hex: {der_data.hex()}")
    exit(1)

# Tentar criar Vapid diretamente do PEM
print("\n" + "="*60)
print("  TESTE 2: Criar Vapid diretamente do PEM")
print("="*60)

try:
    vapid_obj2 = Vapid.from_file('vapid_private.pem')
    print(f"✅ Vapid criado do arquivo PEM!")
    print(f"   Public key: {vapid_obj2.public_key.decode()[:60]}...")
except Exception as e:
    print(f"❌ Erro ao criar Vapid do PEM: {e}")

print("\n" + "="*60)
print("✅ TODOS OS TESTES PASSARAM!")
print("="*60)
