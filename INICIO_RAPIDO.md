# 🚀 INÍCIO RÁPIDO - MINISTÉRIO DE LOUVOR

## Iniciar o Sistema

### Windows
```bash
run_app.bat
```

### Linux/Mac ou Linha de Comando
```bash
python app.py
```

## Acessar

Abra seu navegador em: **http://127.0.0.1:5000**

## Login Padrão (Admin)

- **Usuário**: `admin`
- **Senha**: `admin123`

⚠️ **IMPORTANTE**: Altere a senha após o primeiro login!

---

## ✨ Principais Recursos

### Para Todos os Membros
- 📋 Ver escalas atribuídas
- ❌ Registrar indisponibilidades
- 🎵 Consultar repertório musical
- 🎧 Ouvir playbacks/VSs
- 📢 Ver avisos
- 💬 Enviar feedback

### Para Administradores
Tudo acima + 
- 👥 Gerenciar membros
- 📅 Criar cultos
- 📋 Gerar escalas automaticamente
- ✅ Aprovar/rejeitar indisponibilidades
- 🎼 Adicionar músicas com áudio
- 📢 Publicar avisos
- 📊 Ver dashboard completo

---

## 🎵 Como Adicionar Música com Áudio

1. Login como **admin**
2. Menu **"Repertório Musical"**
3. Botão **"Adicionar Música"**
4. Preencher dados:
   - ✅ Título (obrigatório)
   - Artista, tom, categoria...
   - **📎 Selecionar arquivo de áudio**
5. Sistema valida automaticamente
6. **Salvar** → Player disponível na lista!

### Formatos Aceitos
- MP3, WAV, OGG, M4A, AAC, FLAC
- Tamanho máximo: **50MB**

---

## 📋 Como Criar Escalas

### Método 1: Individual
1. Menu **"Escalas"**
2. **"Adicionar Membro à Escala"**
3. Selecionar culto, membro e função
4. Salvar

### Método 2: Automática (Recomendado)
1. Menu **"Escalas"**
2. **"Gerar Escalas Automaticamente"**
3. Sistema distribui membros disponíveis
4. Revisar e editar se necessário

---

## ❌ Indisponibilidades

### Como Membro
1. Menu **"Indisponibilidade"**
2. Verificar se período está **ABERTO**
3. **"Adicionar Indisponibilidade"**
4. Selecionar data(s) e motivo
5. Aguardar aprovação do admin

### Como Admin
1. **Dashboard** → **"Gerenciar Indisponibilidades"**
2. Ver todas com status (pendente/aprovado/rejeitado)
3. Aprovar ou rejeitar com resposta
4. Controlar período (ABRIR/FECHAR)

---

## ⚙️ Configurações Importantes

### Alterar Senha (Admin)
```python
# Executar no terminal Python:
from app import db, User
from werkzeug.security import generate_password_hash

user = User.query.filter_by(username='admin').first()
user.password_hash = generate_password_hash('SUA_NOVA_SENHA')
db.session.commit()
```

### Backup do Banco
Copiar pasta: `instance/ministry.db`

### Limpar Dados de Teste
```python
# CUIDADO: Apaga tudo exceto admin!
from app import db, Culto, Escala, Indisponibilidade

Escala.query.delete()
Culto.query.delete()
Indisponibilidade.query.delete()
db.session.commit()
```

---

## 🔧 Solução de Problemas

### Servidor não inicia
```bash
# Verificar dependências
pip install -r requirements.txt

# Verificar Python
python --version  # Deve ser 3.8+
```

### Erro ao adicionar música com áudio
- ✅ Verificar tamanho (máx 50MB)
- ✅ Verificar formato (MP3, WAV, etc.)
- ✅ Verificar permissões da pasta `static/uploads/`

### Página em branco
- F5 para recarregar
- F12 → Console para ver erros
- Limpar cache do navegador

### Banco de dados corrompido
```bash
# Deletar e reiniciar (CUIDADO: perde dados!)
rm instance/ministry.db
python app.py  # Recria automático
```

---

## 📞 Verificação de Saúde

Execute periodicamente:
```bash
python verificar_sistema.py
```

---

## 🎯 Próximos Passos Sugeridos

1. ✅ Alterar senha do admin
2. ✅ Cadastrar todos os membros
3. ✅ Criar primeiros cultos
4. ✅ Adicionar músicas ao repertório
5. ✅ Gerar escalas
6. ✅ Testar sistema completo

---

**Sistema pronto para uso! 🎉**

Para documentação completa, consulte: `README_SISTEMA.md`
