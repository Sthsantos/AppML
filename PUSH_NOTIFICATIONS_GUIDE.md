# 🔔 Sistema de Notificações Push - Guia Completo

## 📋 Visão Geral

O sistema de notificações push permite que os membros e administradores recebam alertas em tempo real sobre eventos importantes, mesmo quando o aplicativo não está aberto. Utilizamos a **Web Push API** com autenticação VAPID, uma solução padrão da web que funciona em todos os navegadores modernos.

---

## 🚀 Configuração Inicial

### 1. Gerar VAPID Keys

As VAPID keys são necessárias para autenticar o servidor junto aos serviços de push dos navegadores.

```bash
python gerar_vapid_keys.py
```

Este script irá:
- Gerar um par de chaves pública/privada
- Salvar as chaves em `vapid_keys.json` (backup)
- Exibir as variáveis para adicionar ao `.env`

### 2. Configurar Variáveis de Ambiente

Adicione as chaves geradas ao arquivo `.env`:

```bash
# Push Notifications (Web Push API)
VAPID_PUBLIC_KEY=sua-chave-publica-aqui
VAPID_PRIVATE_KEY=sua-chave-privada-aqui
VAPID_CLAIMS_EMAIL=mailto:admin@ministry.com
```

**⚠️ IMPORTANTE:** 
- Nunca compartilhe a chave privada
- Use um email válido em `VAPID_CLAIMS_EMAIL`
- Mantenha o arquivo `vapid_keys.json` em local seguro

### 3. Instalar Dependências

```bash
pip install pywebpush==1.14.0
```

Ou use:

```bash
pip install -r requirements.txt
```

### 4. Executar Migração do Banco de Dados

Crie a tabela `push_subscription`:

```bash
python migrate_add_push_subscription.py
```

Isso criará uma tabela com a seguinte estrutura:

```sql
CREATE TABLE push_subscription (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,              -- FK para User (admins/líderes)
    member_id INTEGER,            -- FK para Member (membros)
    endpoint TEXT NOT NULL UNIQUE,  -- URL única do dispositivo
    p256dh_key TEXT NOT NULL,     -- Chave de criptografia pública
    auth_key TEXT NOT NULL,       -- Chave de autenticação
    device_info VARCHAR(500),     -- User agent do dispositivo
    created_at DATETIME,          -- Data de criação
    last_used DATETIME,           -- Último uso
    is_active BOOLEAN             -- Status ativo/inativo
);
```

---

## 👤 Guia do Usuário

### Como Ativar Notificações

1. **Acesse seu Perfil**
   - Entre no sistema e clique no seu nome no menu
   - Selecione "Perfil"

2. **Ative as Notificações**
   - Role até a seção "Notificações Push"
   - Clique no botão "Ativar Notificações"
   - Conceda permissão quando o navegador solicitar

3. **Teste o Sistema**
   - Após ativar, clique em "Enviar Teste"
   - Você deve receber uma notificação de teste

### Tipos de Notificações

Você receberá notificações sobre:

- ✅ **Novas Escalas**: Quando você for escalado para um culto
- ⏰ **Lembretes**: Confirmação de presença próximo ao evento
- 📢 **Avisos**: Comunicados importantes do ministério
- ⚠️ **Alertas**: Mudanças em cultos e repertórios

### Como Desativar

1. Acesse seu perfil
2. Encontre a seção "Notificações Push"
3. Clique em "Desativar" ou use o switch toggle

---

## 🔧 Arquitetura Técnica

### Componentes do Sistema

```
┌─────────────────────────────────────────────────────┐
│                   FRONTEND                          │
├─────────────────────────────────────────────────────┤
│ perfil.html           → UI de controle              │
│ push-manager.js       → Gerenciador de subscrições │
│ sw.js                 → Service Worker (handlers)   │
└─────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────┐
│                   BACKEND                           │
├─────────────────────────────────────────────────────┤
│ /get_vapid_public_key → Retorna chave pública      │
│ /push_subscribe       → Salva subscrição           │
│ /push_unsubscribe     → Remove subscrição          │
│ /push_test            → Envia teste                │
│ send_push_notification() → Função helper           │
└─────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────┐
│              PUSH SERVICE PROVIDER                  │
├─────────────────────────────────────────────────────┤
│ Google FCM (Chrome/Edge)                           │
│ Mozilla Push Service (Firefox)                     │
│ Apple Push Service (Safari)                        │
└─────────────────────────────────────────────────────┘
```

### Fluxo de Subscrição

```
1. Usuário clica em "Ativar Notificações"
   ↓
2. PushManager.subscribe() solicita permissão
   ↓
3. Navegador cria endpoint único + chaves de criptografia
   ↓
4. Frontend envia subscription para /push_subscribe
   ↓
5. Backend salva no banco de dados (PushSubscription)
   ↓
6. Servidor envia notificação de boas-vindas
   ↓
7. Service Worker recebe e exibe notificação
```

### Fluxo de Envio de Notificação

