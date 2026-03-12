"""Script para listar usuários e membros cadastrados no sistema"""
from app import app, db, User, Member

with app.app_context():
    print("=" * 80)
    print("USUÁRIOS CADASTRADOS (Tabela User)")
    print("=" * 80)
    users = User.query.all()
    
    if not users:
        print("❌ Nenhum usuário encontrado na tabela User")
    else:
        for user in users:
            admin_badge = "👑 ADMIN" if user.is_admin else "👤 MEMBRO"
            print(f"\n{admin_badge}")
            print(f"  ID: {user.id}")
            print(f"  Nome: {user.name}")
            print(f"  Email: {user.email}")
            print(f"  É Admin: {user.is_admin}")
    
    print("\n" + "=" * 80)
    print("MEMBROS CADASTRADOS (Tabela Member)")
    print("=" * 80)
    members = Member.query.all()
    
    if not members:
        print("❌ Nenhum membro encontrado na tabela Member")
    else:
        for member in members:
            print(f"\n📝 Membro ID: {member.id}")
            print(f"  Nome: {member.name}")
            print(f"  Email: {member.email}")
            print(f"  Instrumento: {member.instrument}")
            print(f"  Telefone: {member.phone}")
            print(f"  Tem senha: {'Sim' if member.password else 'Não'}")
    
    print("\n" + "=" * 80)
    print("SUGESTÃO PARA CRIAR USUÁRIO MEMBRO (NÃO-ADMIN)")
    print("=" * 80)
    
    # Verificar se existe algum membro que não seja admin
    non_admin_users = User.query.filter_by(is_admin=False).all()
    
    if non_admin_users:
        print("\n✅ Usuários NÃO-ADMIN disponíveis para teste:")
        for user in non_admin_users:
            print(f"\n  📧 Email: {user.email}")
            print(f"  👤 Nome: {user.name}")
            print(f"  ⚠️  Senha: Você precisará resetar a senha ou criar uma nova")
    else:
        print("\n⚠️  Não há usuários não-admin cadastrados!")
        print("\nCrie um usuário de teste com o seguinte script Python:")
        print("""
from app import app, db, User

with app.app_context():
    # Criar usuário membro (não admin)
    teste_user = User(
        name='Membro Teste',
        email='membro@teste.com',
        is_admin=False
    )
    teste_user.set_password('123456')  # Senha: 123456
    db.session.add(teste_user)
    db.session.commit()
    print('✅ Usuário membro criado com sucesso!')
    print('📧 Email: membro@teste.com')
    print('🔑 Senha: 123456')
""")
