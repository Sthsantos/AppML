# 📱 Instalação PWA - Ministério de Louvor

## 🎯 O que é PWA?

**Progressive Web App (PWA)** permite que você instale o sistema como um aplicativo nativo no seu dispositivo (celular, tablet ou computador) sem precisar de loja de aplicativos (Google Play ou App Store).

## ✨ Vantagens do PWA

✅ **Acesso Rápido** - Ícone na tela inicial, como qualquer app
✅ **Sem Distrações** - Abre em tela cheia, sem barra de navegador
✅ **Modo Offline** - Funciona mesmo sem internet (recursos básicos)
✅ **Rápido** - Cache inteligente para carregamento instantâneo
✅ **Economia de Espaço** - Muito menor que um app tradicional
✅ **Atualizações Automáticas** - Sempre atualizado sem precisar baixar

---

## 📥 Como Instalar

### 🤖 **Android (Chrome, Edge, Samsung Internet)**

#### **Método 1: Prompt Automático**
1. Acesse o sistema pelo navegador
2. Aguarde 3 segundos
3. Aparecerá um **banner na parte inferior** com botão "Instalar Agora"
4. Clique em **"Instalar Agora"**
5. Confirme a instalação
6. ✅ Pronto! O ícone aparecerá na tela inicial

#### **Método 2: Menu do Navegador**
1. Abra o menu (⋮) no canto superior direito
2. Toque em **"Adicionar à tela inicial"** ou **"Instalar app"**
3. Confirme tocando em **"Adicionar"** ou **"Instalar"**
4. ✅ O app está instalado!

#### **Método 3: Botão no Menu Lateral**
1. Abra o **menu lateral** (☰)
2. Role para baixo
3. Clique no botão **"Instalar App"** (com ícone de download)
4. Confirme a instalação
5. ✅ Instalado!

---

### 🍎 **iOS (Safari - iPhone/iPad)**

> **Nota**: No iOS, a instalação é manual pelo Safari. Não há prompt automático.

1. Abra o sistema no **Safari**
2. Toque no botão de **Compartilhar** (quadrado com seta para cima) na barra inferior
3. Role para baixo e toque em **"Adicionar à Tela de Início"**
4. Edite o nome se desejar (padrão: "Min. Louvor")
5. Toque em **"Adicionar"** no canto superior direito
6. ✅ O ícone aparecerá na tela inicial!

**Dica iOS**: Após alguns segundos, pode aparecer uma mensagem explicando o processo.

---

### 💻 **Windows/Mac (Chrome, Edge)**

1. Acesse o sistema pelo navegador
2. Clique no ícone de **instalação** (➕) na barra de endereço
   - Ou aguarde o **banner automático** aparecer
3. Clique em **"Instalar"**
4. ✅ O app será instalado e aparecerá:
   - **Windows**: Menu Iniciar e área de trabalho (opcional)
   - **Mac**: Pasta de Aplicativos e Dock

**Alternativa**: 
- Menu (⋮) → **"Instalar Ministério de Louvor..."**

---

## 🔍 Como Saber se Está Instalado?

✅ **Instalado com sucesso quando:**
- Abre em **tela cheia** (sem barra do navegador)
- Tem **ícone próprio** na tela inicial/menu iniciar
- Nome aparece como **"Min. Louvor"** ou **"Ministério de Louvor - Sistema de Gestão"**
- Console do navegador mostra: `✅ Executando em modo standalone (PWA instalado)`

---

## 🎨 Recursos do PWA

### 🌐 **Cache Inteligente**
- **Primeira visita**: Baixa recursos essenciais
- **Visitas seguintes**: Carregamento instantâneo do cache
- **Offline**: Recursos básicos disponíveis sem internet

### 🔄 **Atualizações Automáticas**
- O Service Worker verifica atualizações automaticamente
- Novas versões são instaladas em segundo plano
- Recarrega automaticamente quando necessário

