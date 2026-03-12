# Guia de Deploy no Render

## 🚀 Configuração Rápida

### 1. Variáveis de Ambiente no Render

Acesse o dashboard do Render e configure as seguintes variáveis de ambiente:

**Obrigatórias:**
```
SECRET_KEY=sua-chave-secreta-super-forte-aqui-mude-isto-12345678901234567890
FLASK_ENV=production
PORT=10000
```

**Opcionais:**
```
MAX_CONTENT_LENGTH=52428800
```

### 2. Banco de Dados

**✅ RECOMENDADO: PostgreSQL (Produção)**
1. No Render, crie um PostgreSQL Database
2. Conecte ao seu Web Service
3. O Render criará automaticamente a variável `DATABASE_URL`
4. A aplicação detectará e converterá automaticamente para o formato correto
5. **IMPORTANTE:** O app já possui `psycopg2-binary` nas dependências para PostgreSQL

**Opção alternativa: SQLite (Apenas testes - NÃO recomendado)**
- O Render pode ter problemas com SQLite pois o filesystem é efêmero
- Deixe `DATABASE_URL` sem configurar para usar SQLite (não recomendado)

### 3. Build e Deploy

O Render detectará automaticamente:
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `gunicorn app:app` (definido no Procfile)

### 4. Verificação Pós-Deploy

Após o deploy, verifique:
1. ✅ Aplicação iniciou sem erros
2. ✅ Você consegue acessar a URL fornecida pelo Render
3. ✅ Página de login aparece corretamente
4. ✅ Consegue fazer login com: `admin@ministry.com` / `admin123`

### 5. Configurações Adicionais

**Domínio Personalizado:**
- Acesse Settings > Custom Domain no Render
- Adicione seu domínio

**Logs:**
- Acesse Logs no dashboard para ver erros e debug

**Atualizações Automáticas:**
- O Render faz deploy automático a cada push no GitHub
- Para desabilitar: Settings > Auto-Deploy

### 6. Troubleshooting

**Erro "Application failed to start":**
- Verifique os logs no Render
- Certifique-se que `SECRET_KEY` está definido
- Verifique se o PostgreSQL está conectado (se usando)

**Erro 502 Bad Gateway:**
- Aguarde alguns minutos, o build pode estar em andamento
- Verifique os logs para erros de dependências

**Banco de dados vazio:**
- O app cria automaticamente as tabelas na primeira execução
- O usuário admin padrão é criado automaticamente

### 7. Segurança

⚠️ **IMPORTANTE:**
- Altere `SECRET_KEY` para uma chave única e forte
- Altere a senha do admin após primeiro login
- Use HTTPS (Render fornece automaticamente)
- Configure `FLASK_ENV=production` (nunca use `development`)

## 📱 URLs Importantes

- Dashboard Render: https://dashboard.render.com
- Repositório GitHub: https://github.com/Sthsantos/AppML
- Documentação Render: https://render.com/docs

## ✅ Checklist de Deploy

- [ ] Criar conta no Render
- [ ] Conectar repositório GitHub
- [ ] Criar Web Service
- [ ] Configurar variáveis de ambiente
- [ ] (Opcional) Criar PostgreSQL Database
- [ ] Aguardar primeiro deploy
- [ ] Testar aplicação
- [ ] Alterar senha do admin
- [ ] Configurar domínio personalizado (se desejado)

---

**Suporte:** Em caso de dúvidas, consulte os logs do Render ou a documentação oficial.
