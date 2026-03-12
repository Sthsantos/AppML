"""Mostra membros com senha resetada para teste"""
from app import app, db, Member

print("\n" + "=" * 80)
print("🎯 CREDENCIAIS PRONTAS PARA TESTE - MEMBROS COMUNS (NÃO-ADMIN)")
print("=" * 80)
print("\nTodos os membros abaixo têm a senha: 123456")
print("\n" + "-" * 80)

membros_teste = [
    'sthenio@ministerio.com',
    'patrick@ministerio.com',
    'andremiguel@ministerio.com'
]

with app.app_context():
    for email in membros_teste:
        m = Member.query.filter_by(email=email).first()
        if m:
            print(f"\n📧 Email: {email}")
            print(f"👤 Nome: {m.name}")
            print(f"🎵 Instrumento: {m.instrument}")
            print(f"🔑 Senha: 123456")
            print("-" * 80)

print("\n💡 DICA: Você também pode resetar a senha de QUALQUER membro usando:")
print("   python resetar_senha_membro.py EMAIL_DO_MEMBRO 123456")
print("\n🔧 Exemplo:")
print("   python resetar_senha_membro.py maykonkennedy@ministerio.com 123456")
print("\n" + "=" * 80)
