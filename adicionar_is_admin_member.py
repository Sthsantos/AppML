"""Script para adicionar coluna is_admin à tabela Member"""
from app import app, db, Member

with app.app_context():
    print("🔧 Adicionando coluna 'is_admin' à tabela Member...")
    
    try:
        # Tentar criar a coluna
        with db.engine.connect() as conn:
            # Verificar se a coluna já existe
            result = conn.execute(db.text("PRAGMA table_info(member)"))
            columns = [row[1] for row in result]
            
            if 'is_admin' not in columns:
                print("   Coluna 'is_admin' não existe. Criando...")
                conn.execute(db.text("ALTER TABLE member ADD COLUMN is_admin BOOLEAN DEFAULT 0"))
                conn.commit()
                print("   ✅ Coluna criada!")
                
                # Atualizar todos os membros existentes para is_admin = False
                print("   Atualizando membros existentes...")
                conn.execute(db.text("UPDATE member SET is_admin = 0 WHERE is_admin IS NULL"))
                conn.commit()
                print("   ✅ Todos os membros configurados como NÃO-ADMIN")
            else:
                print("   ⚠️  Coluna 'is_admin' já existe!")
        
        print("\n✅ Migração concluída com sucesso!")
        print("\n📊 Testando acesso ao atributo...")
        
        # Testar se agora funciona
        membro_teste = Member.query.filter_by(email='sthenio@ministerio.com').first()
        if membro_teste:
            print(f"   Nome: {membro_teste.name}")
            print(f"   Email: {membro_teste.email}")
            print(f"   is_admin: {membro_teste.is_admin}")
            print("\n✅ Atributo is_admin acessível!")
        
    except Exception as e:
        print(f"❌ Erro na migração: {str(e)}")
        import traceback
        traceback.print_exc()
