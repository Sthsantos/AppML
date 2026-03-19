# 🔔 Push Notifications - Início Rápido

Sistema de notificações em tempo real usando Web Push API.

## ⚡ Setup em 4 Passos

### 1. Gerar VAPID Keys
```bash
python gerar_vapid_keys.py
```

### 2. Configurar .env
```bash
VAPID_PUBLIC_KEY=sua-chave-aqui
VAPID_PRIVATE_KEY=sua-chave-aqui
VAPID_CLAIMS_EMAIL=mailto:admin@ministry.com
```

### 3. Instalar Dependência
```bash
pip install pywebpush==1.14.0
```

### 4. Criar Tabela no Banco
```bash
python migrate_add_push_subscription.py
```

## ✅ Pronto!

Acesse `/perfil` no sistema e clique em **"Ativar Notificações"**.

---

## 📡 Eventos com Notificações

- ✅ **Nova Escala** → Membro recebe notificação
- 📢 **Novo Aviso** → Todos os usuários recebem
- ⚠️ **Ausência** → Admins e líderes são notificados

---

## 🔧 Uso Programático

```python
from app import send_push_notification, PushSubscription

# Buscar subscrições
subs = PushSubscription.query.filter_by(member_id=123, is_active=True).all()

# Enviar notificação
for sub in subs:
    send_push_notification(
        sub,
        '🎵 Novo Repertório',
        'Confira as músicas para domingo',
        {'type': 'novo_repertorio', 'url': '/repertorio'}
    )
```

---

## 📖 Documentação Completa

Veja [PUSH_NOTIFICATIONS_GUIDE.md](PUSH_NOTIFICATIONS_GUIDE.md) para:
- Arquitetura detalhada
- API completa
- Troubleshooting
- Segurança
- Melhorias futuras

---

## 🆘 Problemas Comuns

**Notificações não aparecem?**
1. Verifique permissões do navegador
2. Confirme que Service Worker está ativo
3. Valide VAPID keys no .env

**Subscrição não salva?**
1. Execute a migração do banco
2. Verifique se está logado
3. Confirme conexão HTTPS

---

**Versão:** 1.0.0  
**Compatível com:** Chrome, Firefox, Edge, Safari (iOS 16.4+)
