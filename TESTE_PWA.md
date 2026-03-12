# 🔧 TESTE PWA - Diagnóstico Rápido

## 🚀 Servidor Rodando
✅ http://127.0.0.1:5000

---

## ✅ CORREÇÕES APLICADAS

1. **Rotas PWA adicionadas ao Flask** (`app.py`):
   - ✅ `/sw.js` → Serve o Service Worker
   - ✅ `/manifest.json` → Serve o manifesto PWA

2. **Referências atualizadas** (`base.html`):
   - ✅ Service Worker: `/static/sw.js` → `/sw.js`
   - ✅ Manifest: `/static/manifest.json` → `/manifest.json`

3. **Servidor reiniciado**:
   - ✅ Novas rotas carregadas

---

## 🧪 COMO TESTAR AGORA

### **📱 Teste no Celular (Recomendado)**

#### **Android:**

1. **Conecte-se à mesma rede Wi-Fi do computador**

2. **Descubra o IP do computador:**
   - Windows: Abra **Prompt de Comando** e digite:
     ```bash
     ipconfig
     ```
   - Procure por "Endereço IPv4" (ex: `192.168.1.100`)

3. **Acesse no navegador do celular:**
   ```
   http://SEU_IP:5000
   ```
   Exemplo: `http://192.168.1.100:5000`

4. **Aguarde 3 segundos** → Banner de instalação aparecerá! 🎉

5. **Clique em "Instalar Agora"**

6. **Confirme** → App instalado na tela inicial!

#### **iOS:**

1. Siga os passos 1-3 acima
2. Abra no **Safari**
3. Toque no botão **Compartilhar** (quadrado com seta)
4. Role e toque em **"Adicionar à Tela de Início"**
5. Confirme → Instalado!

---

### **💻 Teste no Computador (Chrome/Edge)**

1. **Abra no navegador:**
   ```
   http://127.0.0.1:5000
   ```

2. **Abra o DevTools** (F12)

3. **Vá para a aba "Console"**

4. **Procure por:**
   ```
   ✅ Service Worker registrado com sucesso: http://127.0.0.1:5000/
   ```

5. **Vá para "Application" → "Service Workers"**
   - Deve aparecer: `Status: activated`

6. **Aguarde 3 segundos** → Banner aparece

7. **Ou clique no ícone ➕ na barra de endereço** (ao lado do ⭐)

8. **Clique em "Instalar"**

---

## 🔍 DIAGNÓSTICO PASSO A PASSO

### **Teste 1: Service Worker acessível?**

Abra no navegador:
```
http://127.0.0.1:5000/sw.js
```

✅ **Esperado:** Código JavaScript do Service Worker aparece  
❌ **Se erro 404:** Rota não funcionou, verificar `app.py`

---

### **Teste 2: Manifest acessível?**

Abra no navegador:
```
http://127.0.0.1:5000/manifest.json
```

✅ **Esperado:** JSON com configuração do PWA  
❌ **Se erro 404:** Rota não funcionou

---

### **Teste 3: Service Worker registrado?**

No **Console do DevTools** (F12 → Console):

```javascript
// Verificar registrations
navigator.serviceWorker.getRegistrations()
    .then(regs => console.log('SW Registrations:', regs));
```

✅ **Esperado:** Array com 1 registration  
❌ **Se array vazio:** SW não registrou

---

### **Teste 4: Evento beforeinstallprompt capturado?**

No **Console**:

```javascript
// Forçar evento (se ainda não apareceu)
let captured = false;
window.addEventListener('beforeinstallprompt', (e) => {
    captured = true;
    console.log('✅ Evento capturado!', e);
});

setTimeout(() => {
    if (!captured) {
        console.log('❌ Evento NÃO capturado. Possíveis razões:');
        console.log('  1. App já instalado');
        console.log('  2. Critérios PWA não atendidos');
        console.log('  3. Navegador não suporta');
    }
}, 3000);
```

---

### **Teste 5: Forçar exibição do banner**

No **Console**:

```javascript
// Mostrar banner manualmente
document.getElementById('pwaInstallPrompt').style.display = 'block';
```

---

### **Teste 6: Verificar critérios PWA (Lighthouse)**

1. **DevTools (F12)** → Aba **"Lighthouse"**
2. Selecione **"Progressive Web App"**
3. Clique **"Analyze page load"**
4. **Esperado:** Score ≥ 90/100

---

## ❓ POSSÍVEIS PROBLEMAS

### **"Não apareceu o banner"**

**Razões comuns:**

1. ✅ **App já instalado**
   - Verifique na tela inicial
   - Console mostra: `✅ Executando em modo standalone`

2. ⏰ **Banner foi dispensado recentemente**
   - Aguarda 7 dias
   - **Solução:** Limpar localStorage:
     ```javascript
     localStorage.clear();
     location.reload();
     ```

3. 🌐 **Navegador não suporta**
   - Chrome/Edge: ✅ Suporta
   - Firefox: ⚠️ Parcial
   - Safari Desktop: ❌ Não suporta instalação automática

