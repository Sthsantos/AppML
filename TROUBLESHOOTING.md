# ⚠️ Troubleshooting - Erro 500 no Render

## ✅ Correções Aplicadas

As seguintes correções foram implementadas para resolver o erro 500:

1. **✅ PostgreSQL Support**
   - Adicionado `psycopg2-binary==2.9.9` no requirements.txt
   - Necessário para conectar ao PostgreSQL do Render

2. **✅ DATABASE_URL Conversion**
   - Render usa `postgres://` mas SQLAlchemy 1.4+ requer `postgresql://`
   - Conversão automática implementada no código

3. **✅ Gunicorn Compatibility**
   - Inicialização do banco movida para fora do `if __name__ == '__main__'`
   - Garante que o banco seja criado quando rodado via Gunicorn

4. **✅ SECRET_KEY Validation**
   - Validação adicionada para ambiente de produção
   - Avisos exibidos se SECRET_KEY não estiver configurado

5. **✅ Better Error Handling**
   - Logs melhorados para facilitar debug
   - Tratamento de exceções aprimorado

## 🔍 Como Verificar se Funcionou

### 1. Acesse o Dashboard do Render
- URL: https://dashboard.render.com
- Vá para seu Web Service

### 2. Verifique os Logs
No Render, clique em **"Logs"** e procure por:

**✅ Sinais de Sucesso:**
```
✅ Aplicação inicializada com sucesso!
Tabelas do banco de dados criadas/verificadas.
Usando banco de dados: PostgreSQL
```

**❌ Erros Comuns:**

#### Erro: "psycopg2 not found"
**Solução:** Aguarde o build completar. O psycopg2-binary está sendo instalado.

#### Erro: "SECRET_KEY not set"
**Solução:** 
1. Vá em Environment no Render
2. Adicione: `SECRET_KEY=sua-chave-forte-aqui-123456789`

#### Erro: "connection refused" ou "database does not exist"
**Solução:**
1. Verifique se o PostgreSQL Database foi criado no Render
2. Certifique-se que está conectado ao Web Service
3. A variável DATABASE_URL deve aparecer automaticamente

#### Erro: "No module named 'dotenv'"
**Solução:** Já está em requirements.txt, aguarde o build.

## 🎯 Checklist de Verificação

- [ ] PostgreSQL Database criado no Render?
- [ ] DATABASE_URL aparece nas variáveis de ambiente?
- [ ] SECRET_KEY está configurado?
- [ ] FLASK_ENV=production está configurado?
- [ ] Build completou sem erros?
- [ ] Logs mostram "Aplicação inicializada com sucesso!"?

## 📋 Variáveis de Ambiente Necessárias

No Render, configure em **Environment**:

```
SECRET_KEY=gere-uma-chave-forte-unica-aqui-com-pelo-menos-32-caracteres
FLASK_ENV=production
```

Opcionais:
```
MAX_CONTENT_LENGTH=52428800
PORT=10000
```

**IMPORTANTE:** O `DATABASE_URL` é criado automaticamente pelo Render quando você conecta o PostgreSQL Database.

## 🔄 Se Ainda Houver Erro

1. **Force Redeploy:**
   - No Render: Manual Deploy > Deploy latest commit

2. **Verifique Requirements:**
   ```bash
   # Localmente, teste se todas as dependências instalam:
   pip install -r requirements.txt
   ```

3. **Teste Localmente com PostgreSQL:**
   ```bash
   # Configure DATABASE_URL localmente:
   export DATABASE_URL="postgresql://..."
   python app.py
   ```

4. **Logs Detalhados:**
   - No Render, ative "Show timestamps" nos Logs
   - Envie os logs para análise se o problema persistir

## 📞 Suporte

Se o erro persistir após essas correções:

1. Copie os logs completos do Render (últimas 50 linhas)
2. Verifique se todas as variáveis de ambiente estão configuradas
3. Confirme que o PostgreSQL Database está "Available"
4. Verifique se o build completou 100%

## ✅ Status Atual

**Commit:** 709d880 - CORREÇÃO CRÍTICA: Resolver erro 500 no Render
**Data:** 2026-03-12
**Status:** Todas as correções aplicadas e enviadas para produção

---

**As correções foram aplicadas. O Render fará deploy automático em 2-5 minutos.**
