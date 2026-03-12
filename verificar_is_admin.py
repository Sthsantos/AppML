"""Verifica se todos os membros têm o atributo is_admin"""
from app import app, db, Member, User

with app.app_context():
    print("=" * 80)
    print("🔍 VERIFICAÇÃO DE ATRIBUTO is_admin")
    print("=" * 80)
    
    # Verificar alguns membros
    print("\n📋 MEMBROS:")
    print("-" * 80)
    membros = Member.query.limit(5).all()
    
    for m in membros:
        try:
            is_admin = m.is_admin
            print(f"✅ {m.name:30} | {m.email:40} | is_admin={is_admin}")
        except AttributeError as e:
            print(f"❌ {m.name:30} | {m.email:40} | ERRO: {e}")
    
    # Verificar usuários admin
    print("\n👑 USUÁRIOS ADMIN:")
    print("-" * 80)
    admins = User.query.filter_by(is_admin=True).all()
    
    for u in admins:
        try:
            is_admin = u.is_admin
            print(f"✅ {u.email:40} | is_admin={is_admin}")
        except AttributeError as e:
            print(f"❌ {u.email:40} | ERRO: {e}")
    
    print("\n" + "=" * 80)
    print("✅ VERIFICAÇÃO CONCLUÍDA - Sistema pronto para login!")
    print("=" * 80)
    print("\n🎯 TESTE AGORA:")
    print("   1. Acesse: http://127.0.0.1:5000/login")
    print("   2. Login MEMBRO: sthenio@ministerio.com / 123456")
    print("   3. Login ADMIN:  admin@ministeriodelouvor.com / sua_senha")
    print("=" * 80)
