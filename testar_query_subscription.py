#!/usr/bin/env python3
"""Testa query de subscriptions diretamente."""
from app import app, db, PushSubscription, User, Member
from sqlalchemy import or_

def testar_query():
    with app.app_context():
        print("\n" + "="*50)
        print("  TESTE DE QUERY - PUSH SUBSCRIPTIONS")
        print("="*50 + "\n")
        
        # Simular usuário ID 2
        user_id = 2
        
        # Buscar Member associado ao User ID 2
        user = User.query.get(user_id)
        if user:
            print(f"✅ User encontrado: ID={user.id}, Email={user.email}")
            
            member = Member.query.filter_by(email=user.email).first()
            if member:
                member_id = member.id
                print(f"✅ Member encontrado: ID={member.id}, Nome={member.name}\n")
            else:
                member_id = None
                print("⚠️ Nenhum Member com este email\n")
        else:
            print(f"❌ User ID {user_id} não encontrado!\n")
            return
        
        # Teste 1: Query simples por user_id
        print("1️⃣ Query por user_id:")
        subs1 = PushSubscription.query.filter_by(user_id=user_id, is_active=True).all()
        print(f"   Resultado: {len(subs1)} subscription(s)")
        for sub in subs1:
            print(f"   - Sub #{sub.id}: user_id={sub.user_id}, member_id={sub.member_id}\n")
        
        # Teste 2: Query simples por member_id
        if member_id:
            print("2️⃣ Query por member_id:")
            subs2 = PushSubscription.query.filter_by(member_id=member_id, is_active=True).all()
            print(f"   Resultado: {len(subs2)} subscription(s)")
            for sub in subs2:
                print(f"   - Sub #{sub.id}: user_id={sub.user_id}, member_id={sub.member_id}\n")
        
        # Teste 3: Query com OR (como está no código)
        print("3️⃣ Query com OR (user_id OU member_id):")
        query_filters = [PushSubscription.is_active == True]
        user_filters = []
        
        if user_id:
            user_filters.append(PushSubscription.user_id == user_id)
        if member_id:
            user_filters.append(PushSubscription.member_id == member_id)
        
        if user_filters:
            query_filters.append(or_(*user_filters))
            subs3 = PushSubscription.query.filter(*query_filters).all()
        else:
            subs3 = []
        
        print(f"   Resultado: {len(subs3)} subscription(s)")
        for sub in subs3:
            print(f"   - Sub #{sub.id}: user_id={sub.user_id}, member_id={sub.member_id}\n")
        
        # Teste 4: Todas as subscriptions (sem filtro)
        print("4️⃣ Todas as subscriptions ativas (sem filtro de usuário):")
        all_subs = PushSubscription.query.filter_by(is_active=True).all()
        print(f"   Resultado: {len(all_subs)} subscription(s)")
        for sub in all_subs:
            print(f"   - Sub #{sub.id}: user_id={sub.user_id}, member_id={sub.member_id}")
        
        print("\n" + "="*50)

if __name__ == '__main__':
    testar_query()
