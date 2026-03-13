"""Script simples para criar cultos de teste"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db, Culto
from datetime import date, time, timedelta

with app.app_context():
    print("\nCriando cultos de teste...\n")
    
    hoje = date.today()
    count = 0
    
    # Criar 10 cultos (5 passados, 5 futuros)
    for i in range(-5, 6):
        if i == 0:
            continue
            
        data_culto = hoje + timedelta(days=i*7)
        
        culto = Culto(
            date=data_culto,
            time=time(19, 0),
            description=f'Culto de Celebração - Domingo {data_culto.strftime("%d/%m/%Y")}'
        )
        db.session.add(culto)
        count += 1
        print(f"✅ Culto criado: {culto.description}")
    
    db.session.commit()
    
    total = Culto.query.count()
    print(f"\n✅ {count} cultos criados!")
    print(f"📊 Total de cultos no banco: {total}\n")
