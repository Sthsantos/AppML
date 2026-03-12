# 🚀 Como Enviar para o GitHub

## Passo 1: Criar Repositório no GitHub

1. Acesse https://github.com
2. Faça login na sua conta
3. Clique no botão "+" no canto superior direito
4. Selecione "New repository"
5. Configure:
   - Nome: `ministerio-louvor-app` (ou nome de sua preferência)
   - Descrição: "Sistema de gerenciamento de ministério de louvor"
   - Visibilidade: Private (recomendado) ou Public
   - **NÃO** marque "Initialize this repository with a README"
6. Clique em "Create repository"

## Passo 2: Conectar seu Repositório Local ao GitHub

Após criar o repositório, o GitHub mostrará instruções. Use os comandos abaixo:

```bash
# Substitua SEU-USUARIO e SEU-REPOSITORIO pelos valores corretos
git remote add origin https://github.com/SEU-USUARIO/SEU-REPOSITORIO.git
```

Exemplo:
```bash
git remote add origin https://github.com/joao/ministerio-louvor-app.git
```

## Passo 3: Configurar Credenciais Git (se necessário)

Se for a primeira vez usando Git:

```bash
git config --global user.name "Seu Nome"
git config --global user.email "seu-email@exemplo.com"
```

## Passo 4: Enviar o Código para o GitHub

```bash
# Enviar o código para o GitHub
git push -u origin master
```

OU, se seu repositório usa "main" como branch principal:

```bash
git branch -M main
git push -u origin main
```

## Passo 5: Verificar no GitHub

1. Acesse seu repositório no GitHub
2. Verifique se todos os arquivos foram enviados
3. Seu código está agora no GitHub! 🎉

## 📋 Comandos Úteis para o Futuro

### Fazer alterações e enviar para o GitHub:

```bash
# 1. Adicionar arquivos modificados
git add .

# 2. Fazer commit com mensagem descritiva
git commit -m "Descrição das alterações"

# 3. Enviar para o GitHub
git push
```

## 🔐 Autenticação

Se o GitHub pedir autenticação:

1. **Token de Acesso Pessoal** (recomendado):
   - Acesse: https://github.com/settings/tokens
   - Gere um novo token com permissões de "repo"
   - Use o token como senha ao fazer push

2. **SSH** (alternativa):
   - Configure chaves SSH: https://docs.github.com/pt/authentication/connecting-to-github-with-ssh

## ⚠️ IMPORTANTE

**NÃO** envie para o GitHub:
- Arquivo `.env` (já está no .gitignore) ✅
- Pasta `instance/` com o banco de dados (já está no .gitignore) ✅
- Senhas ou informações sensíveis

Todos esses arquivos já estão protegidos pelo `.gitignore` que criamos!

## 🌐 Próximos Passos - Deploy

Após enviar para o GitHub, você pode fazer deploy em:

1. **Heroku** (mais fácil)
2. **Render** (gratuito)
3. **PythonAnywhere** (gratuito para começar)
4. **Railway**
5. **Fly.io**

Consulte o arquivo `README.md` para instruções detalhadas de deploy!
