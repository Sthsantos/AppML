"""
Script para popular o banco de dados com dados de teste
"""
import sys
import os

# Adiciona o diretório do app ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db, Member, Culto, Repertorio
from datetime import datetime, time, date, timedelta
from werkzeug.security import generate_password_hash

def popular_banco():
    with app.app_context():
        print("\n=== POPULANDO BANCO DE DADOS ===\n")
        
        # 1. CRIAR MEMBROS DE TESTE
        print("📝 Criando membros...")
        membros_data = [
            {
                'name': 'João Silva',
                'email': 'joao@teste.com',
                'password': generate_password_hash('123456'),
                'instrument': 'Vocal',
                'phone': '(11) 98765-4321',
                'is_admin': False
            },
            {
                'name': 'Maria Santos',
                'email': 'maria@teste.com',
                'password': generate_password_hash('123456'),
                'instrument': 'Teclado',
                'phone': '(11) 98765-4322',
                'is_admin': False
            },
            {
                'name': 'Pedro Costa',
                'email': 'pedro@teste.com',
                'password': generate_password_hash('123456'),
                'instrument': 'Guitarra',
                'phone': '(11) 98765-4323',
                'is_admin': False
            },
            {
                'name': 'Ana Paula',
                'email': 'ana@teste.com',
                'password': generate_password_hash('123456'),
                'instrument': 'Bateria',
                'phone': '(11) 98765-4324',
                'is_admin': False
            },
            {
                'name': 'Carlos Oliveira',
                'email': 'carlos@teste.com',
                'password': generate_password_hash('123456'),
                'instrument': 'Baixo',
                'phone': '(11) 98765-4325',
                'is_admin': False
            }
        ]
        
        membros_criados = []
        for membro_data in membros_data:
            membro = Member.query.filter_by(email=membro_data['email']).first()
            if not membro:
                membro = Member(**membro_data)
                db.session.add(membro)
                membros_criados.append(membro)
        
        db.session.commit()
        print(f"✅ {len(membros_criados)} membros criados")
        
        # 2. CRIAR CULTOS
        print("\n📅 Criando cultos...")
        hoje = date.today()
        cultos_data = []
        
        # Cultos passados
        for i in range(4):
            dias_atras = 7 * (i + 1)
            data_culto = hoje - timedelta(days=dias_atras)
            cultos_data.append({
                'date': data_culto,
                'time': time(19, 0),  # 19:00
                'description': f'Culto de Celebração - {data_culto.strftime("%d/%m")}'
            })
        
        # Cultos futuros
        for i in range(4):
            dias_frente = 7 * (i + 1)
            data_culto = hoje + timedelta(days=dias_frente)
            cultos_data.append({
                'date': data_culto,
                'time': time(19, 0),  # 19:00
                'description': f'Culto de Celebração - {data_culto.strftime("%d/%m")}'
            })
        
        cultos_criados = []
        for culto_data in cultos_data:
            culto = Culto(**culto_data)
            db.session.add(culto)
            cultos_criados.append(culto)
        
        db.session.commit()
        print(f"✅ {len(cultos_criados)} cultos criados")
        
        # 3. CRIAR MÚSICAS
        print("\n🎵 Criando músicas...")
        musicas_data = [
            {'title': 'Ruja o Leão', 'artist': 'Davi Sacer', 'tone': 'G'},
            {'title': 'Oceanos', 'artist': 'Hillsong', 'tone': 'D'},
            {'title': 'Além do Rio Azul', 'artist': 'Leandro Borges', 'tone': 'C'},
            {'title': 'Hosana', 'artist': 'Gabriela Rocha', 'tone': 'E'},
            {'title': 'Nada Além do Sangue', 'artist': 'Fernandinho', 'tone': 'A'},
            {'title': 'Como Zaqueu', 'artist': 'Regis Danese', 'tone': 'F'},
            {'title': 'Quão Grande é o Meu Deus', 'artist': 'Soraya Moraes', 'tone': 'G'},
            {'title': 'Deus da Minha Vida', 'artist': 'Morada', 'tone': 'C'},
            {'title': 'Bondade de Deus', 'artist': 'Isaías Saad', 'tone': 'D'},
            {'title': 'Way Maker', 'artist': 'Sinach', 'tone': 'B'}
        ]
        
        musicas_criadas = []
        for musica_data in musicas_data:
            musica = Repertorio.query.filter_by(
                title=musica_data['title'], 
                artist=musica_data['artist']
            ).first()
            if not musica:
                musica = Repertorio(**musica_data)
                db.session.add(musica)
                musicas_criadas.append(musica)
        
        db.session.commit()
        print(f"✅ {len(musicas_criadas)} músicas criadas")
        
        # RESUMO
        print("\n" + "="*50)
        print("✅ BANCO POPULADO COM SUCESSO!")
        print("="*50)
        print(f"📊 Total no banco:")
        print(f"   • Membros: {Member.query.count()}")
        print(f"   • Cultos: {Culto.query.count()}")
        print(f"   • Músicas: {Repertorio.query.count()}")
        print("\n🔐 Logins de teste:")
        print("   • Admin: admin@ministry.com / admin123")
        print("   • Membro: joao@teste.com / 123456")
        print("="*50 + "\n")

if __name__ == '__main__':
    popular_banco()
