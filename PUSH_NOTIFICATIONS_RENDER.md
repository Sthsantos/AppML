# 🔔 Configuração de Push Notifications no Render

## 📋 Pré-requisitos

O sistema de notificações push já está implementado e funcionando localmente. Para funcionar no Render, você precisa configurar as variáveis de ambiente corretas.

---

## 🔑 Variáveis de Ambiente Necessárias

Acesse o **Dashboard do Render** → Seu Web Service → **Environment** e adicione:

### 1. VAPID_PUBLIC_KEY
```
BIE96TdoPCTzTEV2CzZnopybGg9fXG2bo_uZt0nFY0KKi42e-zgneIS4R89Hw_oEQCaoCm0PaV_PkSAbduNLs50
```

### 2. VAPID_PRIVATE_KEY
```
-----BEGIN PRIVATE KEY-----
MIGHAgEAMBMGByqGSM49AgEGCCqGSM49AwEHBG0wawIBAQQgzRp0oAPfjQBk6DOk
PVOISDaEt6GEZebmFvTEtVB+PzuhRANCAASBPek3aDwk80xFdgs2Z6KcmxoPX1xt
m6P7mbdJxWNCiouNnvs4J3iEuEfPR8P6BEAmqAptD2lfz5EgG3bjS7Od
-----END PRIVATE KEY-----
```

**⚠️ IMPORTANTE:** No Render, cole a chave EXATAMENTE como está acima, com as quebras de linha. O código do app.py já trata isso automaticamente.

### 3. VAPID_CLAIMS_EMAIL
```
mailto:admin@ministry.com
```

---

## 📦 Bibliotecas Instaladas Automaticamente

O `requirements.txt` já foi atualizado com as versões corretas:

```txt
pywebpush==1.14.0
py-vapid==1.9.4
cryptography==42.0.0  # ⚠️ VERSÃO FIXA - NÃO ATUALIZAR!
http_ece==1.2.1
```

**⚠️ CRÍTICO:** A versão `cryptography==42.0.0` é obrigatória. A versão 46.x tem incompatibilidade com `pywebpush`.

---

## 🚀 Como Funciona no Render

1. **Deploy automático:** Ao fazer push para o GitHub, o Render detecta as mudanças

2. **Instalação de dependências:** O Render instala as bibliotecas do `requirements.txt`

3. **Criação da chave VAPID:**
   - O `app.py` verifica se existe `vapid_private.pem`
   - Se não existir, pega a variável `VAPID_PRIVATE_KEY` do ambiente
   - Cria o arquivo `instance/vapid_private.pem` automaticamente
   - Usa `Vapid.from_file()` para carregar a chave

4. **Envio de notificações:**
   - Quando um aviso é criado, o sistema busca usuários com push ativo
   - Envia notificação via Firebase Cloud Messaging (FCM)
   - Notificação aparece no navegador/Windows do usuário

---

## ✅ Verificação Pós-Deploy

### 1. Verificar Logs do Render

Após o deploy, verifique os logs e procure por:

```
✅ Usando VAPID key file: vapid_private.pem
```

OU

```
✅ VAPID key salva em: instance/vapid_private.pem
```

Se aparecer:
```
⚠️ VAPID_PRIVATE_KEY não encontrada!
```
**→ A variável de ambiente não foi configurada corretamente!**

### 2. Testar no Navegador

1. Acesse seu site no Render: `https://seu-app.onrender.com`

2. Faça login

3. Vá em **Perfil** (`/perfil`)

4. Ative o toggle **"Ativar Notificações Push"**

5. Clique em **"Permitir"** quando o navegador pedir permissão

6. Crie um **Aviso** em `/avisos`

7. **A notificação deve aparecer no canto inferior direito da tela!**

### 3. Verificar no Console do Navegador (F12)

```javascript
// Deve aparecer:
✅ Subscription created successfully

// Ao criar aviso:
[SW] Push notification recebida: PushEvent {...}
```

---

## 🔧 Troubleshooting

### Erro: "curve must be an EllipticCurve instance"

**Causa:** Versão errada do `cryptography` (46.x)

**Solução:**
1. Verifique `requirements.txt`:
   ```txt
   cryptography==42.0.0
   ```
2. Force rebuild no Render:
   - Dashboard → Manual Deploy → Clear build cache & deploy

### Erro: "VAPID credentials do not correspond"

**Causa:** Subscriptions antigas com VAPID keys diferentes

**Solução:**
1. Limpe as subscriptions antigas:
   ```python
   # No shell do Render ou localmente
   from app import db, PushSubscription
   PushSubscription.query.delete()
   db.session.commit()
   ```

2. Reative notificações no perfil (cria nova subscription)

### Notificação não aparece

