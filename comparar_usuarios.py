#!/usr/bin/env python3
"""Verifica os dois usuários e suas subscriptions."""
from app import app, db, User, PushSubscription

def verificar_usuarios():
    with app.app_context():
        print("\n" + "="*50)
        print("  COMPARANDO USUÁRIOS")
        print("="*50 + "\n")
        
        # Usuário 1: admin@ministry.com
        user1 = db.session.get(User, 1)
        if user1:
            print("👤 Usuário 1:")
            print(f"   Email: {user1.email}")
            print(f"   Role: {user1.role}")
            subs1 = PushSubscription.query.filter_by(user_id=1, is_active=True).count()
            print(f"   Subscriptions ativas: {subs1}")
        
        # Usuário 2: stheni@gmail.com
        user2 = db.session.get(User, 2)
        if user2:
            print("\n👤 Usuário 2:")
            print(f"   Email: {user2.email}")
            print(f"   Role: {user2.role}")
            subs2 = PushSubscription.query.filter_by(user_id=2, is_active=True).count()
            print(f"   Subscriptions ativas: {subs2}")
        
        print("\n" + "="*50)
        print("  RECOMENDAÇÃO")
        print("="*50)
        print("\n✅ Use stheni@gmail.com para RECEBER notificações")
        print("   (Este usuário tem subscription ativa)\n")
        print("💡 Para testar avisos:")
        print("   1. Faça login com: stheni@gmail.com")
        print("   2. Acesse: http://localhost:5000/avisos")
        print("   3. Crie um aviso")
        print("   4. Você receberá a notificação!\n")
        print("="*50 + "\n")

if __name__ == '__main__':
    verificar_usuarios()
