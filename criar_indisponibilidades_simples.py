"""
Criar 3 indisponibilidades de teste de forma simples e direta.
"""

from app import app, db, Member, Culto, Indisponibilidade
from datetime import datetime, date

with app.app_context():
    print("\n=== CRIANDO INDISPONIBILIDADES DE TESTE ===\n")
    
    # Limpar indisponibilidades antigas (opcional)
    # Indisponibilidade.query.delete()
    # db.session.commit()
    # print("Indisponibilidades anteriores removidas\n")
    
    # Buscar membros e cultos
    membros = Member.query.filter_by(suspended=False).limit(8).all()
    cultos = Culto.query.filter(Culto.date >= date.today()).order_by(Culto.date).limit(10).all()
    
    if not membros or not cultos:
        print("ERRO: Sem membros ou cultos no banco!")
        exit()
    
    print(f"Membros disponíveis: {len(membros)}")
    print(f"Cultos futuros: {len(cultos)}\n")
    
    # Criar 5 indisponibilidades
    dados = [
        (0, 0, "Viagem de trabalho"),
        (1, 1, "Compromisso familiar"),
        (2, 2, "Consulta médica"),
        (3, 3, "Curso/Treinamento"),
        (4, 4, "Férias programadas"),
    ]
    
    criadas = 0
    for idx_membro, idx_culto, motivo in dados:
        if idx_membro >= len(membros) or idx_culto >= len(cultos):
            continue
            
        membro = membros[idx_membro]
        culto = cultos[idx_culto]
        
        # Verificar se já existe
        existe = Indisponibilidade.query.filter_by(
            member_id=membro.id,
            culto_id=culto.id
        ).first()
        
        if existe:
            print(f"⚠️  JÁ EXISTE: {membro.name} - {culto.description}")
            continue
        
        # Criar
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
        
        print(f"✅ {membro.name} ({membro.instrument})")
        print(f"   {culto.description} - {culto.date.strftime('%d/%m/%Y')}")
        print(f"   Motivo: {motivo}\n")
    
    if criadas > 0:
        db.session.commit()
        print(f"\n✅ {criadas} indisponibilidade(s) criada(s) com sucesso!\n")
        print("Acesse:")
        print("  • Dashboard: http://127.0.0.1:5000/dashboard")
        print("  • Escalas: http://127.0.0.1:5000/escalas")
        print("  • Indisponibilidade: http://127.0.0.1:5000/indisponibilidade\n")
    else:
        print("\n⚠️  Todas as indisponibilidades já existem!\n")
