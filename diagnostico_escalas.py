"""
Script de diagnóstico para verificar escalas e músicas
"""
import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'instance', 'ministry.db')

print("=" * 80)
print("DIAGNÓSTICO DO SISTEMA DE ESCALAS E MÚSICAS")
print("=" * 80)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Verificar escalas existentes
print("\n📋 ESCALAS CADASTRADAS:")
print("-" * 80)
cursor.execute("""
    SELECT COUNT(*) as total FROM escala
""")
total_escalas = cursor.fetchone()[0]
print(f"Total de escalas: {total_escalas}")

if total_escalas > 0:
    cursor.execute("""
        SELECT e.id, m.name, c.description, c.date, c.time
        FROM escala e
        JOIN member m ON e.member_id = m.id
        JOIN culto c ON e.culto_id = c.id
        ORDER BY c.date DESC, c.time DESC
        LIMIT 10
    """)
    print("\nÚltimas 10 escalas:")
    for row in cursor.fetchall():
        print(f"  ID: {row[0]} | Membro: {row[1]} | Culto: {row[2]} | Data: {row[3]} {row[4]}")

# Verificar cultos
print("\n\n⛪ CULTOS CADASTRADOS:")
print("-" * 80)
cursor.execute("""
    SELECT COUNT(*) as total FROM culto
""")
total_cultos = cursor.fetchone()[0]
print(f"Total de cultos: {total_cultos}")

if total_cultos > 0:
    cursor.execute("""
        SELECT id, description, date, time
        FROM culto
        ORDER BY date DESC, time DESC
        LIMIT 10
    """)
    print("\nÚltimos 10 cultos:")
    for row in cursor.fetchall():
        print(f"  ID: {row[0]} | {row[1]} | Data: {row[2]} {row[3]}")

# Verificar repertório
print("\n\n🎵 REPERTÓRIO DE MÚSICAS:")
print("-" * 80)
cursor.execute("""
    SELECT COUNT(*) as total FROM repertorio
""")
total_musicas = cursor.fetchone()[0]
print(f"Total de músicas cadastradas: {total_musicas}")

if total_musicas > 0:
    cursor.execute("""
        SELECT id, title, artist, key_tone, audio_file
        FROM repertorio
        ORDER BY title
        LIMIT 10
    """)
    print("\nPrimeiras 10 músicas:")
    for row in cursor.fetchall():
        audio_status = "✓ Tem áudio" if row[4] else "✗ Sem áudio"
        print(f"  ID: {row[0]} | {row[1]} - {row[2]} | Tom: {row[3]} | {audio_status}")

# Verificar relação culto_repertorio
print("\n\n🔗 MÚSICAS VINCULADAS AOS CULTOS:")
print("-" * 80)
cursor.execute("""
    SELECT COUNT(*) as total FROM culto_repertorio
""")
total_vinculos = cursor.fetchone()[0]
print(f"Total de vínculos culto-música: {total_vinculos}")

if total_vinculos > 0:
    cursor.execute("""
        SELECT c.description, c.date, r.title, cr."order"
        FROM culto_repertorio cr
        JOIN culto c ON cr.culto_id = c.id
        JOIN repertorio r ON cr.repertorio_id = r.id
        ORDER BY c.date DESC, cr."order"
        LIMIT 20
    """)
    print("\nÚltimos 20 vínculos:")
    for row in cursor.fetchall():
        print(f"  {row[0]} ({row[1]}) → {row[2]} (ordem: {row[3]})")

# Verificar arquivos de áudio
print("\n\n🎧 ARQUIVOS DE ÁUDIO NO SERVIDOR:")
print("-" * 80)
uploads_path = os.path.join(os.path.dirname(__file__), 'static', 'uploads')
if os.path.exists(uploads_path):
    audio_files = [f for f in os.listdir(uploads_path) if f.endswith(('.mp3', '.wav', '.ogg', '.m4a'))]
    print(f"Total de arquivos de áudio: {len(audio_files)}")
    if audio_files:
        print("\nArquivos encontrados:")
        for f in audio_files:
            size = os.path.getsize(os.path.join(uploads_path, f)) / 1024 / 1024
            print(f"  📁 {f} ({size:.2f} MB)")
else:
    print("❌ Pasta de uploads não encontrada!")

# Verificar integridade
print("\n\n🔍 VERIFICAÇÃO DE INTEGRIDADE:")
print("-" * 80)
cursor.execute("""
    SELECT r.title, r.audio_file
    FROM repertorio r
    WHERE r.audio_file IS NOT NULL AND r.audio_file != ''
""")
musicas_com_audio = cursor.fetchall()
print(f"Músicas com referência a áudio: {len(musicas_com_audio)}")

arquivos_faltando = []
for titulo, audio_file in musicas_com_audio:
    filepath = os.path.join(uploads_path, audio_file)
    if not os.path.exists(filepath):
        arquivos_faltando.append((titulo, audio_file))

if arquivos_faltando:
    print(f"\n⚠️  {len(arquivos_faltando)} arquivo(s) referenciado(s) mas não encontrado(s):")
    for titulo, arquivo in arquivos_faltando:
        print(f"  ❌ {titulo} → {arquivo}")
else:
    print("✅ Todos os arquivos de áudio estão no servidor!")

conn.close()

print("\n" + "=" * 80)
print("✅ DIAGNÓSTICO CONCLUÍDO!")
print("=" * 80)
