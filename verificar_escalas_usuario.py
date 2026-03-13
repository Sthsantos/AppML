"""Script para verificar escalas do usuário logado"""
from app import app, db, Member, User, Escala, Culto
from flask import session

with app.app_context():
    print("\n=== VERIFICANDO USUÁRIOS E ESCALAS ===\n")
    
    # Listar todos os usuários
    usuarios = User.query.all()
    print(f"📋 Total de usuários: {len(usuarios)}")
    for u in usuarios:
        print(f"  - {u.email} (Admin: {u.is_admin})")
    
    print("\n📋 Total de membros:", Member.query.count())
    membros = Member.query.all()
    for m in membros:
        print(f"  - {m.name} ({m.email}) - {m.instrument}")
    
    print("\n📋 Total de escalas:", Escala.query.count())
    
    # Verificar escalas por membro
    print("\n=== ESCALAS POR MEMBRO ===")
    for membro in membros:
        escalas = Escala.query.filter_by(member_id=membro.id).all()
        print(f"\n{membro.name}: {len(escalas)} escalas")
        for e in escalas[:3]:  # Mostrar até 3 escalas
            culto = Culto.query.get(e.culto_id)
            if culto:
                print(f"  - {culto.description} - {e.role}")
    
    # Verificar especificamente para stheni@gmail.com
    print("\n=== VERIFICAÇÃO ESPECÍFICA: stheni@gmail.com ===")
    membro_stheni = Member.query.filter_by(email='stheni@gmail.com').first()
    if membro_stheni:
        print(f"✓ Membro encontrado: {membro_stheni.name} (ID: {membro_stheni.id})")
        escalas_stheni = Escala.query.filter_by(member_id=membro_stheni.id).all()
        print(f"✓ Total de escalas: {len(escalas_stheni)}")
        
        if escalas_stheni:
            print("\nPrimeiras escalas:")
            for e in escalas_stheni[:5]:
                culto = Culto.query.get(e.culto_id)
                print(f"  - Culto #{culto.id}: {culto.description} - {e.role}")
        else:
            print("❌ NENHUMA ESCALA ENCONTRADA!")
            print("\n⚠️ Você precisa CRIAR ESCALAS para este membro!")
    else:
        print("❌ Membro stheni@gmail.com NÃO encontrado!")
