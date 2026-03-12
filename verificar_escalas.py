"""Script para verificar as escalas geradas."""
from app import app, db, Escala, Culto, Member
from datetime import datetime

with app.app_context():
    # Total de escalas
    total_escalas = Escala.query.count()
    total_cultos = Culto.query.count()
    
    print("=" * 70)
    print("VERIFICAÇÃO DE ESCALAS GERADAS")
    print("=" * 70)
    print(f"\nTotal de cultos: {total_cultos}")
    print(f"Total de escalas: {total_escalas}")
    print(f"Média de músicos por culto: {total_escalas / total_cultos if total_cultos > 0 else 0:.1f}")
    
    # Mostrar alguns exemplos
    print("\n" + "=" * 70)
    print("EXEMPLOS DE ESCALAS (Primeiros 5 cultos)")
    print("=" * 70)
    
    cultos = Culto.query.order_by(Culto.date, Culto.time).limit(5).all()
    
    for culto in cultos:
        print(f"\n📅 {culto.description}")
        print(f"   Data: {culto.date.strftime('%d/%m/%Y')} às {culto.time.strftime('%H:%M')}")
        print(f"   Escalados:")
        
        escalas = Escala.query.filter_by(culto_id=culto.id).all()
        for escala in escalas:
            membro = Member.query.get(escala.member_id)
            print(f"      • {escala.role}: {membro.name}")
    
    # Distribuição por membro
    print("\n" + "=" * 70)
    print("DISTRIBUIÇÃO DE ESCALAS POR MEMBRO")
    print("=" * 70)
    
    membros = Member.query.filter_by(suspended=False).order_by(Member.instrument, Member.name).all()
    
    current_instrument = None
    for membro in membros:
        if current_instrument != membro.instrument:
            current_instrument = membro.instrument
            print(f"\n{current_instrument}:")
        
        total_membro = Escala.query.filter_by(member_id=membro.id).count()
        print(f"  {membro.name}: {total_membro} culto(s)")
