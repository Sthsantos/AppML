"""
Script para verificar indisponibilidades existentes e criar novas de teste.
"""

from app import app, db, Member, Culto, Indisponibilidade
from datetime import datetime, date

def verificar_e_criar_indisponibilidades():
    """Verifica indisponibilidades existentes e cria novas se necessário."""
    
    with app.app_context():
        # Verificar indisponibilidades existentes
        print("\n" + "="*60)
        print("INDISPONIBILIDADES EXISTENTES NO BANCO")
        print("="*60 + "\n")
        
        indisponibilidades = Indisponibilidade.query.all()
        
        if indisponibilidades:
            print(f"✅ {len(indisponibilidades)} indisponibilidade(s) encontrada(s):\n")
            for ind in indisponibilidades:
                membro = Member.query.get(ind.member_id)
                culto = Culto.query.get(ind.culto_id) if ind.culto_id else None
                
                print(f"• {membro.name if membro else 'Membro desconhecido'} ({membro.instrument if membro else ''})")
                if culto:
                    print(f"  Culto: {culto.description} - {culto.date.strftime('%d/%m/%Y')} às {culto.time.strftime('%H:%M')}")
                print(f"  Motivo: {ind.reason}")
                print(f"  Status: {ind.status}")
                print()
        else:
            print("❌ Nenhuma indisponibilidade cadastrada ainda!\n")
        
        # Buscar membros que NÃO têm indisponibilidades
        print("="*60)
        print("CRIANDO NOVAS INDISPONIBILIDADES")
        print("="*60 + "\n")
        
        todos_membros = Member.query.filter_by(suspended=False).all()
        membros_com_ind = [ind.member_id for ind in indisponibilidades]
        membros_sem_ind = [m for m in todos_membros if m.id not in membros_com_ind]
        
        # Buscar cultos futuros
        hoje = date.today()
        cultos_futuros = Culto.query.filter(Culto.date >= hoje).order_by(Culto.date.asc()).limit(15).all()
        
        if not cultos_futuros:
            print("❌ Nenhum culto futuro encontrado!")
            return
        
        print(f"✅ {len(membros_sem_ind)} membros sem indisponibilidades")
        print(f"✅ {len(cultos_futuros)} cultos futuros disponíveis\n")
        
        # Criar indisponibilidades para 5 membros diferentes
        motivos = [
            "Viagem de trabalho programada",
            "Compromisso familiar importante",
            "Consulta médica agendada",
            "Participação em evento/curso",
            "Férias programadas",
            "Outro compromisso inadiável"
        ]
        
        criadas = 0
        for i, membro in enumerate(membros_sem_ind[:5]):
            if i < len(cultos_futuros):
                culto = cultos_futuros[i]
                motivo = motivos[i % len(motivos)]
                
                ind = Indisponibilidade(
                    member_id=membro.id,
                    culto_id=culto.id,
                    date_start=culto.date,
                    date_end=culto.date,
                    reason=motivo,
                    status='approved',
                    created_at=datetime.now()
                )
                
                db.session.add(ind)
                criadas += 1
                
                print(f"✅ Criada:")
                print(f"   • {membro.name} ({membro.instrument})")
                print(f"   • {culto.description} - {culto.date.strftime('%d/%m/%Y')} às {culto.time.strftime('%H:%M')}")
                print(f"   • Motivo: {motivo}\n")
        
        if criadas > 0:
            try:
                db.session.commit()
                print("="*60)
                print(f"✅ SUCESSO! {criadas} nova(s) indisponibilidade(s) criada(s)!")
                print("="*60)
                print("\n📊 Agora você pode testar:")
                print("1. Dashboard: http://127.0.0.1:5000/dashboard")
                print("2. Escalas: http://127.0.0.1:5000/escalas")
                print("3. Indisponibilidades: http://127.0.0.1:5000/indisponibilidade\n")
            except Exception as e:
                db.session.rollback()
                print(f"\n❌ ERRO: {str(e)}\n")
        else:
            print("⚠️  Todos os membros disponíveis já possuem indisponibilidades!\n")

if __name__ == "__main__":
    verificar_e_criar_indisponibilidades()
