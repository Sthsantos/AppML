"""
Script para diagnosticar subscriptions de push notifications
"""

import sys
import os

# Adicionar diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db, PushSubscription, User, Member
from flask_login import current_user

def diagnosticar_subscriptions():
    with app.app_context():
        print("\n" + "="*50)
        print("  DIAGNÓSTICO: Push Subscriptions")
        print("="*50 + "\n")
        
        # 1. Total de subscriptions
        total = PushSubscription.query.count()
        print(f"1️⃣ Total de subscriptions no banco: {total}")
        
        # 2. Subscriptions ativas
        ativas = PushSubscription.query.filter_by(is_active=True).count()
        print(f"2️⃣ Subscriptions ATIVAS: {ativas}")
        
        # 3. Subscriptions inativas
        inativas = PushSubscription.query.filter_by(is_active=False).count()
        print(f"3️⃣ Subscriptions INATIVAS: {inativas}")
        
        print("\n" + "-"*50)
        print("  Detalhes das Subscriptions")
        print("-"*50 + "\n")
        
        # 4. Listar todas as subscriptions
        subscriptions = PushSubscription.query.all()
        
        if not subscriptions:
            print("❌ Nenhuma subscription encontrada no banco de dados!")
            print("\nPossíveis causas:")
            print("  1. Usuário ainda não ativou notificações")
            print("  2. Erro ao salvar subscription")
            print("  3. Endpoint /push_subscribe não está funcionando")
        else:
            for i, sub in enumerate(subscriptions, 1):
                print(f"\nSubscription #{i}:")
                print(f"  ID: {sub.id}")
                print(f"  User ID: {sub.user_id}")
                print(f"  Member ID: {sub.member_id}")
                print(f"  Endpoint: {sub.endpoint[:50]}...")
                print(f"  Ativa: {'✅ SIM' if sub.is_active else '❌ NÃO'}")
                print(f"  Criada em: {sub.created_at}")
                print(f"  Última vez usada: {sub.last_used}")
                
                # Ver usuário/membro associado
                if sub.user_id:
                    user = User.query.get(sub.user_id)
                    if user:
                        print(f"  👤 Usuário: {user.email} (Role: {user.role})")
                
                if sub.member_id:
                    member = Member.query.get(sub.member_id)
                    if member:
                        print(f"  👥 Membro: {member.name} ({member.email})")
        
        print("\n" + "="*50)
        print("  Resumo")
        print("="*50 + "\n")
        
        if total == 0:
            print("⚠️ STATUS: Nenhuma subscription no banco")
            print("\n💡 SOLUÇÃO:")
            print("  1. Acesse http://localhost:5000/perfil")
            print("  2. Ative o toggle de notificações")
            print("  3. Aceite a permissão do navegador")
            print("  4. Execute este script novamente")
        elif ativas == 0:
            print("⚠️ STATUS: Existem subscriptions, mas nenhuma ativa")
            print("\n💡 SOLUÇÃO:")
            print("  Desative e ative novamente o toggle no perfil")
        else:
            print(f"✅ STATUS: {ativas} subscription(s) ativa(s)")
            print("\n💡 O botão 'Enviar Teste' deve funcionar!")
        
        print("\n" + "="*50 + "\n")

if __name__ == '__main__':
    diagnosticar_subscriptions()
