# 🎯 GUIA PASSO A PASSO - Configurar PostgreSQL no Render

## ⏱️ Tempo estimado: 5-10 minutos

---

## 🚀 PASSO 1: Acessar o Dashboard do Render

1. Abra seu navegador
2. Acesse: **https://dashboard.render.com**
3. Faça login com sua conta
4. Você verá a lista dos seus serviços

✅ **Checkpoint:** Você está vendo o dashboard com seus serviços?

---

## 🗄️ PASSO 2: Criar o Banco PostgreSQL

1. No dashboard, clique no botão **"New +"** (azul, canto superior direito)

2. No menu que aparecer, clique em **"PostgreSQL"**

3. Preencha o formulário que aparecer:

   ```
   Name: ministry-db
   ```
   ↑ Digite exatamente isso (ou outro nome de sua preferência)

   ```
   Database: ministry
   ```
   ↑ Nome do banco de dados

   ```
   User: ministry_user
   ```
   ↑ Nome do usuário do banco

   ```
   Region: Oregon (US West)
   ```
   ↑ **IMPORTANTE:** Escolha a MESMA região onde está seu Web Service (app)
   
   Para verificar a região do seu app:
   - Abra outra aba
   - Vá em Dashboard → Clique no seu Web Service
   - Veja em "Region" qual está usando
   - Volte e selecione a mesma

   ```
   PostgreSQL Version: 15
   ```
   ↑ Ou a versão mais recente disponível

   ```
   Plan: Free
   ```
   ↑ Selecione o plano **Free** (grátis)

4. Clique no botão **"Create Database"** (azul, no final da página)

5. **AGUARDE** 2-3 minutos enquanto o Render cria o banco

   Você verá uma tela com um spinner/loading dizendo "Creating..."

✅ **Checkpoint:** O banco foi criado e você está vendo a página do banco com status "Available"?

---

## 🔗 PASSO 3: Copiar a URL de Conexão

1. Você deve estar na página do banco **ministry-db** que acabou de criar

2. Role a página até encontrar a seção **"Connections"**

3. Você verá DOIS tipos de URL:
   - **Internal Database URL** ⬅️ É ESTA que você vai usar!
   - External Database URL (ignore esta)

4. Na linha **"Internal Database URL"**, clique no botão **"Copy"** (ícone de copiar)

   A URL copiada tem formato assim:
   ```
   postgresql://ministry_user:abc123xyz@dpg-ch9abcd1234.oregon-postgres.render.com/ministry
   ```

✅ **Checkpoint:** A URL foi copiada para sua área de transferência?

---

## ⚙️ PASSO 4: Configurar a Variável de Ambiente

1. Volte para o **Dashboard** (clique em "Dashboard" no menu superior)

2. Encontre seu **Web Service** (o app Flask) na lista
   - Deve ter um nome como "ministry-app" ou "app-ml" ou similar
   - É o serviço onde seu aplicativo está rodando

3. **Clique no nome do Web Service**

4. No menu lateral esquerdo, clique em **"Environment"**

5. Você verá uma lista de variáveis de ambiente existentes

6. **Procure se já existe uma variável chamada `DATABASE_URL`:**

   ### Se NÃO existe DATABASE_URL:
   
   a. Clique no botão **"Add Environment Variable"**
   
   b. No campo **"Key"**, digite:
   ```
   DATABASE_URL
   ```
   
   c. No campo **"Value"**, **cole a URL** que você copiou no PASSO 3
   
   d. Clique em **"Save Changes"** (botão azul)

   ### Se JÁ existe DATABASE_URL:
   
   a. Procure a linha com `DATABASE_URL`
   
   b. Clique no ícone de **editar (lápis)** ao lado
   
   c. **Apague o valor antigo**
   
   d. **Cole a nova URL** que você copiou no PASSO 3
   
   e. Clique em **"Save Changes"** (botão azul)

7. **O Render vai fazer deploy automaticamente!**
   
   Você verá uma mensagem: "Your service will be redeployed with the new environment variables"

✅ **Checkpoint:** Você salvou a variável DATABASE_URL e o deploy iniciou?

---

## ⏳ PASSO 5: Aguardar o Deploy

1. No menu lateral esquerdo, clique em **"Logs"**

2. Você verá o log do deploy acontecendo em tempo real

3. **Aguarde** até ver mensagens como:
   ```
   ==> Installing dependencies...
   ==> Building...
   ==> Build successful 🎉
   ==> Starting service...
   Usando banco de dados: PostgreSQL
   ```

4. **PROCURE** especificamente pela linha:
   ```
   Usando banco de dados: PostgreSQL
   ```
   
   ✅ **Se aparecer "PostgreSQL"** → SUCESSO! Continue para o PASSO 6
   
   ❌ **Se aparecer "SQLite"** → Algo deu errado, veja o "Troubleshooting" abaixo

