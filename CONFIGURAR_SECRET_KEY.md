# Configurar SECRET_KEY no Render

## ⚠️ Problema: Logout Automático Após Deploy

Se você está sendo deslogado toda vez que faz deploy no Render, é porque a `SECRET_KEY` está sendo regenerada a cada deploy, invalidando os cookies de sessão.

## ✅ Solução: Configurar SECRET_KEY Permanente

### Passo 1: Gerar uma SECRET_KEY

Execute no terminal (local ou no Render):

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Copie a chave gerada (exemplo: `a1b2c3d4e5f6...`)

### Passo 2: Adicionar no Render

1. Acesse o **Dashboard do Render**
2. Vá em seu serviço **AppML**
3. Clique em **Environment**
4. Clique em **Add Environment Variable**
5. Configure:
   - **Key**: `SECRET_KEY`
   - **Value**: Cole a chave gerada no Passo 1
6. Clique em **Save Changes**

### Passo 3: Fazer Deploy

O Render vai reiniciar automaticamente com a nova variável. A partir de agora:

✅ **Você NÃO será mais deslogado após deploys**  
✅ **Sessões persistem por 30 dias**  
✅ **Cookie "lembrar-me" funciona corretamente**

## 🔐 Segurança

- ✅ Chave está protegida nas variáveis de ambiente do Render
- ✅ Não é versionada no Git (`.gitignore`)
- ✅ Única por aplicação

## 📝 Sistema de Fallback

O sistema possui fallback automático:

1. **Prioridade 1**: Usa `SECRET_KEY` da variável de ambiente
2. **Prioridade 2**: Carrega de `instance/secret_key.txt` (se existir)
3. **Prioridade 3**: Gera nova e salva em `instance/secret_key.txt`

**⚠️ IMPORTANTE**: O fallback (prioridades 2 e 3) funciona apenas entre **restarts**, não entre **deploys** (porque o Render cria novo contêiner a cada deploy).

## 🎯 Recomendação Final

**Configure a SECRET_KEY no Render como variável de ambiente** para garantir persistência completa entre deploys.