**Verificar:**

1. **Permissão do navegador:**
   - Chrome: `chrome://settings/content/notifications`
   - Edge: `edge://settings/content/notifications`
   - Verifique se o site está na lista de "Permitidos"

2. **Windows Notifications:**
   - Windows → Configurações → Notificações
   - Ative "Obter notificações de aplicativos"
   - Verifique se o navegador está permitido

3. **Service Worker registrado:**
   - F12 → Application → Service Workers
   - Deve mostrar: `sw.js` - Status: Activated

4. **Logs do Render:**
   - Procure por erros no envio da notificação
   - Verifique se `✅ Resposta: Status 201` aparece

---

## 🔐 Segurança

### Não commitar ao GitHub:

✅ **VAPID keys já estão no `.env`** (que está no `.gitignore`)  
✅ **`vapid_private.pem` já está no `.gitignore`**  
✅ **`instance/` já está no `.gitignore`**

### ⚠️ NUNCA faça:

❌ Não remova `vapid_private.pem` do `.gitignore`  
❌ Não commite o arquivo `.env`  
❌ Não compartilhe as VAPID keys publicamente  

**Por quê?**  
As VAPID keys são como senhas. Se alguém tiver acesso, pode enviar notificações falsas para seus usuários.

---

## 📱 Funcionalidades Implementadas

### ✅ O que já funciona:

- [x] Registro de Service Worker (`sw.js`)
- [x] Solicitação de permissão no navegador
- [x] Criação de subscriptions (endpoint + keys)
- [x] Armazenamento no banco de dados (tabela `push_subscription`)
- [x] Envio automático ao criar avisos
- [x] Notificações com ícone e ações personalizadas
- [x] Suporte para diferentes prioridades (alta/normal/baixa)
- [x] Compatibilidade com Chrome, Edge, Firefox
- [x] Notificações no Windows Action Center
- [x] Notificações em mobile (Android/iOS)

### 🎨 Tipos de Notificações:

1. **Novo Aviso:** 
   - Ícone: 📢
   - Botão: "Ver Aviso"

2. **Nova Escala:**
   - Ícone: 📅
   - Botões: "Ver Escala" + "Confirmar Presença"

3. **Lembrete de Confirmação:**
   - Ícone: ⏰
   - Botões: "Confirmar" + "Não Poderei"

---

## 🌐 URLs Importantes

| Rota | Descrição |
|------|-----------|
| `/perfil` | Ativar/desativar notificações |
| `/push_subscribe` | API para criar subscription |
| `/push_unsubscribe` | API para remover subscription |
| `/push_test` | Testar envio de notificação |
| `/get_vapid_public_key` | Obter chave pública VAPID |

---

## 📊 Monitoramento

### Verificar subscriptions ativas:

```sql
SELECT COUNT(*) FROM push_subscription;
SELECT * FROM push_subscription WHERE user_id = 1;
```

### Ver avisos enviados com push:

```sql
SELECT id, titulo, prioridade, created_at 
FROM aviso 
ORDER BY created_at DESC 
LIMIT 10;
```

---

## 🎯 Próximos Passos (Futuro)

- [ ] Dashboard de estatísticas de notificações
- [ ] Agendamento de notificações
- [ ] Notificações personalizadas por grupo
- [ ] Templates de notificações
- [ ] Histórico de notificações enviadas

---

## 📞 Suporte

Se encontrar problemas:

1. Verifique os logs do Render
2. Teste localmente com `.venv\Scripts\python.exe app.py`
3. Verifique as variáveis de ambiente no Render
4. Consulte este documento

---

## 🔄 Resumo do Fluxo

```
┌─────────────────────────────────────────────────────────────┐
│  1. Usuário ativa toggle em /perfil                         │
│     ↓                                                        │
│  2. Service Worker cria subscription (endpoint + keys)      │
│     ↓                                                        │
│  3. Frontend envia POST /push_subscribe                     │
│     ↓                                                        │
│  4. Backend salva no banco (PushSubscription)               │
│     ↓                                                        │
│  5. Admin cria aviso em /avisos                             │
│     ↓                                                        │
│  6. Backend busca subscriptions ativas                      │
│     ↓                                                        │
│  7. Backend assina com VAPID keys                           │
│     ↓                                                        │
│  8. Envia para FCM (Firebase Cloud Messaging)               │
│     ↓                                                        │
│  9. FCM entrega ao navegador/device                         │
│     ↓                                                        │
│ 10. Service Worker mostra notificação                       │
│     ↓                                                        │
│ 11. Usuario vê notificação no Windows! 🎉                  │
└─────────────────────────────────────────────────────────────┘
```

---

**✅ Sistema pronto para produção!**

Última atualização: 18/03/2026