### 🚀 **Atalhos Rápidos** (Android/Windows)
Pressione e segure o ícone do app para ver:
- **Escalas** - Acesso direto às escalas de louvor
- **Repertório** - Visualizar músicas cadastradas
- **Cultos** - Agenda de cultos

### 📊 **Informações Técnicas**
- **Nome Completo**: Ministério de Louvor - Sistema de Gestão
- **Nome Curto**: Min. Louvor
- **Cores do Tema**: Roxo (#667eea) e gradiente
- **Versão do Cache**: v1.2.0
- **Ícones**: SVG responsivo (192x192 e 512x512)

---

## 🛠️ Gerenciar/Desinstalar

### **Android**
1. Pressione e segure o ícone do app
2. Toque em **"Informações do app"** ou **"Desinstalar"**
3. Confirme a remoção

**Ou via Configurações**:
- Configurações → Apps → Ministério de Louvor → Desinstalar

### **iOS**
1. Pressione e segure o ícone
2. Toque em **"Remover App"**
3. Confirme **"Excluir App"**

### **Windows**
1. Menu Iniciar → Clique com botão direito no app
2. Selecione **"Desinstalar"**

**Ou via Chrome**:
- Menu (⋮) → Mais ferramentas → Aplicativos instalados → Desinstalar

### **Mac**
1. Arraste o app para a **Lixeira**
2. Ou: Finder → Aplicativos → Mover para Lixeira

---

## 🐛 Solução de Problemas

### ❓ **Não aparece opção de instalar**

**Possíveis causas:**
1. **Já está instalado** - Verifique se o ícone já está na tela inicial
2. **Navegador não suporta** - Use Chrome, Edge ou Safari (iOS)
3. **Não está em HTTPS** - PWA requer conexão segura (ou localhost)
4. **Já foi dispensado** - Aguarde 7 dias ou limpe o cache do navegador

**Solução**:
- Limpe o cache: Configurações → Privacidade → Limpar dados de navegação
- Ou use o **botão "Instalar App"** no menu lateral

---

### ❓ **App instalado mas não abre**

**Soluções**:
1. Desinstale e reinstale o app
2. Limpe o cache e dados do app
3. Verifique se o servidor está rodando
4. Reinstale usando o navegador

---

### ❓ **Conteúdo desatualizado após instalação**

**Solução**:
1. Feche completamente o app (não apenas minimize)
2. Abra novamente
3. O Service Worker atualizará automaticamente
4. Se persistir: Desinstale, limpe cache do navegador, reinstale

---

### ❓ **iOS não mostra ícone personalizado**

**Explicação**: 
- iOS usa captura de tela da página ao invés do ícone do manifest
- Isso é normal no Safari/iOS

**Solução alternativa**:
- Abra a página inicial antes de adicionar à tela inicial
- O iOS capturará essa tela como ícone

---

## 📞 Suporte

**Problemas técnicos?**
- Verifique o console do navegador (F12)
- Procure por mensagens do Service Worker
- Mensagem esperada: `✅ Service Worker registrado com sucesso`

**Recursos úteis:**
- [Teste de PWA](https://web.dev/measure/)
- [Lighthouse](https://developers.google.com/web/tools/lighthouse) - Auditoria PWA

---

## 📝 Observações Importantes

⚠️ **Requisitos Mínimos**:
- Navegador moderno (Chrome 80+, Safari 11.3+, Edge 79+)
- Conexão HTTPS (ou localhost para desenvolvimento)
- JavaScript ativado

💡 **Dicas**:
- O prompt automático aparece **3 segundos** após carregar a página
- Se dispensar, ele volta a aparecer após **7 dias**
- O botão "Instalar App" no menu **sempre está disponível** (quando aplicável)
- Em modo standalone, não há barra de navegador

🎯 **Experiência Ideal**:
- Instale no celular para acesso rápido às escalas
- Use atalhos rápidos para funções específicas
- Funciona offline para consultas básicas
- Atualizações automáticas sem esforço

---

**Desenvolvido com ❤️ para o Ministério de Louvor**

_Última atualização: Março 2026 | Versão PWA: 1.2.0_
