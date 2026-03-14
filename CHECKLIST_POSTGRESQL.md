# ✅ CHECKLIST RÁPIDO - PostgreSQL no Render

## 📋 Copie este checklist e vá marcando

```
⏱️ Tempo total: 5-10 minutos
🌐 URL: https://dashboard.render.com
```

---

## ☐ PASSO 1: Criar PostgreSQL (3 min)

```
1. Dashboard Render → "New +" → "PostgreSQL"
2. Preencher:
   Name:     ministry-db
   Database: ministry
   User:     ministry_user
   Region:   [mesma do seu Web Service!]
   Version:  15
   Plan:     Free
3. "Create Database" → Aguardar criar
```

---

## ☐ PASSO 2: Copiar URL (30 seg)

```
1. Na página do banco → Connections
2. "Internal Database URL" → Copiar
   (começa com postgresql://...)
```

---

## ☐ PASSO 3: Configurar DATABASE_URL (1 min)

```
1. Dashboard → Seu Web Service → "Environment"
2. Se DATABASE_URL não existe:
   → "Add Environment Variable"
   → Key: DATABASE_URL
   → Value: [colar URL copiada]
3. Se DATABASE_URL já existe:
   → Editar (ícone lápis)
   → Colar nova URL
4. "Save Changes" → Deploy automático inicia
```

---

## ☐ PASSO 4: Verificar Deploy (3 min)

```
1. Web Service → "Logs"
2. Aguardar até ver:
   "Usando banco de dados: PostgreSQL" ✅
   (NÃO pode ser "SQLite"!)
```

---

## ☐ PASSO 5: Testar (2 min)

```
1. Acessar URL do app
2. Login: admin@ministry.com / admin123
3. Cadastrar um membro teste
4. Sucesso! ✅
```

---

## 🎯 RESULTADO ESPERADO

**Antes (SQLite):**
```
App dorme → Dados PERDIDOS ❌
```

**Depois (PostgreSQL):**
```
App dorme → Dados MANTIDOS ✅
```

---

## 🆘 SE ALGO DER ERRADO

**Logs mostram "SQLite":**
→ DATABASE_URL não foi salva corretamente
→ Verifique Environment novamente

**Erro de conexão:**
→ Web Service e PostgreSQL em regiões diferentes
→ Recrie PostgreSQL na mesma região

**Não consigo fazer login:**
→ É normal, banco novo está vazio
→ Use: admin@ministry.com / admin123

---

## ✅ CONFIRMAÇÃO FINAL

Depois dos passos, você deve ver:

- ✅ Logs: "Usando banco de dados: PostgreSQL"
- ✅ App abrindo normalmente
- ✅ Login funciona (admin@ministry.com)
- ✅ Pode cadastrar dados
- ✅ Dados ficam salvos (teste após 20min)

---

**💡 Dica:** Mantenha este checklist aberto enquanto faz no navegador!
