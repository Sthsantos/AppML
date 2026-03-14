# 🆘 SOLUÇÃO: Dados Perdidos no Render

## ❌ Problema

**Sintoma:** Quando o app no Render fica sem uso e "dorme", ao voltar os dados cadastrados (membros, escalas, cultos) foram perdidos.

**Causa:** O app está usando **SQLite** (banco em arquivo local). O Render usa containers efêmeros que são **descartados** quando o app dorme, perdendo todos os dados.

## ✅ Solução: Migrar para PostgreSQL

O PostgreSQL é um banco de dados **externo e persistente** - os dados ficam salvos permanentemente, mesmo quando o app dorme.

---

## 📋 PASSO A PASSO COMPLETO

### **PASSO 1: Verificar se está usando SQLite**

1. Acesse seu app no Render: https://dashboard.render.com
2. Clique no seu Web Service (ministry-app ou similar)
3. Vá em **"Logs"** no menu lateral
4. Role até o início dos logs e procure a linha:
   ```
   Usando banco de dados: SQLite
   ```
   ou
   ```
   Usando banco de dados: PostgreSQL
   ```

🔴 **Se aparecer "SQLite"** → Continue para o PASSO 2
🟢 **Se aparecer "PostgreSQL"** → Seu banco já está configurado, o problema é outro (veja Troubleshooting)

---

### **PASSO 2: Criar Banco PostgreSQL**

1. No dashboard do Render, clique em **"New +"** no canto superior direito
2. Selecione **"PostgreSQL"**
3. Preencha os campos:
   - **Name:** `ministry-db`
   - **Database:** `ministry`
   - **User:** `ministry_user`
   - **Region:** **MESMA REGIÃO DO SEU WEB SERVICE** (importante!)
   - **PostgreSQL Version:** `15` ou mais recente
   - **Plan:** Selecione **"Free"**

4. Clique em **"Create Database"**
5. ⏳ Aguarde 2-3 minutos para o banco ser criado

---

### **PASSO 3: Copiar URL de Conexão**

1. Após o banco ser criado, clique nele no dashboard
2. Na página do banco, vá até a seção **"Connections"**
3. Você verá duas URLs:
   - **Internal Database URL** (recomendada) ✅
   - **External Database URL**

4. Clique em **"Copy"** na **Internal Database URL**
   - Ela tem formato: `postgresql://ministry_user:senha@dpg-xxxxx.oregon-postgres.render.com/ministry`

⚠️ **IMPORTANTE:** Use a **Internal**, NÃO a External!

---

### **PASSO 4: Configurar Variável de Ambiente**

1. Volte para o dashboard e clique no seu **Web Service** (APP)
2. Vá em **"Environment"** no menu lateral esquerdo
3. Procure se já existe uma variável chamada `DATABASE_URL`:

   **Se NÃO existe:**
   - Clique em **"Add Environment Variable"**
   - **Key:** `DATABASE_URL`
   - **Value:** Cole a URL copiada no PASSO 3
   - Clique em **"Save Changes"**

   **Se JÁ existe:**
   - Clique no ícone de **editar** (lápis) ao lado de `DATABASE_URL`
   - Cole a nova URL no campo **Value**
   - Clique em **"Save Changes"**

4. ✅ O Render vai **automaticamente fazer um novo deploy**

---

### **PASSO 5: Aguardar Deploy**

1. Vá em **"Logs"** no menu lateral
2. Aguarde até aparecer:
   ```
   ==> Build successful 🎉
   ==> Starting service...
   Usando banco de dados: PostgreSQL
   ```

⏳ **Tempo estimado:** 1-3 minutos

---

### **PASSO 6: Verificar se Funcionou**

1. Acesse seu app (URL do Render)
2. Faça login com:
   - Email: `admin@ministry.com`
   - Senha: `admin123`

3. ⚠️ **ATENÇÃO:** Como você mudou de banco, **os dados antigos do SQLite não foram migrados**. Você precisará:
   - Cadastrar os membros novamente, OU
   - Importar dados (veja seção "Migrar Dados Antigos" abaixo)

4. **Teste de Persistência:**
   - Cadastre um membro teste
   - Aguarde 20 minutos (até o app "dormir")
   - Acesse novamente
   - ✅ **O membro cadastrado deve continuar lá!**

---

## 🔄 Migrar Dados Antigos (Opcional)

Se você tinha dados importantes no SQLite, precisará cadastrá-los novamente no PostgreSQL, pois:
- O SQLite ficava no container efêmero (já foi perdido)
- Não é possível recuperar dados do container antigo

**Opção 1: Recadastrar manualmente** (recomendado se tinha poucos dados)

