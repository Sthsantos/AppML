import sys
from app import app, db, Culto, Member, Escala
from collections import defaultdict

with app.app_context():
    # Limpar escalas existentes
    print("Limpando escalas...")
    Escala.query.delete()
    db.session.commit()
    
    # Buscar membros não suspensos
    membros = Member.query.filter_by(suspended=False).all()
    
    membros_por_instrumento = defaultdict(list)
    for m in membros:
        membros_por_instrumento[m.instrument].append(m)
    
    instrumentos = ['Guitarrista', 'Violonista', 'Baterista', 'Tecladista', 'Baixista']
    
    print(f"Membros por instrumento:")
    for i in instrumentos:
        print(f"  {i}: {len(membros_por_instrumento[i])}")
    
    # Buscar cultos
    cultos = Culto.query.order_by(Culto.date, Culto.time).all()
    print(f"Total cultos: {len(cultos)}")
    
    # Agrupar por data
    por_data = defaultdict(list)
    for c in cultos:
        por_data[c.date].append(c)
    
    # Contador rotação
    indices = {i: 0 for i in instrumentos}
    
    total_escalas = 0
    for data in sorted(por_data.keys()):
        cultos_dia = sorted(por_data[data], key=lambda x: x.time)
        descricoes = [c.description for c in cultos_dia]
        
        # Verificar se é Domingo ou Santa Ceia
        eh_especial = any('Celebração' in d or 'Família' in d for d in descricoes)
        
        if eh_especial and len(cultos_dia) > 1:
            # Mesma equipe para todos
            equipe = {}
            for instr in instrumentos:
                idx = indices[instr]
                equipe[instr] = membros_por_instrumento[instr][idx]
                indices[instr] = (idx + 1) % len(membros_por_instrumento[instr])
            
            for culto in cultos_dia:
                for instr, membro in equipe.items():
                    e = Escala(member_id=membro.id, culto_id=culto.id, role=instr)
                    db.session.add(e)
                    total_escalas += 1
        else:
            # Equipes diferentes
            for culto in cultos_dia:
                for instr in instrumentos:
                    idx = indices[instr]
                    membro = membros_por_instrumento[instr][idx]
                    e = Escala(member_id=membro.id, culto_id=culto.id, role=instr)
                    db.session.add(e)
                    total_escalas += 1
                    indices[instr] = (idx + 1) % len(membros_por_instrumento[instr])
    
    db.session.commit()
    print(f"\nSUCESSO! {total_escalas} escalas criadas")