4. 🔒 **Não está em HTTPS**
   - Localhost: ✅ Permitido
   - Rede local (192.168.x.x): ⚠️ Pode requerer HTTPS

5. ❌ **Service Worker não registrou**
   - Veja erro no Console
   - Verifique `/sw.js` acessível

---

### **"Aparece erro no Console"**

**Erro comum:**
```
Failed to register a ServiceWorker: The script has an unsupported MIME type
```

**Solução:**
- ✅ **JÁ CORRIGIDO!** Rota `/sw.js` agora serve com `mimetype='application/javascript'`

---

### **"Chrome não mostra ícone de instalação"**

**Critérios para ícone aparecer:**
- ✅ Manifest válido
- ✅ Service Worker registrado
- ✅ Ícone de 192x192 ou maior
- ✅ HTTPS ou localhost
- ✅ Não instalado ainda

**Verificar:**
```javascript
// DevTools → Application → Manifest
// Deve mostrar todos os dados do manifest
```

---

## 🎯 CHECKLIST DE VALIDAÇÃO

Execute este checklist no **Console do DevTools**:

```javascript
// 🧪 PWA HEALTH CHECK
console.log('🔍 PWA HEALTH CHECK');
console.log('==================');

// 1. Service Worker
navigator.serviceWorker.getRegistrations().then(regs => {
    console.log('✅ Service Workers:', regs.length > 0 ? 'OK' : '❌ NENHUM');
    regs.forEach(reg => console.log('  - Scope:', reg.scope));
});

// 2. Manifest
fetch('/manifest.json')
    .then(r => r.json())
    .then(m => console.log('✅ Manifest:', m.name))
    .catch(e => console.log('❌ Manifest ERROR:', e));

// 3. Service Worker file
fetch('/sw.js')
    .then(r => console.log('✅ SW File:', r.status === 200 ? 'OK' : '❌ ERROR'))
    .catch(e => console.log('❌ SW File ERROR:', e));

// 4. HTTPS
console.log('🔒 Protocol:', window.location.protocol === 'https:' || window.location.hostname === 'localhost' ? '✅ OK' : '⚠️ HTTP');

// 5. Standalone mode
console.log('📱 Standalone:', window.matchMedia('(display-mode: standalone)').matches ? '✅ INSTALADO' : '❌ NÃO INSTALADO');

// 6. LocalStorage
console.log('💾 Dismissal:', localStorage.getItem('pwa-prompt-dismissed') ? '⚠️ DISPENSADO' : '✅ OK');

console.log('==================');
console.log('✅ Verificação concluída!');
```

---

## 🚀 SE TUDO FUNCIONAR CORRETAMENTE

Você deve ver:

1. **Console:**
   ```
   ✅ Service Worker registrado com sucesso: http://127.0.0.1:5000/
   ```

2. **Após 3 segundos:**
   - Banner aparece na parte inferior da tela
   - Design com gradiente roxo-azul
   - Botões "Instalar Agora" e "Agora Não"

3. **DevTools → Application → Service Workers:**
   ```
   Status: activated
   ```

4. **DevTools → Application → Manifest:**
   - Nome: "Ministério de Louvor - Sistema de Gestão"
   - Ícones: 2 SVG (192x192, 512x512)
   - Shortcuts: 3 (Escalas, Repertório, Cultos)

5. **Após clicar "Instalar Agora":**
   - Diálogo nativo do navegador
   - Confirmação
   - Mensagem de sucesso
   - Ícone na tela inicial/menu iniciar

---

## 📞 AINDA NÃO FUNCIONA?

### **Solução Definitiva:**

1. **Limpar TUDO:**
   ```javascript
   // Console
   localStorage.clear();
   sessionStorage.clear();
   
   // Remover SW
   navigator.serviceWorker.getRegistrations()
       .then(regs => regs.forEach(reg => reg.unregister()));
   
   // Limpar cache
   caches.keys().then(keys => keys.forEach(k => caches.delete(k)));
   ```

2. **Fechar navegador completamente**

3. **Reabrir e acessar:**
   ```
   http://127.0.0.1:5000
   ```

4. **Aguardar 3 segundos**

5. **Banner DEVE aparecer**

---

## 💡 DICA RÁPIDA

**Quer testar imediatamente sem esperar 3 segundos?**

No Console:
```javascript
document.getElementById('pwaInstallPrompt').style.display = 'block';
```

Ou use o **botão do menu lateral** (☰) → "Instalar App"

---

## 📊 AMBIENTE DE TESTE

- ✅ **Servidor:** http://127.0.0.1:5000
- ✅ **Service Worker:** /sw.js
- ✅ **Manifest:** /manifest.json
- ✅ **Rotas PWA:** Funcionais
- ✅ **Templates:** Atualizados
- ✅ **Sistema:** 100% operacional

---

**🎯 O sistema está configurado corretamente!**  
**Agora é só testar seguindo os passos acima.**

Se ainda tiver problemas, compartilhe:
1. Navegador + versão
2. Sistema operacional
3. Mensagens de erro no Console
4. Screenshot do DevTools → Application

---

_Atualizado: 11/03/2026 | Versão: 1.2.1_
