from app import app, db, Culto, Member, Escala
from collections import defaultdict

with app.app_context():
    # LIMPAR TODAS AS ESCALAS
    print("\n🗑️  Limpando escalas existentes...")
    Escala.query.delete()
    db.session.commit()
    print("✅ Escalas removidas\n")
    
    # BUSCAR OS 5 PRIMEIROS CULTOS
    cultos = Culto.query.order_by(Culto.date, Culto.time).limit(10).all()
    
    print("="*80)
    print("CULTOS CADASTRADOS (primeiros 10):")
    print("="*80)
    for i, c in enumerate(cultos, 1):
        print(f"{i}. ID {c.id}: {c.date} {c.time} - {c.description}")
    print("="*80)
    
    # BUSCAR MEMBROS NÃO SUSPENSOS
    membros = Member.query.filter_by(suspended=False).all()
    membros_por_instr = defaultdict(list)
    for m in membros:
        membros_por_instr[m.instrument].append(m)
    
    instrumentos = ['Guitarrista', 'Violonista', 'Baterista', 'Tecladista', 'Baixista']
    
    print("\n📋 MEMBROS DISPONÍVEIS:")
    for instr in instrumentos:
        nomes = [m.name for m in membros_por_instr[instr]]
        print(f"   {instr}: {', '.join(nomes)}")
    
    # PROCESSAR APENAS OS 5 PRIMEIROS CULTOS
    print("\n" + "="*80)
    qtd = 5
    print(f"⚙️  Processando os primeiros {qtd} cultos...")
    cultos_selecionados = cultos[:qtd]
    
    # AGRUPAR POR DATA
    por_data = defaultdict(list)
    for c in cultos_selecionados:
        por_data[c.date].append(c)
    
    # CONTADOR DE ROTAÇÃO
    indices = {i: 0 for i in instrumentos}
    
    print("\n" + "="*80)
    print("GERANDO ESCALAS...")
    print("="*80)
    
    total_escalas = 0
    
    for data in sorted(por_data.keys()):
        cultos_dia = sorted(por_data[data], key=lambda x: x.time)
        descricoes = [c.description for c in cultos_dia]
        
        print(f"\n📅 {data} ({data.strftime('%A')})")
        print(f"   Cultos: {', '.join([f'{c.time} {c.description}' for c in cultos_dia])}")
        
        # Verificar se é especial (Celebração ou Família)
        eh_especial = False
        if len(cultos_dia) > 1:
            # Domingo tem "Celebração", Santa Ceia tem "Família"
            if any('Celebração' in d or 'Família' in d for d in descricoes):
                eh_especial = True
        
        if eh_especial:
            print(f"   ➡️  MESMA EQUIPE para todos os horários")
            # MESMA EQUIPE PARA TODOS
            equipe = {}
            for instr in instrumentos:
                idx = indices[instr]
                equipe[instr] = membros_por_instr[instr][idx]
                indices[instr] = (idx + 1) % len(membros_por_instr[instr])
            
            # Mostrar equipe
            print("   👥 Equipe:")
            for instr, membro in equipe.items():
                print(f"      {instr}: {membro.name}")
            
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
            print(f"   ➡️  EQUIPES DIFERENTES para cada culto")
            # EQUIPES DIFERENTES
            for culto in cultos_dia:
                print(f"   👥 Equipe para {culto.time}:")
                for instr in instrumentos:
                    idx = indices[instr]
                    membro = membros_por_instr[instr][idx]
                    print(f"      {instr}: {membro.name}")
                    
                    escala = Escala(
                        member_id=membro.id,
                        culto_id=culto.id,
                        role=instr
                    )
                    db.session.add(escala)
                    total_escalas += 1
                    
                    indices[instr] = (idx + 1) % len(membros_por_instr[instr])
    
    db.session.commit()
    
    print("\n" + "="*80)
    print(f"✅ SUCESSO! {total_escalas} escalas criadas para {qtd} cultos")
    print("="*80)
    
    # VERIFICAR ESCALAS CRIADAS
    print("\n📊 VERIFICAÇÃO DAS ESCALAS CRIADAS:")
    print("="*80)
    
    for culto in cultos_selecionados:
        escalas = Escala.query.filter_by(culto_id=culto.id).all()
        print(f"\n{culto.date} {culto.time} - {culto.description}")
        for e in escalas:
            membro = Member.query.get(e.member_id)
            print(f"  {e.role}: {membro.name}")
