# Configuração WhatsApp Business Cloud API

## 📱 Visão Geral

O sistema agora envia notificações via **Push Notification** E **WhatsApp** simultaneamente para:
- ✅ Novas escalas
- ✅ Solicitações de substituição
- ✅ Aceitação/recusa de substituições
- ✅ Avisos gerais (futuro)

---

## 🔧 Configuração Passo a Passo

### **1. Criar App no Meta for Developers**

1. Acesse: https://developers.facebook.com/
2. Clique em **"Meus Apps"** → **"Criar App"**
3. Escolha tipo: **"Outro"** → **"Empresa"**
4. Nome do app: `Ministério Louvor Notificações` (ou qualquer nome)
5. Email de contato e conta comercial

### **2. Adicionar Produto WhatsApp**

1. No painel do app, clique em **"Adicionar Produto"**
2. Selecione **"WhatsApp"** → **"Configurar"**
3. Você será redirecionado para o WhatsApp Manager

### **3. Obter Credenciais**

#### **Token de Acesso (Access Token)**
1. No painel WhatsApp, vá em **"Configuração"** → **"Início Rápido"**
2. Copie o **"Token de acesso temporário"** (válido por 24h)
3. Para token permanente:
   - Vá em **"Configurações"** → **"Tokens de sistema"**
   - Gere um token de **"Acesso de Sistema"** (nunca expira)
   - ⚠️ **IMPORTANTE**: Guarde em local seguro, só aparece uma vez!

#### **Phone Number ID**
1. No mesmo painel, localize **"Phone Number ID"**
2. Copie o ID (formato: `109812345678901`)
3. Este é o número de teste fornecido pelo Meta

### **4. Verificar Número de Telefone**

Para enviar mensagens para números reais, você precisa:
1. Adicionar seus números à **"Lista de Números de Teste"**:
   - WhatsApp Manager → **"Configuração"** → **"Para"**
   - Clique em **"Gerenciar lista de números de telefone"**
   - Adicione números (máximo 5 na versão teste)
   - Cada número receberá um código via WhatsApp para confirmar

OU (para produção):
1. Verificar numero comercial oficial
2. Passar por revisão do app (Business Verification)
3. Limite aumenta para milhares de mensagens/dia

---

## 🔑 Configurar Variáveis de Ambiente

### **Opção 1: Arquivo `.env` (Local)**

Edite o arquivo `.env` e adicione:

```env
# WhatsApp Business Cloud API
WHATSAPP_TOKEN=EAAxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
WHATSAPP_PHONE_ID=109812345678901
```

### **Opção 2: Render Dashboard (Produção)**

1. Acesse seu serviço no Render
2. Vá em **"Environment"** → **"Environment Variables"**
3. Adicione:
   - **Key**: `WHATSAPP_TOKEN`
   - **Value**: Seu token de acesso
   - Clique em **"Add"**
4. Repita para:
   - **Key**: `WHATSAPP_PHONE_ID`
   - **Value**: Seu Phone Number ID
5. Clique em **"Save Changes"**
6. O Render fará redeploy automático

---

## 🧪 Testar Integração

### **1. Teste Local**

```bash
# Ative o ambiente virtual
.\.venv\Scripts\Activate.ps1

# Execute o app
python app.py
```

### **2. Criar uma Escala de Teste**

1. Faça login como admin
2. Vá em **Escalas** → **Criar Nova Escala**
3. Selecione um membro que tenha telefone cadastrado
4. Crie a escala
5. **Verifique**:
   - ✅ Push notification enviada
   - ✅ Mensagem no WhatsApp recebida

### **3. Logs de Debug**

No console, você verá:

```
🚀 [PUSH] Iniciando envio de notificação...
   ✅ Resposta: Status 201

📱 [WHATSAPP] Enviando mensagem...
   📞 Para: 5511987654321
   ✅ WhatsApp enviado com sucesso! ID: wamid.xxxxx
```

---

## 📋 Requisitos de Número de Telefone

### **Formato Aceito no Cadastro**
O sistema aceita qualquer formato e normaliza automaticamente:

```
(11) 98765-4321  → 5511987654321
11 98765-4321    → 5511987654321
+55 11 98765-4321 → 5511987654321
5511987654321    → 5511987654321
```

### **Importante**
- ✅ Números brasileiros devem ter 11 dígitos (DDD + 9 dígitos)
- ✅ O sistema adiciona automaticamente o código +55 (Brasil)
- ❌ Membros sem telefone cadastrado **não** receberão WhatsApp (apenas push)

---

## 🚀 Limites e Custos

### **Modo Teste (Grátis)**
- ✅ 5 números permitidos
- ✅ Até 1.000 conversas/mês grátis
- ✅ Funciona perfeitamente para ministérios pequenos

### **Modo Produção**
- 💰 Após verificação de negócio
- 💰 1.000 primeiras conversas/mês: GRÁTIS
- 💰 Após isso: ~$0,005 - $0,09 por mensagem (varia por país)
- 📊 Para 100 membros com 4 notificações/mês: ~400 mensagens = **GRÁTIS**

**Conclusão**: Para ministérios, quase sempre fica dentro do limite gratuito! 🎉

---

## ❓ Troubleshooting

### **Erro: "WhatsApp API não configurada"**
- Verifique se `WHATSAPP_TOKEN` e `WHATSAPP_PHONE_ID` estão definidos
- No Render, veja se as variáveis foram salvas corretamente

### **Erro: "Número de telefone inválido"**
- Membro não tem telefone cadastrado no sistema
- Edite o perfil do membro e adicione telefone

### **Erro: 401 Unauthorized**
- Token expirado ou inválido
- Gere novo token no Meta for Developers

### **Erro: 403 Forbidden**
- Número destinatário não está na lista de teste
- Adicione o número no WhatsApp Manager → Núme

ros de Teste

### **Mensagens não chegam**
- ✅ Verifique se o número confirmou o código de teste
- ✅ Logs mostram "enviado com sucesso"? Se sim, problema no WhatsApp
- ✅ Tente remover e adicionar novamente à lista de teste

---

## 📚 Documentação Oficial

- [WhatsApp Business Platform](https://developers.facebook.com/docs/whatsapp/cloud-api)
- [Guia de Início Rápido](https://developers.facebook.com/docs/whatsapp/cloud-api/get-started)
- [Criar Token Permanente](https://developers.facebook.com/docs/whatsapp/business-management-api/get-started#1--acquire-an-access-token-using-a-system-user-or-facebook-login)

---

## ✅ Checklist de Configuração

- [ ] App criado no Meta for Developers
- [ ] WhatsApp adicionado como produto
- [ ] Token de acesso gerado (temporário ou permanente)
- [ ] Phone Number ID copiado
- [ ] Números de teste adicionados e confirmados
- [ ] Variáveis `WHATSAPP_TOKEN` e `WHATSAPP_PHONE_ID` configuradas
- [ ] Teste enviado com sucesso
- [ ] Deploy realizado no Render com variáveis configuradas

---

**Status**: ✅ Integração pronta e funcional!
**Próximo passo**: Configurar suas credenciais e testar! 🚀
