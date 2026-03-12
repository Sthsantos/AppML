import sqlite3
from datetime import datetime

# Conectar ao banco de dados
db_path = 'instance/ministry.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("=" * 60)
print("TESTANDO INDISPONIBILIDADES")
print("=" * 60)

# Verificar se a tabela existe
cursor.execute("""
    SELECT name FROM sqlite_master 
    WHERE type='table' AND name='indisponibilidade'
""")
table_exists = cursor.fetchone()

if not table_exists:
    print("❌ Tabela 'indisponibilidade' NÃO existe!")
    conn.close()
    exit()

print("✅ Tabela 'indisponibilidade' existe\n")

# Buscar todas as indisponibilidades
cursor.execute("""
    SELECT 
        i.id,
        i.member_id,
        i.culto_id,
        i.date,
        i.reason,
        i.created_at
    FROM indisponibilidade i
    ORDER BY i.date DESC
""")

indisponibilidades = cursor.fetchall()

print(f"📊 Total de indisponibilidades: {len(indisponibilidades)}\n")

if indisponibilidades:
    print("Detalhes:")
    print("-" * 60)
    
    for ind in indisponibilidades:
        ind_id, member_id, culto_id, date_str, reason, created_at = ind
        
        print(f"\n🆔 ID: {ind_id}")
        print(f"   Member ID: {member_id}")
        
        # Verificar se o membro existe
        cursor.execute("SELECT id, name FROM member WHERE id = ?", (member_id,))
        member = cursor.fetchone()
        if member:
            print(f"   ✅ Membro: {member[1]} (ID: {member[0]})")
        else:
            print(f"   ❌ ERRO: Membro ID {member_id} NÃO EXISTE!")
        
        # Verificar culto
        if culto_id:
            cursor.execute("SELECT id, description FROM culto WHERE id = ?", (culto_id,))
            culto = cursor.fetchone()
            if culto:
                print(f"   ✅ Culto: {culto[1]} (ID: {culto[0]})")
            else:
                print(f"   ❌ ERRO: Culto ID {culto_id} NÃO EXISTE!")
        else:
            print(f"   Culto: Nenhum (geral)")
        
        print(f"   Data: {date_str}")
        print(f"   Motivo: {reason if reason else 'Sem motivo'}")
        print(f"   Cadastrado em: {created_at}")
else:
    print("ℹ️  Nenhuma indisponibilidade cadastrada")

conn.close()
print("\n" + "=" * 60)
