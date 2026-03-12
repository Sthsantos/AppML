"""Script para resetar senha de um membro já cadastrado"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db, Member

def resetar_senha(email_membro, nova_senha='123456'):
    """Reseta a senha de um membro específico"""
    with app.app_context():
        membro = Member.query.filter_by(email=email_membro).first()
        
        if not membro:
            print(f"❌ Membro com email '{email_membro}' não encontrado!")
            print("\n📋 Membros disponíveis:")
            print("-" * 60)
            todos = Member.query.all()
            for m in todos[:10]:  # Mostra os 10 primeiros
                print(f"   {m.email} | {m.name} | {m.instrument}")
            return False
        
        # Resetar senha
        membro.set_password(nova_senha)
        db.session.commit()
        
        print("\n" + "=" * 60)
        print("✅ SENHA RESETADA COM SUCESSO!")
        print("=" * 60)
        print(f"👤 Nome: {membro.name}")
        print(f"📧 Email: {email_membro}")
        print(f"🔑 Nova Senha: {nova_senha}")
        print(f"🎵 Instrumento: {membro.instrument}")
        print(f"📞 Telefone: {membro.phone}")
        print("=" * 60)
        print(f"\n💡 Agora você pode fazer login com:")
        print(f"   Email: {email_membro}")
        print(f"   Senha: {nova_senha}")
        return True

def listar_membros():
    """Lista todos os membros cadastrados"""
    with app.app_context():
        print("\n" + "=" * 80)
        print("📋 TODOS OS MEMBROS CADASTRADOS NO SISTEMA")
        print("=" * 80)
        
        membros = Member.query.all()
        
        # Agrupar por instrumento
        por_instrumento = {}
        for m in membros:
            inst = m.instrument or "Sem instrumento"
            if inst not in por_instrumento:
                por_instrumento[inst] = []
            por_instrumento[inst].append(m)
        
        for instrumento, lista in sorted(por_instrumento.items()):
            print(f"\n🎵 {instrumento.upper()}:")
            print("-" * 80)
            for m in lista:
                status = "⚠️ SUSPENSO" if m.suspended else "✅"
                print(f"  {status} {m.email:40} | {m.name}")

if __name__ == '__main__':
    # Se passar argumentos na linha de comando
    if len(sys.argv) > 1:
        email = sys.argv[1]
        senha = sys.argv[2] if len(sys.argv) > 2 else '123456'
        resetar_senha(email, senha)
    else:
        # Modo interativo
        print("=" * 80)
        print("🔐 RESETAR SENHA DE MEMBRO")
        print("=" * 80)
        
        # Listar membros primeiro
        listar_membros()
        
        print("\n" + "=" * 80)
        print("RESETAR SENHA - EXEMPLOS RÁPIDOS")
        print("=" * 80)
        print("\nEscolha um membro popular para teste:\n")
        
        # Sugestões de membros para teste
        sugestoes = [
            ('sthenio@ministerio.com', 'Sthênio', 'Guitarrista'),
            ('patrick@ministerio.com', 'Patrick', 'Guitarrista'),
            ('andremiguel@ministerio.com', 'André Miguel', 'Baterista'),
            ('maykonkennedy@ministerio.com', 'Maykon Kennedy', 'Baixista'),
            ('gesielleonel@ministerio.com', 'Gesiel Leonel', 'Tecladista'),
        ]
        
        for i, (email, nome, inst) in enumerate(sugestoes, 1):
            print(f"{i}. {nome} ({inst})")
            print(f"   📧 {email}")
            print()
        
        print("=" * 80)
        print("DIGITE O NÚMERO OU EMAIL DO MEMBRO:")
        print("(Ou pressione Enter para resetar senha do Sthênio)")
        print("=" * 80)
        
        escolha = input("\nSua escolha: ").strip()
        
        # Se vazio, usar Sthênio como padrão
        if not escolha:
            escolha = "1"
        
        # Se for número, pegar da lista de sugestões
        if escolha.isdigit() and 1 <= int(escolha) <= len(sugestoes):
            email = sugestoes[int(escolha) - 1][0]
        else:
            email = escolha
        
        # Perguntar a senha
        print(f"\nDefina a nova senha (ou pressione Enter para usar '123456'):")
        senha = input("Nova senha: ").strip() or '123456'
        
        # Resetar
        resetar_senha(email, senha)
