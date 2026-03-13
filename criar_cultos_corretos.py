"""
Script para popular cultos com horários corretos
Terças: 19:00
Quintas: 09:00, 17:30, 19:30
Domingos: 09:00, 18:00
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db, Culto
from datetime import date, time, timedelta

with app.app_context():
    print("\n=== LIMPANDO CULTOS ANTIGOS ===\n")
    Culto.query.delete()
    db.session.commit()
    print("Todos os cultos removidos.\n")
    
    print("=== CRIANDO CULTOS COM HORÁRIOS CORRETOS ===\n")
    
    hoje = date.today()
    count = 0
    
    # Criar cultos para as próximas 12 semanas
    for semana in range(-4, 8):  # 4 semanas passadas, 8 futuras
        base_date = hoje + timedelta(weeks=semana)
        
        # Encontrar a terça dessa semana (weekday 1 = terça)
        dias_ate_terca = (1 - base_date.weekday()) % 7
        if dias_ate_terca == 0 and base_date.weekday() != 1:
            dias_ate_terca = 7
        terca = base_date + timedelta(days=dias_ate_terca)
        
        # Encontrar a quinta dessa semana (weekday 3 = quinta)
        dias_ate_quinta = (3 - base_date.weekday()) % 7
        if dias_ate_quinta == 0 and base_date.weekday() != 3:
            dias_ate_quinta = 7
        quinta = base_date + timedelta(days=dias_ate_quinta)
        
        # Encontrar o domingo dessa semana (weekday 6 = domingo)
        dias_ate_domingo = (6 - base_date.weekday()) % 7
        if dias_ate_domingo == 0 and base_date.weekday() != 6:
            dias_ate_domingo = 7
        domingo = base_date + timedelta(days=dias_ate_domingo)
        
        # TERÇA - 19:00 (Escola Bíblica)
        culto_terca = Culto(
            date=terca,
            time=time(19, 0),
            description=f'Escola Bíblica - {terca.strftime("%d/%m/%Y")}'
        )
        db.session.add(culto_terca)
        count += 1
        print(f"✅ Terça: {terca.strftime('%d/%m/%Y')} às 19:00")
        
        # QUINTA - 3 horários (09:00, 17:30, 19:30)
        horarios_quinta = [
            (time(9, 0), "Manhã"),
            (time(17, 30), "Tarde"),
            (time(19, 30), "Noite")
        ]
        for horario, periodo in horarios_quinta:
            culto_quinta = Culto(
                date=quinta,
                time=horario,
                description=f'Cura e Libertação - {periodo} - {quinta.strftime("%d/%m/%Y")}'
            )
            db.session.add(culto_quinta)
            count += 1
        print(f"✅ Quinta: {quinta.strftime('%d/%m/%Y')} às 09:00, 17:30, 19:30")
        
        # DOMINGO - 2 horários (09:00, 18:00)
        # Verifica se é o primeiro domingo do mês
        is_primeiro_domingo = domingo.day <= 7
        nome_culto = "Santa Ceia" if is_primeiro_domingo else "Culto de Celebração"
        
        horarios_domingo = [
            (time(9, 0), "Manhã"),
            (time(18, 0), "Noite")
        ]
        for horario, periodo in horarios_domingo:
            culto_domingo = Culto(
                date=domingo,
                time=horario,
                description=f'{nome_culto} - {periodo} - {domingo.strftime("%d/%m/%Y")}'
            )
            db.session.add(culto_domingo)
            count += 1
        
        if is_primeiro_domingo:
            print(f"🍷 SANTA CEIA: {domingo.strftime('%d/%m/%Y')} às 09:00, 18:00")
        else:
            print(f"✅ Domingo: {domingo.strftime('%d/%m/%Y')} às 09:00, 18:00")
        print()
    
    db.session.commit()
    
    total = Culto.query.count()
    print(f"\n{'='*60}")
    print(f"✅ CULTOS CRIADOS COM SUCESSO!")
    print(f"{'='*60}")
    print(f"📊 Total de cultos cadastrados: {total}")
    print(f"📅 Período: {(-4)} a {(+8)} semanas")
    print(f"\n📋 Distribuição:")
    print(f"   • Terças (19:00): 1 culto por semana")
    print(f"   • Quintas (09:00, 17:30, 19:30): 3 cultos por semana")
    print(f"   • Domingos (09:00, 18:00): 2 cultos por semana")
    print(f"   • Total por semana: 6 cultos")
    print(f"{'='*60}\n")
