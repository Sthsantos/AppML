# Sistema de Indisponibilidade - Melhorias Implementadas

## 📋 Visão Geral

O sistema de indisponibilidade foi completamente aprimorado para oferecer mais flexibilidade e controle tanto para membros quanto para administradores.

---

## ✨ Novas Funcionalidades

### 1️⃣ **Seleção Flexível de Indisponibilidade**

Os membros agora podem registrar indisponibilidade de **DUAS FORMAS**:

#### **Opção A: Cultos Específicos** (modo anterior mantido)
- Selecione um ou mais cultos específicos da lista
- Útil quando você sabe exatamente quais cultos não poderá participar

#### **Opção B: Período de Datas** ✨ **NOVO**
- Selecione uma data de início e uma data de fim
- O sistema identificará **automaticamente** todos os cultos nesse período
- Útil para viagens, férias ou períodos prolongados de ausência

**Como usar:**
1. Acesse a página [Indisponibilidade](https://appml-tbcw.onrender.com/indisponibilidade)
2. Clique em "Nova Indisponibilidade"
3. Escolha o tipo: **Cultos Específicos** ou **Período de Datas**
4. Preencha os dados e o motivo
5. Clique em "Registrar"

---

### 2️⃣ **Sistema de Solicitação de Exceção** ✨ **NOVO**

#### **Como funciona:**

##### **Para Administradores:**
Quando tentar escalar um membro que está indisponível:

1. O sistema detecta a indisponibilidade
2. Exibe o motivo do membro
3. Oferece a opção: **"Deseja solicitar uma EXCEÇÃO?"**
4. Admin informa o motivo da solicitação
5. Membro recebe a solicitação na página de indisponibilidade

##### **Para Membros:**
Quando recebe uma solicitação especial:

1. A solicitação aparece destacada na página [Indisponibilidade](https://appml-tbcw.onrender.com/indisponibilidade)
2. Vê o culto, data, hora e motivo do admin
3. Pode **AUTORIZAR** ou **RECUSAR**
4. Se autorizar: **é escalado automaticamente**
5. Se recusar: admin é notificado

**Interface visual:**
- Cards destacados em amarelo/laranja para solicitações pendentes
- Botões claros: "Autorizar" (verde) e "Recusar" (cinza)
- Informações completas do culto e motivo do admin

---

### 3️⃣ **Validação Aprimorada** ✨ **MELHORADO**

#### **Bloqueio Automático:**
- Admin **NÃO PODE** escalar membro indisponível diretamente
- Sistema verifica indisponibilidades com status `approved` ou `pending`
- Única exceção: através do sistema de **Solicitação de Exceção**

#### **Verificações incluem:**
- ✅ Indisponibilidade aprovada
- ✅ Indisponibilidade pendente
- ✅ Culto específico marcado
- ✅ Período de datas que inclui o culto

---

## 🗄️ **Estrutura do Banco de Dados**

### **Nova Tabela: `SolicitacaoExcecao`**

```python
- id: Identificador único
- admin_id: Quem solicitou
- member_id: Membro solicitado
- culto_id: Culto em questão
- indisponibilidade_id: Referência à indisponibilidade original
- motivo_solicitacao: Por que o admin precisa escalar
- status: 'pending', 'approved', 'rejected'
- resposta_membro: Resposta opcional do membro
- created_at: Data da solicitação
- respondido_em: Data da resposta
```

### **Modelo `Indisponibilidade` Atualizado**

```python
- status padrão alterado: 'pending' → 'approved'
  (indisponibilidades são auto-aprovadas ao criar)
```

---

## 🔌 **Novas Rotas da API**

### **Para Administradores:**
- `POST /solicitar_excecao` - Solicitar exceção para membro indisponível
- `GET /get_solicitacoes_excecao_admin` - Ver todas as solicitações

### **Para Membros:**
- `GET /get_minhas_solicitacoes_excecao` - Ver solicitações recebidas
- `POST /responder_solicitacao_excecao/<id>` - Aprovar/Rejeitar solicitação

### **Atualizada:**
- `POST /add_indisponibilidade` - Agora aceita período de datas
- `POST /add_escala` - Retorna dados detalhados se membro indisponível

---

## 📱 **Interface do Usuário**

### **Página de Indisponibilidade:**

#### **Seção 1: Solicitações Especiais** (se houver)
- Cards destacados em amarelo
- Informações do admin e do culto
- Botões de Autorizar/Recusar

#### **Seção 2: Minhas Indisponibilidades**
- Lista de todas as indisponibilidades registradas
- Indica culto, data, motivo
- Permite remover (se período aberto)

### **Modal de Nova Indisponibilidade:**

#### **Seletor de Tipo:**
- 🔘 Cultos Específicos (lista de checkboxes)
- 🔘 Período de Datas (campos data início/fim)

#### **Campo Motivo:**
- Obrigatório em ambos os modos

---

## 🚀 **Fluxo de Uso Completo**

### **Cenário 1: Membro registra indisponibilidade por período**

```
1. Membro acessa /indisponibilidade
2. Clica "Nova Indisponibilidade"
3. Seleciona "Período de Datas"
4. Escolhe: 01/04/2026 a 15/04/2026
5. Informa motivo: "Viagem a trabalho"
6. Clica "Registrar"
7. Sistema identifica 3 cultos nesse período
8. Cria 3 indisponibilidades (uma para cada culto)
```

### **Cenário 2: Admin tenta escalar membro indisponível**

```
1. Admin acessa /escalas
2. Tenta adicionar João no culto de 05/04/2026
3. Sistema detecta indisponibilidade
4. Mostra: "João está INDISPONÍVEL - Viagem a trabalho"
5. Admin clica "Solicitar Exceção"
6. Informa motivo: "Precisamos urgentemente de guitarrista"
7. Solicitação enviada para João
```

### **Cenário 3: Membro responde solicitação**

```
1. João acessa /indisponibilidade
2. Vê card destacado: "AGUARDANDO SUA RESPOSTA"
3. Lê motivo do admin
4. Decide AUTORIZAR
5. Sistema cria escala automaticamente
6. João aparece escalado para o culto
```

---

## 🎨 **Melhorias Visuais**

- ✅ Cards coloridos para diferentes status
- ✅ Ícones descritivos (fas fa-user-clock, fas fa-exclamation-circle)
- ✅ Badges de status (Pendente, Aprovado, Recusado)
- ✅ Alerts informativos (amarelo para avisos, azul para info)
- ✅ Botões com cores semânticas (verde=aprovar, vermelho=recusar)

---

## ⚙️ **Configurações**

### **Controle de Período:**
- Admin pode abrir/fechar período de registro via painel
- Membros só podem criar indisponibilidades quando período aberto
- Admin pode criar a qualquer momento

### **Validações:**
- Data fim ≥ Data início
- Cultos futuros apenas
- Motivo obrigatório
- Verificação de duplicatas

---

## 📊 **Benefícios**

### **Para Membros:**
- ✅ Mais flexibilidade (período vs cultos específicos)
- ✅ Transparência (vê solicitações do admin)
- ✅ Controle (pode autorizar ou recusar)

### **Para Administradores:**
- ✅ Respeita indisponibilidades automaticamente
- ✅ Pode solicitar exceções justificadas
- ✅ Rastreabilidade (histórico de solicitações)

### **Para o Sistema:**
- ✅ Integridade de dados
- ✅ Auditoria completa
- ✅ Reduz conflitos humanos

---

## 🔐 **Segurança e Permissões**

- ✅ Apenas admin pode solicitar exceções
- ✅ Apenas o membro pode responder sua própria solicitação
- ✅ Validações de ownership
- ✅ Logs de todas as operações

---

## 📝 **Notas Importantes**

1. **Indisponibilidades são aprovadas automaticamente** ao criar (não precisam aprovação do admin)
2. **Período de datas identifica cultos automaticamente** - não é preciso selecionar manualmente
3. **Solicitações de exceção criam escala automaticamente** se membro aprovar
4. **Service Worker atualizado** (v5.0.2) para forçar cache refresh

---

## 🐛 **Troubleshooting**

### **Problema: Não consigo criar indisponibilidade**
- ✅ Verifique se o período está aberto (banner no topo da página)
- ✅ Certifique-se de preencher o motivo
- ✅ Escolha pelo menos um culto OU um período válido

### **Problema: Solicitação não aparece**
- ✅ Recarregue a página (Ctrl+F5)
- ✅ Verifique se você é o membro solicitado
- ✅ Confirme que a solicitação está pendente

### **Problema: Não consigo escalar membro**
- ✅ Verifique se o membro está indisponível
- ✅ Use a opção "Solicitar Exceção"
- ✅ Aguarde resposta do membro

---

## 📞 **Suporte**

Em caso de dúvidas ou problemas, entre em contato com o administrador do sistema.

**Deploy atual:** https://appml-tbcw.onrender.com
**Versão:** 5.0.2
**Data:** 17/03/2026

---

✅ **Sistema implementado e em produção!**