```
1. Evento acontece no sistema (nova escala, aviso, etc.)
   ↓
2. Backend chama send_push_notification(subscription, title, body, data)
   ↓
3. Monta payload JSON com título, mensagem, ações
   ↓
4. Envia via pywebpush.webpush() para Push Service
   ↓
5. Push Service entrega ao dispositivo do usuário
   ↓
6. Service Worker recebe evento 'push'
   ↓
7. Exibe notificação com self.registration.showNotification()
   ↓
8. Usuário clica → Service Worker navega para URL apropriada
```

---

## 📡 API Endpoints

### GET `/get_vapid_public_key`

Retorna a chave pública VAPID para subscrição.

**Response:**
```json
{
  "publicKey": "BNxw7T..."
}
```

### POST `/push_subscribe`

Salva uma nova subscrição de push.

**Request Body:**
```json
{
  "subscription": {
    "endpoint": "https://fcm.googleapis.com/...",
    "keys": {
      "p256dh": "BJ8...",
      "auth": "k3d..."
    }
  }
}
```

**Response:**
```json
{
  "success": true,
  "message": "Notificações ativadas com sucesso!"
}
```

### POST `/push_unsubscribe`

Remove uma subscrição existente.

**Request Body:**
```json
{
  "endpoint": "https://fcm.googleapis.com/..."
}
```

**Response:**
```json
{
  "success": true,
  "message": "Notificações desativadas"
}
```

### POST `/push_test`

Envia uma notificação de teste ao usuário atual.

**Response:**
```json
{
  "success": true,
  "message": "Notificação de teste enviada para 2 dispositivo(s)"
}
```

---

## 💻 Uso Programático

### Enviar Notificação Personalizada

```python
from app import send_push_notification, PushSubscription

# Buscar subscrições do usuário
subscriptions = PushSubscription.query.filter_by(
    member_id=member_id,
    is_active=True
).all()

# Enviar para todos os dispositivos
for sub in subscriptions:
    send_push_notification(
        subscription_info=sub,
        title='🎵 Novo Repertório Disponível',
        body='O repertório para o culto de domingo foi atualizado',
        data={
            'type': 'novo_repertorio',
            'url': '/repertorio',
            'repertorio_id': 123,
            'requireInteraction': False
        },
        icon='/static/icon-192x192.png',
        badge='/static/icon-72x72.png'
    )
```

### Estrutura do Payload

```python
{
    'type': 'nova_escala',           # Tipo da notificação
    'url': '/minhas_escalas',        # URL de destino ao clicar
    'escala_id': 42,                 # ID do recurso relacionado
    'culto_id': 15,                  # IDs adicionais
    'requireInteraction': True       # Exigir interação do usuário
}
```

### Ações Contextuais

As notificações podem incluir botões de ação:

```python
# nova_escala
actions = [
    {'action': 'view', 'title': 'Ver Escala'},
    {'action': 'confirm', 'title': 'Confirmar Presença'}
]

# lembrete_confirmacao
actions = [
    {'action': 'confirm', 'title': 'Confirmar'},
    {'action': 'deny', 'title': 'Não Poderei'}
]
```

Essas ações são automaticamente adicionadas pela função `send_push_notification()` quando você especifica o `type` apropriado no parâmetro `data`.

---

## 🎯 Eventos Integrados

O sistema já está configurado para enviar notificações nos seguintes eventos:

### 1. Nova Escala Criada

**Quando:** Admin adiciona membro a uma escala  
**Destinatário:** Membro escalado  
**Conteúdo:** "📋 Nova Escala: [Nome do Culto]"  
**Ação:** Navega para `/minhas_escalas`

```python
# Código em app.py (add_escala route)
send_push_notification(
    sub,
    f'📋 Nova Escala: {culto.name}',
    f'Você foi escalado(a) como {role} em {culto_data}',
    {'type': 'nova_escala', 'url': '/minhas_escalas', ...}
)
```

### 2. Novo Aviso Publicado

**Quando:** Admin cria novo aviso  
**Destinatário:** Todos os usuários com notificações ativas  
**Conteúdo:** Depende da prioridade  
- 🚨 Urgent
- ⚠️ High
- 📢 Normal

```python
# Código em app.py (add_aviso route)
send_push_notification(
    sub,
    f'{emoji} {title}',
    message_preview,
    {'type': 'novo_aviso', 'priority': priority, ...}
)
```

### 3. Ausência Confirmada

**Quando:** Membro nega presença em escala  
**Destinatário:** Admins e líderes  
**Conteúdo:** "⚠️ Ausência Confirmada - [Nome do Membro]"  
**Ação:** Navega para `/escalas`

```python
# Código em app.py (negar_presenca route)
send_push_notification(
    sub,
    f'⚠️ Ausência Confirmada - {member.name}',
    f'{member.name} não poderá comparecer...',
    {'type': 'ausencia_confirmada', 'requireInteraction': True, ...}
)
```

---

## 🔒 Segurança

### VAPID Authentication

