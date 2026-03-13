# 🚀 Deploy Rápido com render.yaml

Este arquivo automatiza a criação do Web Service e do PostgreSQL no Render.

## 📦 Opção 1: Deploy Automático com render.yaml

### Vantagens
✅ Cria Web Service e PostgreSQL automaticamente  
✅ Conecta DATABASE_URL automaticamente  
✅ Configuração em 1 clique  

### Como Usar

1. **Faça commit do render.yaml:**
   ```bash
   git add render.yaml
   git commit -m "Add: Configuração automática Render"
   git push origin main
   ```

2. **Acesse o Render:**
   - Vá em https://dashboard.render.com
   - Clique em **"New +"** → **"Blueprint"**
   - Conecte seu repositório GitHub
   - Selecione o repositório `AppML`
   - O Render detectará o `render.yaml` automaticamente
   - Clique em **"Apply"**

3. **Aguarde:**
   - PostgreSQL será criado (2-3 minutos)
   - Web Service será criado e deployado (3-5 minutos)
   - DATABASE_URL será configurada automaticamente

4. **Verificar:**
   - Acesse os Logs do Web Service
   - Procure: `Usando banco de dados: PostgreSQL`
   - Teste o app!

---

## 🔧 Opção 2: Configuração Manual (Sem render.yaml)

Se preferir configurar manualmente ou já tem o Web Service criado:

1. **Siga o guia:** [CONFIGURAR_BANCO_RENDER.md](CONFIGURAR_BANCO_RENDER.md)
2. **Ignore o render.yaml** (pode deletar se quiser)

---

## ⚙️ O que o render.yaml faz?

```yaml
# Cria Web Service
- Nome: ministry-app
- Runtime: Python 3.11
- Comando build: pip install -r requirements.txt
- Comando start: gunicorn app:app
- Plano: Free

# Cria PostgreSQL
- Nome: ministry-db
- Plano: Free (256MB)
- Conecta automaticamente via DATABASE_URL
```

---

## 🔄 Atualizar Configuração

Se já usou render.yaml e quer mudar configurações:

1. Edite o `render.yaml`
2. Faça commit e push
3. No Render, vá em **Dashboard** → Seu Blueprint
4. Clique em **"Sync"** para aplicar mudanças

---

## 📝 Notas Importantes

- ⚠️ O PostgreSQL Free Plan **expira após 90 dias** mas pode ser renovado gratuitamente
- 💡 Você pode migrar para Starter Plan ($7/mês) depois sem perder dados
- 🔐 O render.yaml **não expõe** senhas - o Render gera automaticamente
- 📊 O banco fica vazio inicialmente - o app cria as tabelas e admin automaticamente

---

## 🎯 Qual Opção Escolher?

| Situação | Recomendação |
|----------|--------------|
| **Primeiro deploy** | Use render.yaml (mais fácil) |
| **Já tem Web Service** | Configuração manual |
| **Quer rapidez** | Use render.yaml |
| **Quer controle total** | Configuração manual |

---

**Próximo Passo:** Escolha a Opção 1 (automático) ou Opção 2 (manual) e siga as instruções! 🚀
