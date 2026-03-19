import subprocess
import sys
import base64

# Verificar/instalar py-vapid
try:
    from py_vapid import Vapid
    from cryptography.hazmat.primitives import serialization
except ImportError:
    print("📦 Instalando py-vapid...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "py-vapid"])
    from py_vapid import Vapid
    from cryptography.hazmat.primitives import serialization

print("\n" + "="*60)
print("  GERANDO NOVAS CHAVES VAPID (Web Push Format)")
print("="*60 + "\n")

# Gerar chaves
vapid = Vapid()
vapid.generate_keys()

# Exportar private key em PEM format
private_pem = vapid.private_key.private_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PrivateFormat.PKCS8,
    encryption_algorithm=serialization.NoEncryption()
).decode('utf-8')

# Exportar public key em URL-safe base64 (formato Web Push)
public_bytes_raw = vapid.public_key.public_bytes(
    encoding=serialization.Encoding.X962,
    format=serialization.PublicFormat.UncompressedPoint
)
public_key_b64 = base64.urlsafe_b64encode(public_bytes_raw).decode('utf-8').rstrip('=')

print("✅ Chaves geradas!\n")

print(f"📌 Public Key (URL-safe base64 - copie para .env):")
print(f"VAPID_PUBLIC_KEY={public_key_b64}")

print(f"\n🔐 Private Key (PEM format - copie para .env):")
# Escapar newlines para .env
private_escaped = private_pem.strip().replace('\n', '\\n')
print(f"VAPID_PRIVATE_KEY={private_escaped}")

print("\n" + "="*60)
print("INSTRUÇÃO: Copie as linhas acima e substitua no arquivo .env")
print("="*60 + "\n")