- **Chave Pública**: Compartilhada com o frontend, identifica o servidor
- **Chave Privada**: Mantida em segredo, assina as mensagens push
- **Claims Email**: Permite que Push Services entrem em contato em caso de problemas

### Criptografia End-to-End

Cada subscrição possui:
- **p256dh**: Chave pública P-256 ECDH para criptografia
- **auth**: Segredo de autenticação para descriptografia

As mensagens são criptografadas pelo navegador antes de enviar ao Push Service e só podem ser descriptografadas pelo destinatário.

### Permissões

- **Navegador**: Usuário deve conceder permissão explícita
- **HTTPS Only**: Push API só funciona em conexões seguras
- **Origem Única**: Subscrições são vinculadas a um domínio específico

---

## 🐛 Troubleshooting

### Notificações não aparecem

1. **Verifique permissões do navegador**
   ```javascript
   console.log(Notification.permission); // Deve ser "granted"
   ```

2. **Verifique Service Worker**
   - Abra DevTools → Application → Service Workers
   - Verifique se está ativo e rodando

3. **Verifique VAPID keys no .env**
   ```bash
   echo $VAPID_PUBLIC_KEY
   echo $VAPID_PRIVATE_KEY
   ```

4. **Verifique logs do servidor**
   - Erros de envio aparecem no console do Flask

### Subscrição não salva

1. **Verifique conexão com banco**
   ```python
   python migrate_add_push_subscription.py
   ```

2. **Verifique autenticação do usuário**
   - User ou Member deve estar logado
   - Session deve conter `user_id` ou `member_id`

### Erro 410 Gone

Este erro indica que o endpoint expirou:
- O sistema automaticamente desativa a subscrição
- Usuário precisa reativar manualmente
- Comum quando dados do navegador são limpos

### Notificação não clicável

Verifique se o Service Worker está registrando cliques:

```javascript
// Em sw.js
self.addEventListener('notificationclick', event => {
    console.log('Notificação clicada:', event);
    // ...
});
```

---

## 📊 Monitoramento

### Verificar Subscrições Ativas

```python
from app import app, db, PushSubscription

with app.app_context():
    total = PushSubscription.query.filter_by(is_active=True).count()
    print(f"Subscrições ativas: {total}")
    
    # Por usuário
    por_usuario = db.session.query(
        PushSubscription.user_id,
        db.func.count(PushSubscription.id)
    ).filter_by(is_active=True).group_by(PushSubscription.user_id).all()
    
    for user_id, count in por_usuario:
        print(f"User {user_id}: {count} dispositivo(s)")
```

### Limpar Subscrições Inativas

```python
from datetime import datetime, timedelta

# Remover subscrições não usadas há mais de 90 dias
limite = datetime.utcnow() - timedelta(days=90)
antigas = PushSubscription.query.filter(
    PushSubscription.last_used < limite
).all()

for sub in antigas:
    db.session.delete(sub)
db.session.commit()
```

---

## 🚀 Próximas Melhorias

### Funcionalidades Planejadas

1. **Agendamento de Notificações**
   - Enviar lembretes automáticos 48h antes do culto
   - Background job com APScheduler ou Celery

2. **Preferências de Notificação**
   - Permitir usuário escolher quais eventos deseja receber
   - Horários de "não perturbe"

3. **Interface Admin**
   - Painel para broadcast de notificações
   - Histórico de notificações enviadas
   - Estatísticas de entrega e cliques

4. **Rich Notifications**
   - Imagens e ícones personalizados
   - Sons customizados por tipo de evento
   - Progresso de download (ex: repertórios)

5. **Multi-idioma**
   - Suporte a notificações em diferentes idiomas

---

## 📚 Recursos Adicionais

### Documentação Oficial

- [Web Push API - MDN](https://developer.mozilla.org/en-US/docs/Web/API/Push_API)
- [Notifications API - MDN](https://developer.mozilla.org/en-US/docs/Web/API/Notifications_API)
- [Service Worker API - MDN](https://developer.mozilla.org/en-US/docs/Web/API/Service_Worker_API)
- [pywebpush - GitHub](https://github.com/web-push-libs/pywebpush)

### Compatibilidade de Navegadores

| Navegador | Desktop | Mobile | Notas |
|-----------|---------|--------|-------|
| Chrome    | ✅      | ✅     | Suporte completo |
| Edge      | ✅      | ✅     | Chromium-based |
| Firefox   | ✅      | ✅     | Suporte completo |
| Safari    | ✅      | ⚠️     | iOS 16.4+ apenas |
| Opera     | ✅      | ✅     | Suporte completo |

⚠️ = Suporte parcial ou com limitações

---

## 🆘 Suporte

Em caso de problemas:

1. Verifique este guia de troubleshooting
2. Consulte os logs do servidor
3. Verifique o console do navegador (F12 → Console)
4. Entre em contato com a administração do sistema

---

**Última atualização:** 17/03/2026  
**Versão do sistema:** 5.0.4  
**Autor:** Sistema de Gerenciamento de Ministério de Louvor
