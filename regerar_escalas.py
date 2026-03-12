from app import app, db, Culto, Member, Escala
from collections import defaultdict
from datetime import datetime

def regerar_escalas_inteligente():
    """Gera escalas respeitando mesma equipe para cultos do mesmo dia."""
    
    with app.app_context():
        # Limpar escalas existentes
        print("\n🗑️  Limpando escalas existentes...")
        Escala.query.delete()
        db.session.commit()
        print("✅ Escalas antigas removidas")
        
        # Buscar membros ativos por instrumento (não suspensos)
        print("\n📋 Carregando membros...")
        membros_ativos = Member.query.filter_by(suspended=False).all()
        
        membros_por_instrumento = defaultdict(list)
        for membro in membros_ativos:
            membros_por_instrumento[membro.instrument].append(membro)
        
        instrumentos_necessarios = ['Guitarrista', 'Violonista', 'Baterista', 'Tecladista', 'Baixista']
        
        # Verificar se temos todos os instrumentos
        for instrumento in instrumentos_necessarios:
            if not membros_por_instrumento[instrumento]:
                print(f"❌ Faltam membros para: {instrumento}")
                return
            print(f"   {instrumento}: {len(membros_por_instrumento[instrumento])} membros")
        
        # Buscar todos os cultos
        cultos = Culto.query.order_by(Culto.date, Culto.time).all()
        print(f"\n📅 Total de cultos: {len(cultos)}")
        
        # Agrupar cultos por data
        print("\n🔍 Agrupando cultos por data...")
        cultos_por_data = defaultdict(list)
        for culto in cultos:
            cultos_por_data[culto.date].append(culto)
        
        # Contador de rotação por instrumento
        indices = {instrumento: 0 for instrumento in instrumentos_necessarios}
        
        # Processar cada data
        datas_processadas = 0
        escalas_criadas = 0
        
        for data in sorted(cultos_por_data.keys()):
            cultos_do_dia = sorted(cultos_por_data[data], key=lambda x: x.time)
            datas_processadas += 1
            
            # Verificar se é domingo (Celebração) ou Santa Ceia (Família)
            descricoes = [c.description for c in cultos_do_dia]
            eh_domingo = any('Celebração' in d for d in descricoes)
            eh_santa_ceia = any('Família' in d for d in descricoes)
            
            if eh_domingo or eh_santa_ceia:
                # Mesma equipe para todos os cultos do dia
                equipe_do_dia = {}
                for instrumento in instrumentos_necessarios:
                    membros = membros_por_instrumento[instrumento]
                    indice = indices[instrumento]
                    equipe_do_dia[instrumento] = membros[indice]
                    # Avançar para próximo membro
                    indices[instrumento] = (indice + 1) % len(membros)
                
                # Aplicar mesma equipe para todos os cultos do dia
                for culto in cultos_do_dia:
                    for instrumento, membro in equipe_do_dia.items():
                        nova_escala = Escala(
                            member_id=membro.id,
                            culto_id=culto.id,
                            role=instrumento
                        )
                        db.session.add(nova_escala)
                        escalas_criadas += 1
                
                tipo = "Santa Ceia" if eh_santa_ceia else "Domingo"
                print(f"   ✓ {data} ({tipo}): {len(cultos_do_dia)} cultos, mesma equipe")
            else:
                # Equipe diferente para cada culto
                for culto in cultos_do_dia:
                    for instrumento in instrumentos_necessarios:
                        membros = membros_por_instrumento[instrumento]
                        indice = indices[instrumento]
                        membro = membros[indice]
                        
                        nova_escala = Escala(
                            member_id=membro.id,
                            culto_id=culto.id,
                            role=instrumento
                        )
                        db.session.add(nova_escala)
                        escalas_criadas += 1
                        
                        # Avançar para próximo membro
                        indices[instrumento] = (indice + 1) % len(membros)
                
                print(f"   ✓ {data}: {len(cultos_do_dia)} cultos individuais")
            
            # Commit a cada 10 datas
            if datas_processadas % 10 == 0:
                db.session.commit()
                print(f"\n💾 Salvando... ({datas_processadas} datas processadas)")
        
        # Commit final
        db.session.commit()
        
        print(f"\n{'='*70}")
        print(f"✅ ESCALAS GERADAS COM SUCESSO!")
        print(f"{'='*70}")
        print(f"   📊 Datas processadas: {datas_processadas}")
        print(f"   📝 Escalas criadas: {escalas_criadas}")
        print(f"   👥 Média de músicos por data: {escalas_criadas / datas_processadas:.1f}")
        print(f"{'='*70}\n")
        
        # Mostrar distribuição
        print("\n📈 DISTRIBUIÇÃO POR MEMBRO:")
        print("-" * 70)
        for instrumento in instrumentos_necessarios:
            print(f"\n{instrumento}:")
            for membro in membros_por_instrumento[instrumento]:
                count = Escala.query.filter_by(member_id=membro.id).count()
                print(f"   {membro.name}: {count} escalas")

if __name__ == '__main__':
    print("\n" + "="*70)
    print("REGERAR ESCALAS INTELIGENTE")
    print("="*70)
    print("\nRegras:")
    print("- Domingos (Celebração): MESMA equipe para 09:00 e 18:00")
    print("- Santa Ceia (Família): MESMA equipe para 09:00 e 18:00")
    print("- Outros cultos: equipes diferentes com rotação")
    print("\n" + "="*70)
    
    regerar_escalas_inteligente()
