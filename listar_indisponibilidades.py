"""
Listar todas as indisponibilidades existentes para teste.
"""

from app import app, db, Member, Culto, Indisponibilidade
from datetime import date

with app.app_context():
    print("\n" + "="*70)
    print("INDISPONIBILIDADES CADASTRADAS NO SISTEMA")
    print("="*70 + "\n")
    
    # Buscar apenas indisponibilidades de cultos futuros
    hoje = date.today()
    
    indisponibilidades = db.session.query(
        Indisponibilidade, Member, Culto
    ).join(
        Member, Indisponibilidade.member_id == Member.id
    ).join(
        Culto, Indisponibilidade.culto_id == Culto.id
    ).filter(
        Culto.date >= hoje
    ).order_by(
        Culto.date.asc()
    ).all()
    
    if not indisponibilidades:
        print("❌ Nenhuma indisponibilidade de cultos futuros encontrada!\n")
    else:
        print(f"✅ {len(indisponibilidades)} indisponibilidade(s) encontrada(s):\n")
        
        for ind, membro, culto in indisponibilidades:
            print(f"🔴 {membro.name} ({membro.instrument})")
            print(f"   📅 Culto: {culto.description}")
            print(f"   📆 Data: {culto.date.strftime('%d/%m/%Y')} às {culto.time.strftime('%H:%M')}")
            print(f"   💬 Motivo: {ind.reason}")
            print(f"   ✅ Status: {ind.status}")
            print()
        
        print("="*70)
        print("\n📊 AGORA VOCÊ PODE TESTAR:")
        print()
        print("1️⃣  DASHBOARD - Ver indisponibilidades:")
        print("   http://127.0.0.1:5000/dashboard")
        print("   → Role até 'Indisponibilidades Próximas'")
        print()
        print("2️⃣  ESCALAS - Testar bloqueio de membros indisponíveis:")
        print("   http://127.0.0.1:5000/escalas")
        print("   → Tente criar escala para um dos cultos listados acima")
        print("   → Selecione o culto e instrumento do membro indisponível")
        print("   → Veja que ele aparece como 'INDISPONÍVEL' e não pode ser selecionado")
        print()
        print("3️⃣  INDISPONIBILIDADE - Ver como membro:")
        print("   http://127.0.0.1:5000/indisponibilidade")
        print("   → Faça login como um dos membros listados")
        print("   → Veja suas indisponibilidades cadastradas")
        print()
        print("="*70 + "\n")
