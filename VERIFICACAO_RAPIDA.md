# ⚡ VERIFICAÇÃO RÁPIDA - 2 Minutos

## 🎯 O que você precisa fazer AGORA

### **OPÇÃO 1: Executar Script de Diagnóstico (Recomendado)**

No seu computador, abra o terminal na pasta do projeto e execute:

```bash
python diagnostico_banco.py
```

O script vai mostrar:
- ✅ Se está usando PostgreSQL (BOM) 
- ❌ Se está usando SQLite (PROBLEMA - dados serão perdidos)
- ✅ Se a conexão está funcionando
- 📊 Quais tabelas existem

---

### **OPÇÃO 2: Verificar Manualmente no Render**

1. Acesse: https://dashboard.render.com
2. Clique no seu **Web Service** (app)
3. Clique em **"Logs"** no menu lateral
4. Procure esta linha perto do início:

```
Usando banco de dados: PostgreSQL  ← ✅ BOM!
```
ou
```
Usando banco de dados: SQLite      ← ❌ PROBLEMA!
```

---

## 🔴 Se mostrou SQLite - URGENTE

Seus dados **SERÃO PERDIDOS** quando o app dormir!

**➡️ Solução:** [Abra este arquivo](SOLUCAO_DADOS_PERDIDOS.md) e siga o passo a passo (5-10 minutos)

---

## 🟢 Se mostrou PostgreSQL

Parabéns! Está configurado corretamente. Seus dados estão seguros.

**Possíveis razões para dados ainda serem perdidos:**
1. Você migrou recentemente e os dados antigos estavam no SQLite (já perdidos)
2. Erro na aplicação (verifique os logs)
3. Banco PostgreSQL expirou (plano free expira em 90 dias - renove gratuitamente)

---

## 📞 Precisa de Help?

Verifique os logs completos:
1. Dashboard Render → Seu App → Logs
2. Procure por mensagens de erro em vermelho
3. Copie e salve a mensagem de erro completa

---

## ✅ Checklist de 30 Segundos

- [ ] Executei `python diagnostico_banco.py` OU
- [ ] Verifiquei os logs no Render
- [ ] Identifiquei se está usando SQLite ou PostgreSQL
- [ ] Se SQLite: Abri o [SOLUCAO_DADOS_PERDIDOS.md](SOLUCAO_DADOS_PERDIDOS.md)
- [ ] Se PostgreSQL: Verifiquei se o banco não expirou

---

## 🚀 Próximos Passos Por Situação

### Caso 1: Está usando SQLite
→ [Migrar para PostgreSQL](SOLUCAO_DADOS_PERDIDOS.md) (URGENTE)

### Caso 2: Está usando PostgreSQL mas dados somem
→ Verifique se o banco PostgreSQL não expirou:
- Dashboard → Databases → ministry-db
- Se expirou: Renove gratuitamente ou crie novo

### Caso 3: Tudo configurado mas não funciona
→ Verifique os logs:
- Procure por "ERROR", "FAILED", "Exception"
- Veja se as tabelas foram criadas: `db.create_all()`

---

**⏱️ Tempo total:** 2-10 minutos para resolver!
