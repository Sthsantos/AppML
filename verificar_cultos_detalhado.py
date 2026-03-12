from app import app, db, Culto
from collections import defaultdict

with app.app_context():
    # Buscar todos os cultos
    cultos = Culto.query.order_by(Culto.date, Culto.time).all()
    
    print(f"\n{'='*80}")
    print(f"TOTAL DE CULTOS: {len(cultos)}")
    print(f"{'='*80}\n")
    
    # Agrupar por data
    por_data = defaultdict(list)
    for culto in cultos:
        por_data[culto.date].append(culto)
    
    # Mostrar primeiras 10 datas
    for i, (data, cultos_dia) in enumerate(sorted(por_data.items())[:10]):
        print(f"\n{data} ({data.strftime('%A')})")
        print("-" * 60)
        for culto in sorted(cultos_dia, key=lambda x: x.time):
            print(f"  {culto.time} - {culto.description} (ID: {culto.id})")
