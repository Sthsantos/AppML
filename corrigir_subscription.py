#!/usr/bin/env python3
"""Corrige a subscription com IDs errados."""
from app import app, db, PushSubscription, User, Member

def corrigir():
    with app.app_context():
        print("\n" + "="*50)
        print("  CORRIGINDO SUBSCRIPTION")
        print("="*50 + "\n")
        
        # Buscar a subscription com user_id=1
        sub = PushSubscription.query.get(1)
        
        if not sub:
            print("❌ Subscription #1 não encontrada!")
            return
        
        print(f"📌 Subscription atual:")
        print(f"   ID: {sub.id}")
        print(f"   user_id: {sub.user_id}")
        print(f"   member_id: {sub.member_id}")
        print(f"   is_active: {sub.is_active}\n")
        
        # Corrigir para os IDs corretos
        sub.user_id = 2
        sub.member_id = 1
        sub.is_active = True
        
        db.session.commit()
        
        print("✅ Subscription corrigida!")
        print(f"   Novo user_id: {sub.user_id}")
        print(f"   Novo member_id: {sub.member_id}\n")
        
        print("="*50)
        print("Agora teste novamente o botão 'Enviar Teste'!")
        print("="*50 + "\n")

if __name__ == '__main__':
    corrigir()