⏱️ **Tempo:** 2-4 minutos

✅ **Checkpoint:** Deploy concluído e logs mostram "PostgreSQL"?

---

## 🧪 PASSO 6: Testar se Funcionou

1. Copie a **URL do seu app** (aparece no topo da página do Web Service)
   - Algo como: `https://ministry-app.onrender.com`

2. Abra essa URL em uma **nova aba anônima/privada** do navegador
   - Chrome: Ctrl + Shift + N
   - Firefox: Ctrl + Shift + P
   - Edge: Ctrl + Shift + N

3. Faça login:
   ```
   Email: admin@ministry.com
   Senha: admin123
   ```

4. **Cadastre um membro teste:**
   - Vá em "Membros" → "Adicionar Membro"
   - Preencha com dados fictícios
   - Salve

5. **Teste de persistência:**
   - Anote o nome do membro que você cadastrou
   - **Aguarde 20 minutos** (para o app "dormir")
   - Acesse novamente a URL do app
   - Faça login
   - Vá em "Membros"
   - ✅ **O membro deve estar lá!**

✅ **Checkpoint:** Conseguiu fazer login e cadastrar dados?

---

## 🎉 PASSO 7: Concluído!

**Parabéns!** Seu banco PostgreSQL está configurado!

### 🔒 Segurança - Importante:

1. **Altere a senha do admin:**
   - Faça login
   - Vá em "Perfil" ou "Configurações"
   - Altere a senha de `admin123` para algo forte

2. **Recadastre seus dados:**
   - Os dados antigos no SQLite foram perdidos
   - Cadastre novamente os membros, escalas, etc.

### 📊 Monitoramento:

- **Uso do PostgreSQL:** Dashboard → ministry-db → Metrics
- **Logs do app:** Dashboard → Seu Web Service → Logs
- **Expira em:** 90 dias (você receberá email para renovar gratuitamente)

---

## 🆘 TROUBLESHOOTING

### ❌ Problema: Logs ainda mostram "SQLite"

**Soluções:**

1. **Verifique a variável de ambiente:**
   - Web Service → Environment
   - Confirme que DATABASE_URL existe
   - Confirme que o valor começa com `postgresql://`
   - Não pode ter espaços extras

2. **Force um novo deploy:**
   - Web Service → Manual Deploy
   - Clique em "Clear build cache & deploy"

3. **Verifique se copiou a URL correta:**
   - Volte no banco PostgreSQL
   - Vá em Connections
   - Copie novamente a **Internal** Database URL
   - Atualize DATABASE_URL no Web Service

---

### ❌ Problema: "could not connect to server"

**Causa:** Web Service e PostgreSQL em regiões diferentes

**Solução:**

1. Verifique a região do Web Service:
   - Dashboard → Web Service → Settings → Region

2. Verifique a região do PostgreSQL:
   - Dashboard → ministry-db → Info → Region

3. Se forem diferentes:
   - **Opção A:** Delete o PostgreSQL e crie novamente na mesma região do Web Service
   - **Opção B:** Use External Database URL ao invés da Internal

---

### ❌ Problema: Tabelas não foram criadas

**Solução:**

O app cria automaticamente. Se não funcionou, verifique os logs:

1. Dashboard → Web Service → Logs
2. Procure por erros em vermelho
3. Procure pela linha "Tabelas do banco de dados criadas"

Se não aparecer, há erro na conexão.

---

### ❌ Problema: Esqueci a senha do admin

**Solução:**

Se você tem acesso SSH ao Render Shell:

```python
python -c "from app import app, db, User; from werkzeug.security import generate_password_hash; app.app_context().push(); admin = User.query.filter_by(email='admin@ministry.com').first(); admin.password_hash = generate_password_hash('admin123'); db.session.commit(); print('Senha resetada!')"
```

Ou crie um script `reset_admin_senha.py` e execute no Render.

---

## 📞 Precisa de Mais Ajuda?

1. **Verifique os logs completos:** Web Service → Logs
2. **Copie mensagens de erro:** E procure no Google ou me pergunte
3. **Documentação Render:** https://render.com/docs/databases

---

## ✅ CHECKLIST FINAL

Marque conforme for completando:

- [ ] Criei o banco PostgreSQL no Render
- [ ] Copiei a Internal Database URL
- [ ] Configurei DATABASE_URL no Web Service
- [ ] Aguardei o deploy terminar
- [ ] Logs mostram "Usando banco de dados: PostgreSQL"
- [ ] Consegui fazer login no app
- [ ] Cadastrei um dado de teste
- [ ] Alterei a senha do admin
- [ ] Testei após 20 minutos (opcional, mas recomendado)

---

**🎯 Está pronto! Seus dados agora são PERMANENTES!** 🎉
