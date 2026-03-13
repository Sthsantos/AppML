# 🗄️ Configurar Banco de Dados PostgreSQL no Render

## ⚠️ Problema Atual

**Sintoma:** Dados cadastrados são apagados toda vez que faz deploy no Render.

**Causa:** O Render está usando **SQLite** (banco em arquivo) que é **efêmero** - o sistema de arquivos do Render é temporário e resetado a cada deploy.

**Solução:** Configurar **PostgreSQL** (banco externo persistente) no Render.

---

## 📋 Passo a Passo para Configurar PostgreSQL

### 1️⃣ Criar Banco PostgreSQL no Render

1. Acesse https://dashboard.render.com
2. Clique em **"New +"** → **"PostgreSQL"**
3. Configure:
   - **Name:** `ministry-db` (ou nome de sua preferência)
   - **Database:** `ministry` (nome do banco)
   - **User:** `ministry_user` (usuário)
   - **Region:** Mesma região do seu Web Service (geralmente `Oregon (US West)`)
   - **PostgreSQL Version:** 15 ou mais recente
   - **Plan:** **Free** (para começar)
4. Clique em **"Create Database"**
5. Aguarde 2-3 minutos para o banco ser criado

### 2️⃣ Obter a URL de Conexão

Após criar o banco:

1. Acesse o banco criado no dashboard
2. Vá em **"Info"** ou **"Connect"**
3. Copie a **"Internal Database URL"** (mais segura e rápida)
   - Formato: `postgresql://user:password@host:port/database`
   - Exemplo: `postgresql://ministry_user:abc123xyz@dpg-xyz.oregon-postgres.render.com/ministry`

⚠️ **IMPORTANTE:** Use a **Internal Database URL**, não a External!

### 3️⃣ Configurar Variável de Ambiente no Web Service

1. Acesse seu **Web Service** (AppML) no Render
2. Vá em **"Environment"** (menu lateral)
3. Adicione uma nova variável:
   - **Key:** `DATABASE_URL`
   - **Value:** Cole a URL copiada no passo anterior
4. Clique em **"Save Changes"**

O Render irá **redesploy automaticamente** após salvar.

### 4️⃣ Verificar se Funcionou

Após o deploy:

1. Acesse os **Logs** do Web Service
2. Procure pela linha:
   ```
   Usando banco de dados: PostgreSQL
   ```
   ✅ Se aparecer "PostgreSQL" → SUCESSO!
   ❌ Se aparecer "SQLite" → Verifique a variável DATABASE_URL

3. Teste cadastrando um membro
4. Faça um novo deploy (commit qualquer mudança)
5. **Verifique se os dados permanecem** 🎯

---

## 🔧 Verificação Técnica

### Como o App Detecta o Banco

O código já está preparado para usar PostgreSQL automaticamente:

```python
# app.py (linha 59)
database_url = os.environ.get('DATABASE_URL', 'sqlite:///' + os.path.join(app.instance_path, 'ministry.db'))

# Se DATABASE_URL existe → usa PostgreSQL
# Se DATABASE_URL não existe → usa SQLite (desenvolvimento local)
```

### Migração Automática

Ao conectar no PostgreSQL pela primeira vez:

1. `db.create_all()` cria todas as tabelas automaticamente
2. `create_admin()` cria o usuário admin padrão
3. Dados ficam **permanentemente** no PostgreSQL

---

## 📊 Comparação: SQLite vs PostgreSQL

| Aspecto | SQLite (Atual) | PostgreSQL (Recomendado) |
|---------|----------------|--------------------------|
| **Persistência** | ❌ Apagado a cada deploy | ✅ Dados permanentes |
| **Performance** | 🐢 Limitada | ⚡ Alta performance |
| **Concorrência** | ⚠️ Problemas com múltiplos acessos | ✅ Suporta milhares de conexões |
| **Produção** | ❌ Não recomendado | ✅ Ideal para produção |
| **Custo** | Grátis (efêmero) | Grátis (Free Plan) |
| **Backup** | ❌ Impossível persistir | ✅ Backups automáticos |

---

## 🎯 Planos PostgreSQL no Render

### Free Plan (Recomendado para Começar)
- ✅ **Gratuito**
- 📦 256 MB de armazenamento
- 🔌 1 GB de transferência/mês
- ⏰ Expira após 90 dias (mas pode renovar gratuitamente)
- ⚠️ Sem backups automáticos
- **Ideal para:** Teste, desenvolvimento, pequenos projetos

### Starter Plan ($7/mês)
- 💰 $7/mês
- 📦 1 GB de armazenamento
- 🔌 10 GB de transferência/mês
- 💾 Backups automáticos diários
- **Ideal para:** Produção pequena/média

### Standard Plan ($20/mês)
- 💰 $20/mês
- 📦 10 GB de armazenamento
- 🔌 100 GB de transferência/mês
- 💾 Backups automáticos com retenção de 7 dias
- **Ideal para:** Aplicações em crescimento

---

## 🔐 Segurança

### Boas Práticas com DATABASE_URL

✅ **Faça:**
- Use sempre **Internal Database URL** (mais segura)
- Nunca commite a URL no código
- Mantenha como variável de ambiente

❌ **Não Faça:**
- Não compartilhe a URL publicamente
- Não use External Database URL se ambos estiverem no Render
- Não hardcode credenciais no código

---

## 🆘 Troubleshooting

### Problema: "could not connect to server"

**Solução:**
1. Verifique se a DATABASE_URL está correta
2. Confirme que o banco PostgreSQL está "Available" no dashboard
3. Use Internal Database URL se Web Service e Database estiverem no Render

### Problema: "FATAL: password authentication failed"

**Solução:**
1. Recrie a DATABASE_URL (senha pode ter expirado)
2. Copie novamente do dashboard do PostgreSQL
3. Atualize a variável de ambiente

### Problema: Ainda aparece "SQLite" nos logs

**Solução:**
1. Verifique se salvou a variável DATABASE_URL
2. Confirme que o Web Service fez redesploy
3. Verifique se não há typo no nome da variável (deve ser exatamente `DATABASE_URL`)

### Problema: Tabelas não criadas automaticamente

**Solução:**
1. Verifique os logs do deploy
2. Procure por erros de migração
3. O `db.create_all()` cria automaticamente - se não funcionar, há erro de conexão

---

## 📝 Checklist de Configuração

- [ ] PostgreSQL criado no Render
- [ ] Internal Database URL copiada
- [ ] Variável DATABASE_URL adicionada ao Web Service
- [ ] Web Service redesployado
- [ ] Logs mostram "PostgreSQL" (não "SQLite")
- [ ] Admin padrão criado (`admin@ministry.com`)
- [ ] Teste: Cadastrar membro
- [ ] Teste: Fazer novo deploy
- [ ] ✅ Verificado: Dados permanecem após deploy

---

## 🎓 Recursos Adicionais

- [Documentação PostgreSQL Render](https://render.com/docs/databases)
- [Connecting to PostgreSQL](https://render.com/docs/postgresql-connecting)
- [Database Migration Guide](https://render.com/docs/migrate-from-heroku#migrating-databases)

---

**Status Atual:** ⚠️ Usando SQLite (dados não persistem)  
**Status Desejado:** ✅ Usando PostgreSQL (dados persistentes)  
**Próximo Passo:** Seguir o Passo 1️⃣ acima

---

💡 **Dica:** Após configurar PostgreSQL, você pode continuar usando SQLite localmente (desenvolvimento) sem problemas. O app detecta automaticamente qual banco usar!
