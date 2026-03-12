"""
Script para cadastrar cultos no sistema do Ministério de Louvor
"""

from datetime import datetime, date, time, timedelta
import os
import sys

# Obter o diretório base
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'instance', 'ministry.db')

# Configurar o ambiente
os.environ['FLASK_ENV'] = 'production'
os.environ['FLASK_DEBUG'] = '0'

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# Criar aplicação Flask mínima
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_PATH}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Definir modelo Culto
class Culto(db.Model):
    """Modelo para cultos do ministério."""
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    time = db.Column(db.Time, nullable=False)
    description = db.Column(db.String(255), nullable=False)

def get_all_tuesdays(start_date, end_date):
    """Retorna todas as terças-feiras entre duas datas"""
    current = start_date
    tuesdays = []
    while current <= end_date:
        if current.weekday() == 1:  # 1 = terça-feira
            tuesdays.append(current)
        current += timedelta(days=1)
    return tuesdays

def get_all_thursdays(start_date, end_date):
    """Retorna todas as quintas-feiras entre duas datas"""
    current = start_date
    thursdays = []
    while current <= end_date:
        if current.weekday() == 3:  # 3 = quinta-feira
            thursdays.append(current)
        current += timedelta(days=1)
    return thursdays

def get_all_sundays(start_date, end_date):
    """Retorna todos os domingos entre duas datas"""
    current = start_date
    sundays = []
    while current <= end_date:
        if current.weekday() == 6:  # 6 = domingo
            sundays.append(current)
        current += timedelta(days=1)
    return sundays

def get_first_sundays(start_date, end_date):
    """Retorna os primeiros domingos de cada mês entre duas datas"""
    first_sundays = []
    current = start_date
    
    while current <= end_date:
        # Pegar o primeiro dia do mês
        first_of_month = date(current.year, current.month, 1)
        
        # Encontrar o primeiro domingo do mês
        days_until_sunday = (6 - first_of_month.weekday()) % 7
        first_sunday = first_of_month + timedelta(days=days_until_sunday)
        
        # Se o primeiro domingo já passou no mês atual, avançar para o próximo mês
        if first_sunday >= current and first_sunday <= end_date:
            if first_sunday not in first_sundays:
                first_sundays.append(first_sunday)
        
        # Avançar para o próximo mês
        if current.month == 12:
            current = date(current.year + 1, 1, 1)
        else:
            current = date(current.year, current.month + 1, 1)
    
    return first_sundays

def cadastrar_cultos():
    """Cadastra todos os cultos no banco de dados"""
    
    with app.app_context():
        # Definir período: próximos 4 meses
        start_date = date.today()
        end_date = start_date + timedelta(days=120)  # ~4 meses
        
        cultos_cadastrados = 0
        cultos_existentes = 0
        
        print(f"Cadastrando cultos de {start_date} até {end_date}")
        print("=" * 80)
        
        # 1. ESCOLA BÍBLICA - Todas as terças às 19:30
        print("\n📚 Cadastrando Escola Bíblica (Terças 19:30)...")
        tuesdays = get_all_tuesdays(start_date, end_date)
        for tuesday in tuesdays:
            culto = Culto.query.filter_by(
                date=tuesday, 
                time=time(19, 30), 
                description="Escola Bíblica"
            ).first()
            
            if not culto:
                novo_culto = Culto(
                    date=tuesday,
                    time=time(19, 30),
                    description="Escola Bíblica"
                )
                db.session.add(novo_culto)
                cultos_cadastrados += 1
                print(f"   ✓ {tuesday.strftime('%d/%m/%Y')} - 19:30")
            else:
                cultos_existentes += 1
        
        # 2. CURA E LIBERTAÇÃO - Todas as quintas (3 cultos)
        print("\n✨ Cadastrando Cura e Libertação (Quintas)...")
        thursdays = get_all_thursdays(start_date, end_date)
        horarios_cura = [time(8, 0), time(17, 30), time(19, 30)]
        
        for thursday in thursdays:
            for horario in horarios_cura:
                culto = Culto.query.filter_by(
                    date=thursday,
                    time=horario,
                    description="Cura e Libertação"
                ).first()
                
                if not culto:
                    novo_culto = Culto(
                        date=thursday,
                        time=horario,
                        description="Cura e Libertação"
                    )
                    db.session.add(novo_culto)
                    cultos_cadastrados += 1
                    print(f"   ✓ {thursday.strftime('%d/%m/%Y')} - {horario.strftime('%H:%M')}")
                else:
                    cultos_existentes += 1
        
        # 3. CULTOS DE DOMINGO - 2 cultos (09:00 e 18:00)
        print("\n⛪ Cadastrando Cultos de Domingo...")
        sundays = get_all_sundays(start_date, end_date)
        first_sundays = get_first_sundays(start_date, end_date)
        
        for sunday in sundays:
            # Culto da manhã (09:00)
            if sunday in first_sundays:
                description_manha = "Santa Ceia - Manhã"
            else:
                description_manha = "Culto de Celebração - Manhã"
            
            culto = Culto.query.filter_by(
                date=sunday,
                time=time(9, 0),
                description=description_manha
            ).first()
            
            if not culto:
                novo_culto = Culto(
                    date=sunday,
                    time=time(9, 0),
                    description=description_manha
                )
                db.session.add(novo_culto)
                cultos_cadastrados += 1
                print(f"   ✓ {sunday.strftime('%d/%m/%Y')} - 09:00 - {description_manha}")
            else:
                cultos_existentes += 1
            
            # Culto da noite (18:00)
            if sunday in first_sundays:
                description_noite = "Santa Ceia - Noite"
            else:
                description_noite = "Culto de Celebração - Noite"
            
            culto = Culto.query.filter_by(
                date=sunday,
                time=time(18, 0),
                description=description_noite
            ).first()
            
            if not culto:
                novo_culto = Culto(
                    date=sunday,
                    time=time(18, 0),
                    description=description_noite
                )
                db.session.add(novo_culto)
                cultos_cadastrados += 1
                print(f"   ✓ {sunday.strftime('%d/%m/%Y')} - 18:00 - {description_noite}")
            else:
                cultos_existentes += 1
        
        # Commit de todas as alterações
        try:
            db.session.commit()
            print("\n" + "=" * 80)
            print(f"✅ SUCESSO!")
            print(f"   • Cultos cadastrados: {cultos_cadastrados}")
            print(f"   • Cultos já existentes: {cultos_existentes}")
            print(f"   • Total no banco: {Culto.query.count()}")
            print("=" * 80)
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ ERRO ao salvar cultos: {str(e)}")

if __name__ == '__main__':
    print("\n" + "=" * 80)
    print("CADASTRO DE CULTOS - MINISTÉRIO DE LOUVOR")
    print("=" * 80)
    cadastrar_cultos()
