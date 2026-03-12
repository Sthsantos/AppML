from app import app, db, Culto, Member, Escala

with app.app_context():
    # Buscar Santa Ceia (09:00 e 18:00)
    print("\n" + "="*70)
    print("VERIFICAÇÃO: SANTA CEIA (Culto da Família)")
    print("="*70)
    
    cultos_familia = Culto.query.filter(Culto.description.contains('Família')).order_by(Culto.date, Culto.time).first()
    if cultos_familia:
        data = cultos_familia.date
        cultos_dia = Culto.query.filter_by(date=data).order_by(Culto.time).all()
        
        print(f"\nData: {data}")
        for culto in cultos_dia:
            print(f"\n{culto.time} - {culto.description}:")
            escalas = Escala.query.filter_by(culto_id=culto.id).all()
            for e in escalas:
                membro = Member.query.get(e.member_id)
                print(f"  {e.role}: {membro.name}")
    
    # Buscar Domingo (Celebração 09:00 e 18:00)
    print("\n" + "="*70)
    print("VERIFICAÇÃO: DOMINGO (Culto de Celebração)")
    print("="*70)
    
    culto_celebracao = Culto.query.filter(Culto.description.contains('Celebração')).order_by(Culto.date, Culto.time).first()
    if culto_celebracao:
        data = culto_celebracao.date
        cultos_dia = Culto.query.filter_by(date=data).order_by(Culto.time).all()
        
        print(f"\nData: {data}")
        for culto in cultos_dia:
            print(f"\n{culto.time} - {culto.description}:")
            escalas = Escala.query.filter_by(culto_id=culto.id).all()
            for e in escalas:
                membro = Member.query.get(e.member_id)
                print(f"  {e.role}: {membro.name}")
    
    print("\n" + "="*70 + "\n")
