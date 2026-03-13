from app import app, db
import json

app.app_context().push()

# Simular requisição com usuário logado
with app.test_client() as client:
    # Fazer login
    client.post('/login', data={'email': 'stheni@gmail.com', 'password': '123456'})
    
    # Buscar escalas
    response = client.get('/get_minhas_escalas')
    data = response.json
    
    print(f"\nStatus: {response.status_code}")
    print(f"Total de escalas: {len(data.get('escalas', []))}\n")
    
    # Mostrar cada escala
    for i, escala in enumerate(data.get('escalas', []), 1):
        print(f"{i}. Culto: {escala['culto_name']}")
        print(f"   Member: {escala['member_name']}")
        print(f"   Role: {escala['role']}")
        print(f"   Is Me: {escala.get('is_me', False)}")
        print()
