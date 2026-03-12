"""Script para verificar membros e instrumentos cadastrados."""
from app import app, db, Member, Culto

with app.app_context():
    members = Member.query.filter_by(suspended=False).all()
    
    print("=" * 60)
    print("MEMBROS CADASTRADOS POR INSTRUMENTO")
    print("=" * 60)
    
    instruments = {}
    for m in members:
        if m.instrument not in instruments:
            instruments[m.instrument] = []
        instruments[m.instrument].append(m.name)
    
    for inst, names in instruments.items():
        print(f"\n{inst}: {len(names)} membro(s)")
        for name in names:
            print(f"  - {name}")
    
    print("\n" + "=" * 60)
    print(f"Total de membros ativos: {len(members)}")
    print("=" * 60)
    
    # Verificar cultos
    cultos = Culto.query.order_by(Culto.date, Culto.time).all()
    print(f"\nTotal de cultos cadastrados: {len(cultos)}")
    if cultos:
        print(f"Primeiro culto: {cultos[0].date} às {cultos[0].time} - {cultos[0].description}")
        print(f"Último culto: {cultos[-1].date} às {cultos[-1].time} - {cultos[-1].description}")
