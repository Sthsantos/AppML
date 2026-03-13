from app import app, db, Member, User
from werkzeug.security import generate_password_hash

with app.app_context():
    print("\n🔄 Criando usuários para os membros...")
    
    membros = Member.query.all()
    criados = 0
    
    for membro in membros:
        # Verificar se já existe usuário com esse email
        existing = User.query.filter_by(email=membro.email).first()
        
        if not existing:
            # Criar novo usuário
            novo_user = User(
                email=membro.email,
                password_hash=generate_password_hash('123456'),
                is_admin=False
            )
            db.session.add(novo_user)
            print(f"✅ Criando usuário para: {membro.name} ({membro.email})")
            criados += 1
        else:
            print(f"ℹ️  Usuário já existe: {membro.email}")
    
    if criados > 0:
        db.session.commit()
        print(f"\n✅ {criados} usuário(s) criado(s) com sucesso!")
        print("🔑 Senha padrão para todos: 123456")
    else:
        print("\nℹ️  Todos os membros já têm contas de usuário.")
    
    # Listar todos os usuários
    print("\n📋 USUÁRIOS CADASTRADOS:")
    users = User.query.all()
    for u in users:
        print(f"  - {u.email} (Admin: {u.is_admin})")
