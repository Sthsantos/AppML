# Sistema de Gerenciamento de Ministério de Louvor

Sistema web completo para gerenciamento de escalas, repertório, membros e cultos do ministério de louvor.

## 🚀 Funcionalidades

- ✅ Gerenciamento de membros e usuários
- ✅ Sistema de escalas automáticas
- ✅ Gestão de repertório com uploads de áudio
- ✅ Controle de cultos e eventos
- ✅ Sistema de indisponibilidades
- ✅ Dashboard com estatísticas
- ✅ Sistema de feedback
- ✅ PWA (Progressive Web App) - Instalável em dispositivos móveis
- ✅ Autenticação e autorização
- ✅ Notificações e avisos

## 📋 Pré-requisitos

- Python 3.11+
- pip (gerenciador de pacotes Python)

## 🔧 Instalação Local

1. Clone o repositório:
```bash
git clone <seu-repositorio-url>
cd APP ML
```

2. Crie um ambiente virtual:
```bash
python -m venv venv
```

3. Ative o ambiente virtual:
- Windows:
```bash
venv\Scripts\activate
```
- Linux/Mac:
```bash
source venv/bin/activate
```

4. Instale as dependências:
```bash
pip install -r requirements.txt
```

5. Configure as variáveis de ambiente:
- Copie o arquivo `.env.example` para `.env`
- Edite o arquivo `.env` e configure suas variáveis

6. Execute a aplicação:
```bash
python app.py
```

7. Acesse no navegador:
```
http://localhost:5000
```

## 🌐 Deploy para Produção

### Heroku

1. Crie uma conta no [Heroku](https://heroku.com)

2. Instale o Heroku CLI

3. Faça login no Heroku:
```bash
heroku login
```

4. Crie uma aplicação:
```bash
heroku create nome-da-sua-app
```

5. Configure as variáveis de ambiente:
```bash
heroku config:set SECRET_KEY=sua-chave-secreta-aqui
heroku config:set FLASK_ENV=production
```

6. Faça o deploy:
```bash
git push heroku master
```

7. Abra a aplicação:
```bash
heroku open
```

### Render

1. Crie uma conta no [Render](https://render.com)

2. Conecte seu repositório GitHub

3. Crie um novo Web Service

4. Configure:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app`

5. Adicione variáveis de ambiente:
   - `SECRET_KEY`: sua chave secreta
   - `FLASK_ENV`: production

### PythonAnywhere

1. Crie uma conta no [PythonAnywhere](https://www.pythonanywhere.com)

2. Clone o repositório no console

3. Configure o WSGI file

4. Instale as dependências

5. Recarregue a aplicação

## 🔐 Configurações de Segurança

⚠️ **IMPORTANTE**: Antes do deploy em produção:

1. Altere a `SECRET_KEY` no arquivo `.env` para uma chave forte e única
2. Configure `FLASK_ENV=production`
3. Use um banco de dados PostgreSQL ou MySQL em produção (não SQLite)
4. Configure HTTPS/SSL
5. Revise as configurações de CORS se necessário

## 📱 PWA - Progressive Web App

O sistema pode ser instalado como aplicativo em dispositivos móveis:

1. Acesse o site pelo navegador móvel
2. Clique em "Adicionar à tela inicial" ou "Instalar"
3. O app estará disponível como um aplicativo nativo

## 🗄️ Banco de Dados

Por padrão, usa SQLite para desenvolvimento. Para produção, recomenda-se PostgreSQL:

```bash
# No Heroku, adicione o addon PostgreSQL:
heroku addons:create heroku-postgresql:hobby-dev

# A variável DATABASE_URL será configurada automaticamente
```

## 👤 Usuário Padrão

- **Email**: admin@ministry.com
- **Senha**: admin123

⚠️ **Altere essas credenciais após o primeiro login!**

## 📁 Estrutura do Projeto

```
APP ML/
├── app.py                 # Aplicação principal Flask
├── requirements.txt       # Dependências Python
├── Procfile              # Configuração Heroku
├── runtime.txt           # Versão Python
├── .env.example          # Exemplo de variáveis de ambiente
├── static/               # Arquivos estáticos (CSS, JS, uploads)
├── templates/            # Templates HTML
└── instance/             # Banco de dados (não commitado)
```

## 🛠️ Tecnologias Utilizadas

- **Backend**: Flask (Python)
- **Banco de Dados**: SQLite (dev) / PostgreSQL (prod)
- **Frontend**: HTML, CSS, JavaScript
- **Autenticação**: Flask-Login
- **ORM**: SQLAlchemy
- **Servidor**: Gunicorn

## 📝 Licença

Projeto privado - Todos os direitos reservados

## 🤝 Suporte

Para dúvidas ou problemas, entre em contato com o administrador do sistema.

---

Desenvolvido com ❤️ para o Ministério de Louvor
