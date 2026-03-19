"""
Limpa todas as push subscriptions do banco de dados
(necessário após gerar novas chaves VAPID)
"""
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///instance/ministry.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class PushSubscription(db.Model):
    __tablename__ = 'push_subscription'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    member_id = db.Column(db.Integer, db.ForeignKey('member.id'), nullable=True)
    endpoint = db.Column(db.String(500), nullable=False, unique=True)
    p256dh_key = db.Column(db.String(200), nullable=False)
    auth_key = db.Column(db.String(100), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

print("="*60)
print("  LIMPANDO PUSH SUBSCRIPTIONS")
print("="*60)

with app.app_context():
    total = PushSubscription.query.count()
    print(f"\n📊 Total de subscriptions antes: {total}")
    
    if total > 0:
        PushSubscription.query.delete()
        db.session.commit()
        print(f"✅ {total} subscriptions removidas!")
    else:
        print("⚠️ Nenhuma subscription encontrada")
    
    total_after = PushSubscription.query.count()
    print(f"📊 Total de subscriptions depois: {total_after}")

print("\n" + "="*60)
print("✅ LIMPEZA CONCLUÍDA!")
print("="*60)
print("\nPRÓXIMOS PASSOS:")
print("1. Acesse: http://localhost:5000/perfil")
print("2. Desative e depois REATIVE as notificações push")
print("3. Conceda permissão quando o browser solicitar")
print("4. Teste criando um aviso em: http://localhost:5000/avisos")
print("="*60)