**Opção 2: Popular dados de teste**
```bash
# No seu computador, com o DATABASE_URL configurado
python popular_dados_teste.py
```

---

## 🎯 Como Funciona Agora

### ANTES (SQLite - ❌ Problema)
```
App Render → SQLite (arquivo local no container)
              ↓
         Container dorme
              ↓
    Container é destruído
              ↓
         DADOS PERDIDOS ❌
```

### DEPOIS (PostgreSQL - ✅ Solução)
```
App Render → PostgreSQL (servidor externo)
              ↓                ↓
         Container dorme    Dados ficam
              ↓              no PostgreSQL
    Container é destruído        ↓
              ↓              Dados SEGUROS ✅
     Container novo inicia
              ↓
    Conecta no PostgreSQL → Dados ainda estão lá! 🎉
```

---

## 📊 Comparação

| Aspecto | SQLite (Antes) | PostgreSQL (Agora) |
|---------|----------------|-------------------|
| **Persistência** | ❌ Dados perdidos ao dormir | ✅ Dados permanentes |
| **Performance** | 🐢 Limitada | ⚡ Alta |
| **Produção** | ❌ NÃO recomendado | ✅ Ideal |
| **Múltiplos acessos** | ⚠️ Problemas | ✅ Suporta milhares |
| **Custo Render** | Grátis | Grátis (Free Plan) |
| **Expira?** | N/A | ⚠️ Após 90 dias (renova grátis) |

---

## 🆘 Troubleshooting

### ❌ Logs mostram "SQLite" mesmo após configurar DATABASE_URL

**Possíveis causas:**
1. Variável `DATABASE_URL` foi salva incorretamente
   - Verifique se não tem espaços extras
   - Verifique se copiou a URL completa

2. Deploy não aconteceu
   - Force um novo deploy: vá em "Manual Deploy" → "Deploy latest commit"

3. URL do PostgreSQL está errada
   - Volte ao banco PostgreSQL
   - Copie novamente a **Internal Database URL**
   - Atualize a variável

---

### ❌ Erro "could not connect to server" nos logs

**Causa:** Web Service e PostgreSQL estão em **regiões diferentes**

**Solução:**
1. Verifique a região do Web Service (Settings → Region)
2. Verifique a região do PostgreSQL
3. Se forem diferentes, você precisa:
   - Criar outro PostgreSQL na mesma região, OU
   - Recriar o Web Service na região do PostgreSQL

---

### ❌ Tabelas não são criadas

**Solução:**
O app cria tabelas automaticamente com `db.create_all()`. Se não funcionou:

1. Verifique os logs para erros de conexão
2. Force a criação manualmente:
   ```bash
   # No terminal do Render ou local com DATABASE_URL configurada
   python -c "from app import app, db; app.app_context().push(); db.create_all(); print('Tabelas criadas!')"
   ```

---

### ⚠️ PostgreSQL Free expira em 90 dias

O plano Free do PostgreSQL expira após 90 dias, mas:

**Opção 1: Renovar gratuitamente**
- Render envia email antes de expirar
- Clique no link para renovar por mais 90 dias
- Repita indefinidamente

**Opção 2: Upgrade para Starter ($7/mês)**
- Backups automáticos
- Não expira
- Mais espaço (1 GB)

---

## 💡 Próximos Passos Recomendados

1. ✅ **Altere a senha do admin**
   ```python
   # No perfil do admin, troque para uma senha forte
   ```

2. ✅ **Configure alertas no Render**
   - Settings → Notifications
   - Receba email se o app cair

3. ✅ **Monitore uso do PostgreSQL**
   - Database → Metrics
   - Veja espaço usado

4. ✅ **Faça backups mensais** (plano Free não tem backup automático)
   - Use `pg_dump` para exportar dados
   - Ou upgrade para Starter Plan

---

## 📞 Suporte

Se ainda tiver problemas:

1. **Verifique os logs** no Render
2. **Copie a mensagem de erro completa**
3. **Verifique qual banco está usando** (linha "Usando banco de dados:")
4. **Consulte:** [Documentação Render PostgreSQL](https://render.com/docs/databases)

---

## ✅ Checklist Final

Após seguir todos os passos:

- [ ] PostgreSQL criado no Render
- [ ] DATABASE_URL configurada no Web Service
- [ ] Deploy concluído com sucesso
- [ ] Logs mostram "Usando banco de dados: PostgreSQL"
- [ ] Consegui fazer login
- [ ] Cadastrei um dado de teste
- [ ] Aguardei 20 minutos
- [ ] Voltei e o dado ainda está lá ✅
- [ ] Alterei senha do admin
- [ ] Configurei alertas no Render

🎉 **PRONTO! Seus dados agora são permanentes!**
