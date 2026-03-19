# 🎵 Sistema de Gerenciamento de Ministério de Louvor - Guia Rápido de Persistência

## ⚡ Configure a Persistência de Arquivos de Áudio em 3 Passos

### 📌 Por que isso é importante?
Por padrão, arquivos salvos no Render são **deletados a cada novo deploy**. Para manter seus áudios permanentemente, siga este guia.

---

## 🚀 Passo 1: Criar Render Disk

1. Acesse: https://dashboard.render.com/
2. Selecione seu **Web Service** (AppML)
3. Vá na aba **"Disks"**
4. Clique **"Add Disk"**
5. Configure:
   ```
   Name: audio-uploads
   Mount Path: /var/data/uploads
   Size: 1 GB
   ```
6. Clique **"Save Disk"**

**Custo**: $0.25/mês por GB

---

## 🔧 Passo 2: Adicionar Variável de Ambiente

1. No Render Dashboard, vá em **"Environment"**
2. Adicione:
   ```
   Key: PERSISTENT_UPLOAD_FOLDER
   Value: /var/data/uploads
   ```
3. Clique **"Save Changes"**
4. Aguarde o **redeploy automático**

---

## ✅ Passo 3: Verificar

1. Acesse os **Logs** do Render
2. Procure pela mensagem:
   ```
   ✅ Usando pasta persistente para uploads: /var/data/uploads
   ```
3. Faça upload de um áudio de teste
4. Faça um novo deploy (commit no GitHub)
5. Verifique se o áudio ainda está disponível

---

## 🎯 Pronto!

Seus arquivos de áudio agora **persistirão entre deploys**! 🎉

Para mais detalhes, consulte: [PERSISTENCIA_ARQUIVOS.md](PERSISTENCIA_ARQUIVOS.md)

---

## 🆘 Problemas?

**Arquivos ainda somem?**
- Verifique se a variável `PERSISTENT_UPLOAD_FOLDER` está configurada
- Certifique-se que o Disk está montado em `/var/data/uploads`

**Erro de permissão?**
```bash
# No Render Shell:
mkdir -p /var/data/uploads
chmod 755 /var/data/uploads
```

---

**Sistema desenvolvido em**: Março de 2026  
**Versão**: 5.0  
**Status da Persistência**: ✅ Implementado e pronto para uso
