"""
Limpa todas as push subscriptions usando SQLite direto
"""
import sqlite3

print("="*60)
print("  LIMPANDO PUSH SUBSCRIPTIONS (SQLite direto)")
print("="*60)

# Conectar ao banco
conn = sqlite3.connect('instance/ministry.db')
cursor = conn.cursor()

# Contar subscriptions antes
cursor.execute("SELECT COUNT(*) FROM push_subscription")
total_antes = cursor.fetchone()[0]
print(f"\n📊 Total de subscriptions antes: {total_antes}")

if total_antes > 0:
    # Deletar todas
    cursor.execute("DELETE FROM push_subscription")
    conn.commit()
    print(f"✅ {total_antes} subscriptions removidas!")
else:
    print("⚠️ Nenhuma subscription encontrada")

# Contar depois
cursor.execute("SELECT COUNT(*) FROM push_subscription")
total_depois = cursor.fetchone()[0]
print(f"📊 Total de subscriptions depois: {total_depois}")

conn.close()

print("\n" + "="*60)
print("✅ LIMPEZA CONCLUÍDA!")
print("="*60)
print("\n🔄 PRÓXIMOS PASSOS:")
print("1. Reinicie Flask: .venv\\Scripts\\python.exe app.py")
print("2. Acesse: http://localhost:5000/perfil")
print("3. Desative e depois REATIVE as notificações push")
print("4. Conceda permissão quando o browser solicitar")
print("5. Teste criando um aviso em: http://localhost:5000/avisos")
print("="*60)
