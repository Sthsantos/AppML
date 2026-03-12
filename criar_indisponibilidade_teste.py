"""
Script para criar indisponibilidades de teste no banco de dados.
Use este script quando estiver fora do período de registro (dias 1-2 do mês).
"""

from app import app, db, Member, Culto, Indisponibilidade
from datetime import datetime, date

def criar_indisponibilidades_teste():
    """Cria algumas indisponibilidades de teste para demonstração."""
    
    with app.app_context():
        # Buscar membros ativos
        membros = Member.query.filter_by(suspended=False).limit(5).all()
        
        # Buscar cultos futuros
        hoje = date.today()
        cultos_futuros = Culto.query.filter(Culto.date >= hoje).order_by(Culto.date.asc()).limit(10).all()
        
        print("\n" + "="*60)
        print("CRIANDO INDISPONIBILIDADES DE TESTE")
        print("="*60)
        
        if not membros:
            print("❌ Nenhum membro encontrado no banco de dados!")
            return
        
        if not cultos_futuros:
            print("❌ Nenhum culto futuro encontrado no banco de dados!")
            return
        
        print(f"\n✅ {len(membros)} membros encontrados")
        print(f"✅ {len(cultos_futuros)} cultos futuros encontrados\n")
        
        # Criar 3 indisponibilidades de teste
        indisponibilidades_criadas = []
        motivos_exemplo = [
            "Viagem de trabalho",
            "Compromisso familiar",
            "Consulta médica agendada",
            "Curso/Treinamento",
            "Outro compromisso importante"
        ]
        
        for i in range(min(3, len(membros), len(cultos_futuros))):
            membro = membros[i]
            culto = cultos_futuros[i]
            motivo = motivos_exemplo[i % len(motivos_exemplo)]
            
            # Verificar se já existe indisponibilidade para este membro neste culto
            existe = Indisponibilidade.query.filter_by(
                member_id=membro.id,
                culto_id=culto.id
            ).first()
            
            if existe:
                print(f"⚠️  {membro.name} já possui indisponibilidade para {culto.description}")
                continue
            
            # Criar indisponibilidade
            ind = Indisponibilidade(
                member_id=membro.id,
                culto_id=culto.id,
                date_start=culto.date,
                date_end=culto.date,
                reason=motivo,
                status='approved',  # Auto-aprovado para teste
                created_at=datetime.now()
            )
            
            db.session.add(ind)
            indisponibilidades_criadas.append({
                'membro': membro.name,
                'instrumento': membro.instrument,
                'culto': culto.description,
                'data': culto.date.strftime('%d/%m/%Y'),
                'hora': culto.time.strftime('%H:%M'),
                'motivo': motivo
            })
            
            print(f"✅ Criada indisponibilidade:")
            print(f"   • Membro: {membro.name} ({membro.instrument})")
            print(f"   • Culto: {culto.description}")
            print(f"   • Data: {culto.date.strftime('%d/%m/%Y')} às {culto.time.strftime('%H:%M')}")
            print(f"   • Motivo: {motivo}\n")
        
        try:
            db.session.commit()
            print("="*60)
            print(f"✅ SUCESSO! {len(indisponibilidades_criadas)} indisponibilidade(s) criada(s)!")
            print("="*60)
            
            print("\n📊 TESTES DISPONÍVEIS:")
            print("1. Acesse /dashboard para ver as indisponibilidades")
            print("2. Acesse /escalas e tente criar escala com membros indisponíveis")
            print("3. Acesse /indisponibilidade para ver no perfil do membro")
            print("\n")
            
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ ERRO ao salvar no banco de dados: {str(e)}\n")

if __name__ == "__main__":
    criar_indisponibilidades_teste()
