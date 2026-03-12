"""Script para gerar escalas automáticas para todos os cultos."""
from app import app, db, Member, Culto, Escala
from datetime import datetime
from collections import defaultdict

def gerar_escalas_automaticas():
    """Gera escalas distribuindo membros de forma equilibrada pelos cultos."""
    
    with app.app_context():
        # Limpar escalas existentes (opcional - comentar se quiser manter)
        print("🗑️  Limpando escalas existentes...")
        Escala.query.delete()
        db.session.commit()
        
        # Buscar todos os membros ativos por instrumento
        print("\n📋 Carregando membros...")
        membros_por_instrumento = defaultdict(list)
        
        membros = Member.query.filter_by(suspended=False).order_by(Member.name).all()
        for membro in membros:
            membros_por_instrumento[membro.instrument].append(membro)
        
        # Validar que temos membros de todos os instrumentos necessários
        instrumentos_necessarios = ['Guitarrista', 'Violonista', 'Baterista', 'Tecladista', 'Baixista']
        for instrumento in instrumentos_necessarios:
            if not membros_por_instrumento.get(instrumento):
                print(f"⚠️  Aviso: Nenhum {instrumento} cadastrado!")
                return
        
        print("\nMembros por instrumento:")
        for instrumento in instrumentos_necessarios:
            membros = membros_por_instrumento[instrumento]
            print(f"  {instrumento}: {len(membros)} membro(s)")
        
        # Buscar todos os cultos ordenados por data e hora
        cultos = Culto.query.order_by(Culto.date, Culto.time).all()
        print(f"\n🎵 Total de cultos: {len(cultos)}")
        
        # Contadores para rotação (índice do próximo membro a ser escalado)
        indices = {instrumento: 0 for instrumento in instrumentos_necessarios}
        
        # Estatísticas
        escalas_criadas = 0
        cultos_processados = 0
        
        print("\n🔄 Gerando escalas...\n")
        
        for culto in cultos:
            cultos_processados += 1
            data_culto = f"{culto.date.strftime('%d/%m/%Y')} às {culto.time.strftime('%H:%M')}"
            
            # Para cada instrumento, selecionar o próximo membro da lista (rotação)
            for instrumento in instrumentos_necessarios:
                membros_instrumento = membros_por_instrumento[instrumento]
                
                if not membros_instrumento:
                    continue
                
                # Pegar o próximo membro da rotação
                indice_atual = indices[instrumento]
                membro_selecionado = membros_instrumento[indice_atual]
                
                # Criar a escala
                nova_escala = Escala(
                    member_id=membro_selecionado.id,
                    culto_id=culto.id,
                    role=instrumento
                )
                db.session.add(nova_escala)
                escalas_criadas += 1
                
                # Avançar para o próximo membro (rotação circular)
                indices[instrumento] = (indice_atual + 1) % len(membros_instrumento)
            
            # Mostrar progresso a cada 10 cultos
            if cultos_processados % 10 == 0:
                print(f"  ✓ Processados {cultos_processados}/{len(cultos)} cultos...")
        
        # Salvar no banco de dados
        print("\n💾 Salvando escalas no banco de dados...")
        db.session.commit()
        
        print("\n" + "="*60)
        print("✅ ESCALAS GERADAS COM SUCESSO!")
        print("="*60)
        print(f"Total de cultos processados: {cultos_processados}")
        print(f"Total de escalas criadas: {escalas_criadas}")
        print(f"Média de músicos por culto: {escalas_criadas / cultos_processados:.1f}")
        print("="*60)
        
        # Mostrar estatísticas de distribuição
        print("\n📊 Estatísticas de distribuição:")
        for instrumento in instrumentos_necessarios:
            membros = membros_por_instrumento[instrumento]
            escalas_por_membro = len(cultos) // len(membros) if membros else 0
            print(f"\n{instrumento}:")
            for membro in membros:
                total_escalas = Escala.query.filter_by(
                    member_id=membro.id,
                    role=instrumento
                ).count()
                print(f"  {membro.name}: {total_escalas} culto(s)")

if __name__ == "__main__":
    print("\n" + "="*60)
    print("GERADOR AUTOMÁTICO DE ESCALAS - MINISTÉRIO DE LOUVOR")
    print("="*60)
    
    resposta = input("\n⚠️  Isso irá LIMPAR todas as escalas existentes e gerar novas.\n   Deseja continuar? (s/n): ")
    
    if resposta.lower() == 's':
        gerar_escalas_automaticas()
    else:
        print("\n❌ Operação cancelada.")
