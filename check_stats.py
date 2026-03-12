import sys
sys.path.insert(0, '.')

from app import app, db, Member, Culto, Escala, Repertorio

with app.app_context():
    membros = Member.query.count()
    cultos = Culto.query.count()
    escalas = Escala.query.count()
    musicas = Repertorio.query.count()
    
    print("=" * 50)
    print("ESTATISTICAS DO BANCO DE DADOS")
    print("=" * 50)
    print(f"Membros cadastrados: {membros}")
    print(f"Cultos cadastrados: {cultos}")
    print(f"Escalas criadas: {escalas}")
    print(f"Musicas no repertorio: {musicas}")
    print("=" * 50)

