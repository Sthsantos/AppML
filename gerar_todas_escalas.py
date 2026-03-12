from app import app, db, Culto, Member, Escala
from collections import defaultdict

with app.app_context():
    # LIMPAR TODAS AS ESCALAS
    print("\n🗑️  Limpando escalas existentes...")
    Escala.query.delete()
    db.session.commit()
    print("✅ Escalas removidas\n")
    
    # BUSCAR TODOS OS CULTOS
    cultos = Culto.query.order_by(Culto.date, Culto.time).all()
    
    print("="*80)
    print(f"📅 PROCESSANDO {len(cultos)} CULTOS")
    print("="*80)
    
    # BUSCAR MEMBROS NÃO SUSPENSOS
    membros = Member.query.filter_by(suspended=False).all()
    membros_por_instr = defaultdict(list)
    for m in membros:
        membros_por_instr[m.instrument].append(m)
    
    instrumentos = ['Guitarrista', 'Violonista', 'Baterista', 'Tecladista', 'Baixista']
    
    # AGRUPAR POR DATA
    por_data = defaultdict(list)
    for c in cultos:
        por_data[c.date].append(c)
    
    # CONTADOR DE ROTAÇÃO
    indices = {i: 0 for i in instrumentos}
    
    total_escalas = 0
    datas_processadas = 0
    
    for data in sorted(por_data.keys()):
        cultos_dia = sorted(por_data[data], key=lambda x: x.time)
        descricoes = [c.description for c in cultos_dia]
        datas_processadas += 1
        
        # Verificar se é especial (Celebração ou Família/Santa Ceia)
        eh_especial = False
        if len(cultos_dia) > 1:
            if any('Celebração' in d or 'Família' in d or 'Santa Ceia' in d for d in descricoes):
                eh_especial = True
        
        if eh_especial:
            # MESMA EQUIPE PARA TODOS
            equipe = {}
            for instr in instrumentos:
                idx = indices[instr]
                equipe[instr] = membros_por_instr[instr][idx]
                indices[instr] = (idx + 1) % len(membros_por_instr[instr])
            
            # Aplicar para todos os cultos do dia
            for culto in cultos_dia:
                for instr, membro in equipe.items():
                    escala = Escala(
                        member_id=membro.id,
                        culto_id=culto.id,
                        role=instr
                    )
                    db.session.add(escala)
                    total_escalas += 1
        else:
            # EQUIPES DIFERENTES
            for culto in cultos_dia:
                for instr in instrumentos:
                    idx = indices[instr]
                    membro = membros_por_instr[instr][idx]
                    
                    escala = Escala(
                        member_id=membro.id,
                        culto_id=culto.id,
                        role=instr
                    )
                    db.session.add(escala)
                    total_escalas += 1
                    
                    indices[instr] = (idx + 1) % len(membros_por_instr[instr])
        
        # Commit a cada 10 datas
        if datas_processadas % 10 == 0:
            db.session.commit()
            print(f"   ✓ {datas_processadas} datas processadas...")
    
    db.session.commit()
    
    print("\n" + "="*80)
    print(f"✅ SUCESSO!")
    print(f"   📊 Datas processadas: {datas_processadas}")
    print(f"   📝 Escalas criadas: {total_escalas}")
    print(f"   👥 Média por culto: {total_escalas / len(cultos):.1f}")
    print("="*80 + "\n")
