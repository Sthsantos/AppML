from flask import Flask, render_template, jsonify, request, redirect, url_for, session, flash, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_required, login_user, logout_user, current_user
from datetime import datetime, date, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from sqlalchemy.orm import aliased  # Para criar aliases nas queries
import secrets
import os
import json
from functools import wraps  # Importando wraps para decoradores
from dotenv import load_dotenv
from pywebpush import webpush, WebPushException
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
from py_vapid import Vapid

# Carrega variaveis de ambiente do arquivo .env
load_dotenv()

# Configurações VAPID para Push Notifications  
VAPID_PUBLIC_KEY = os.environ.get('VAPID_PUBLIC_KEY')
VAPID_PRIVATE_KEY_FILE = 'vapid_private.pem'  # Usar arquivo PEM direto que já existe

# Verificar se arquivo existe e usar
if os.path.exists(VAPID_PRIVATE_KEY_FILE):
    VAPID_PRIVATE_KEY = VAPID_PRIVATE_KEY_FILE
    print(f"✅ Usando VAPID key file: {VAPID_PRIVATE_KEY_FILE}")
else:
    # Fallback: tentar criar do .env
    VAPID_PRIVATE_KEY_RAW = os.environ.get('VAPID_PRIVATE_KEY')
    if VAPID_PRIVATE_KEY_RAW:
        if '\\n' in VAPID_PRIVATE_KEY_RAW:
            VAPID_PRIVATE_KEY_RAW = VAPID_PRIVATE_KEY_RAW.replace('\\n', '\n')
        VAPID_PRIVATE_KEY_RAW = VAPID_PRIVATE_KEY_RAW.strip()
        
        # Salvar em arquivo
        key_file = 'instance/vapid_private.pem'
        try:
            os.makedirs('instance', exist_ok=True)
            with open(key_file, 'w') as f:
                f.write(VAPID_PRIVATE_KEY_RAW)
            VAPID_PRIVATE_KEY = key_file
            print(f"✅ VAPID key salva em: {key_file}")
        except Exception as e:
            print(f"⚠️ Erro ao salvar VAPID key: {e}")
            VAPID_PRIVATE_KEY = VAPID_PRIVATE_KEY_RAW
    else:
        print("⚠️ VAPID_PRIVATE_KEY não encontrada!")
        VAPID_PRIVATE_KEY = None
    
VAPID_CLAIMS_EMAIL = os.environ.get('VAPID_CLAIMS_EMAIL', 'mailto:admin@ministry.com')

def convert_pem_to_der(pem_key_str):
    """
    Converte chave privada PEM para DER (necessário porque py_vapid não reconhece PEM)
    
    Args:
        pem_key_str: String com chave PEM (com \\n ou newlines reais)
    
    Returns:
        bytes: Chave privada em formato DER
    """
    try:
        # Se for string, converter para bytes
        if isinstance(pem_key_str, str):
            pem_bytes = pem_key_str.encode('utf-8')
        else:
            pem_bytes = pem_key_str
            
        # Carregar chave PEM
        private_key = serialization.load_pem_private_key(
            pem_bytes,
            password=None,
            backend=default_backend()
        )
        
        # Converter para DER
        der_data = private_key.private_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        return der_data
    except Exception as e:
        print(f"❌ Erro ao converter PEM para DER: {e}")
        raise

# ========================================
# CONSTANTES DE NIVEIS DE PERMISSAO
# ========================================
ROLE_ADMIN = 'admin'  # Desenvolvedor - Acesso total ao sistema
ROLE_PASTOR = 'pastor'  # Pastor - Acesso pleno
ROLE_LIDER_BANDA = 'lider_banda'  # Lider de Banda - Acesso pleno (escalas de instrumentos)
ROLE_LIDER_MINISTERIO = 'lider_ministerio'  # Lider de Ministerio - Acesso pleno (escalas de ministros/back vocal)
ROLE_MINISTRO = 'ministro'  # Ministro de Louvor - Gerencia musicas das proprias escalas
ROLE_MEMBRO = 'membro'  # Membro comum - Acesso limitado

# Roles com acesso administrativo pleno
ADMIN_ROLES = [ROLE_ADMIN, ROLE_PASTOR, ROLE_LIDER_BANDA, ROLE_LIDER_MINISTERIO]

# Configuracao do Flask
app = Flask(__name__)

# Validacao do SECRET_KEY em producao
secret_key = os.environ.get('SECRET_KEY')
flask_env = os.environ.get('FLASK_ENV', 'development')

if flask_env == 'production' and not secret_key:
    print("AVISO: SECRET_KEY nao definido em producao! Usando chave temporaria.")
    print("Configure a variavel de ambiente SECRET_KEY no Render!")
    secret_key = secrets.token_hex(32)
elif not secret_key:
    secret_key = secrets.token_hex(16)

app.secret_key = secret_key

# Configuracoes de sessao para manter login persistente (especialmente em mobile)
app.config['SESSION_COOKIE_SECURE'] = flask_env == 'production'  # HTTPS em producao
app.config['SESSION_COOKIE_HTTPONLY'] = True  # Protege contra XSS
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # protecao CSRF basica
app.config['SESSION_REFRESH_EACH_REQUEST'] = False  # Nao renovar cookie a cada request
app.config['PERMANENT_SESSION_LIFETIME'] = 2592000  # 30 dias em segundos
app.config['SESSION_COOKIE_NAME'] = 'ministry_session'  # Nome customizado
app.config['REMEMBER_COOKIE_NAME'] = 'ministry_remember'  # Cookie "lembrar-me"
app.config['REMEMBER_COOKIE_DURATION'] = 2592000  # 30 dias para "lembrar-me"
app.config['REMEMBER_COOKIE_SECURE'] = flask_env == 'production'
app.config['REMEMBER_COOKIE_HTTPONLY'] = True
app.config['REMEMBER_COOKIE_SAMESITE'] = 'Lax'

# Configura o banco de dados SQLite na pasta 'instance'
# Em producao, use DATABASE_URL do ambiente (ex: PostgreSQL do Render/Heroku)
database_url = os.environ.get('DATABASE_URL', 'sqlite:///' + os.path.join(app.instance_path, 'ministry.db'))
# Render usa postgres:// mas SQLAlchemy 1.4+ requer postgresql://
if database_url and database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)
app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Desativa notificacoes de modificacao para performance
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')  # Pasta para uploads de audio
app.config['AVATAR_FOLDER'] = os.path.join('static', 'uploads', 'avatars')  # Pasta para fotos de perfil
app.config['MAX_CONTENT_LENGTH'] = int(os.environ.get('MAX_CONTENT_LENGTH', 50 * 1024 * 1024))  # 50 MB max file size

# Extensoes de arquivo permitidas
ALLOWED_AUDIO_EXTENSIONS = {'mp3', 'wav', 'ogg', 'm4a', 'aac', 'flac'}
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}  # Extensoes permitidas para avatares

# Configuracao para CSRF (opcional, caso queira usar Flask-WTF)
# Desativando temporariamente para testes, caso o Flask-WTF nao esteja instalado
app.config['WTF_CSRF_ENABLED'] = False  # Desativa protecao CSRF temporariamente para testes
app.config['WTF_CSRF_CHECK_DEFAULT'] = False  # Desativa verificacao CSRF por padrao temporariamente

# Garante que a pasta 'instance' exista
try:
    os.makedirs(app.instance_path, exist_ok=True)
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)  # Criar pasta de uploads
except OSError as e:
    print(f"Erro ao criar pastas: {e}")

# Funcao auxiliar para validar extensao de arquivo de audio
def allowed_audio_file(filename):
    """Verifica se a extensao do arquivo e permitida."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_AUDIO_EXTENSIONS

# Configuracao do banco de dados
db = SQLAlchemy(app)

# Configuracao do Flask-Login para autenticacao
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # Define a rota de login como padrao

# Configuracao opcional do Flask-WTF para CSRF
try:
    from flask_wtf.csrf import CSRFProtect
    csrf = CSRFProtect(app)
except ImportError:
    print("Flask-WTF nao instalado. protecao CSRF desativada. Instale com 'pip install flask-wtf' para habilitar.")
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['WTF_CSRF_CHECK_DEFAULT'] = False

# Modelos para o banco de dados
class User(db.Model, UserMixin):
    """Modelo para Usuarios administradores."""
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)  # Armazena o hash da senha
    is_admin = db.Column(db.Boolean, default=False)  # Mantido para compatibilidade
    role = db.Column(db.String(20), default=ROLE_MEMBRO)  # Nivel de permissao
    avatar = db.Column(db.String(255), nullable=True, default='default-avatar.png')  # Foto de perfil

    def set_password(self, password):
        """Define a senha como hash para o Usuario."""
        self.password = generate_password_hash(password)

    def check_password(self, password):
        """Verifica se a senha fornecida corresponde ao hash armazenado."""
        return check_password_hash(self.password, password)
    
    def has_admin_access(self):
        """Verifica se o Usuario tem acesso administrativo pleno."""
        return self.role in ADMIN_ROLES
    
    def is_ministro(self):
        """Verifica se o Usuario e ministro de louvor."""
        return self.role == ROLE_MINISTRO
    
    def get_id(self):
        """Retorna o ID do Usuario com prefixo para distinguir de membros."""
        return f"user_{self.id}"

class Member(db.Model, UserMixin):
    """Modelo para membros comuns do Ministerio."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    instrument = db.Column(db.String(120), nullable=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    password = db.Column(db.String(255), nullable=False)  # Armazena o hash da senha para membros
    suspended = db.Column(db.Boolean, default=False)  # Campo para indicar Suspensao
    is_admin = db.Column(db.Boolean, default=False)  # Mantido para compatibilidade
    role = db.Column(db.String(20), default=ROLE_MEMBRO)  # Nivel de permissao
    avatar = db.Column(db.String(255), nullable=True, default='default-avatar.png')  # Foto de perfil

    def set_password(self, password):
        """Define a senha como hash para o membro."""
        self.password = generate_password_hash(password)

    def check_password(self, password):
        """Verifica se a senha fornecida corresponde ao hash armazenado."""
        return check_password_hash(self.password, password)
    
    def has_admin_access(self):
        """Verifica se o membro tem acesso administrativo pleno."""
        return self.role in ADMIN_ROLES
    
    def is_ministro(self):
        """Verifica se o membro e ministro de louvor."""
        return self.role == ROLE_MINISTRO
    
    def get_id(self):
        """Retorna o ID do membro com prefixo para distinguir de Usuarios."""
        return f"member_{self.id}"

# Tabela de associacao para relacionamento many-to-many entre Culto e Repertorio
culto_repertorio = db.Table('culto_repertorio',
    db.Column('culto_id', db.Integer, db.ForeignKey('culto.id'), primary_key=True),
    db.Column('repertorio_id', db.Integer, db.ForeignKey('repertorio.id'), primary_key=True),
    db.Column('order', db.Integer, default=0)  # Ordem das musicas no culto
)

class Culto(db.Model):
    """Modelo para cultos do Ministerio."""
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    time = db.Column(db.Time, nullable=False)  # Alterado para db.Time para melhor manipulacao
    description = db.Column(db.String(255), nullable=False)
    
    # Relacionamento many-to-many com Repertorio
    musicas = db.relationship('Repertorio', secondary=culto_repertorio, 
                              backref=db.backref('cultos', lazy='dynamic'),
                              lazy='dynamic')

class Escala(db.Model):
    """Modelo para escalas de membros em cultos."""
    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey('member.id'), nullable=False)
    culto_id = db.Column(db.Integer, db.ForeignKey('culto.id'), nullable=False)
    role = db.Column(db.String(120), nullable=False)  # Ex.: "Guitarrista Principal"
    
    # NOVOS CAMPOS - Sistema de Confirmacao de Presenca
    status_confirmacao = db.Column(db.String(20), default='pendente')  # 'pendente', 'confirmado', 'negado'
    data_confirmacao = db.Column(db.DateTime, nullable=True)  # Quando confirmou/negou
    observacao_confirmacao = db.Column(db.Text, nullable=True)  # Mensagem opcional do membro

    member = db.relationship('Member', backref=db.backref('escalas', lazy=True))
    culto = db.relationship('Culto', backref=db.backref('escalas', lazy=True))

class Aviso(db.Model):
    """Modelo para avisos/notificacoes do Ministerio."""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    priority = db.Column(db.String(20), default='normal')  # low, normal, high, urgent
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    active = db.Column(db.Boolean, default=True)

class Repertorio(db.Model):
    """Modelo para repertorio musical."""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    artist = db.Column(db.String(120), nullable=True)
    key_tone = db.Column(db.String(20), nullable=True)  # Tom da musica (ex: C, D, Em)
    tempo = db.Column(db.String(20), nullable=True)  # Tempo/andamento
    link_video = db.Column(db.String(300), nullable=True)
    link_audio = db.Column(db.String(300), nullable=True)
    audio_file = db.Column(db.String(300), nullable=True)  # Arquivo de audio local (VS)
    lyrics = db.Column(db.Text, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    category = db.Column(db.String(50), nullable=True)  # louvor, adoracao, etc
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    added_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

class Indisponibilidade(db.Model):
    """Modelo para registrar indisponibilidades dos membros."""
    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey('member.id'), nullable=False)
    culto_id = db.Column(db.Integer, db.ForeignKey('culto.id'), nullable=True)
    date_start = db.Column(db.Date, nullable=False)
    date_end = db.Column(db.Date, nullable=True)
    reason = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default='approved')  # pending, approved, rejected
    admin_response = db.Column(db.Text, nullable=True)  # Resposta do administrador
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    member = db.relationship('Member', backref=db.backref('indisponibilidades', lazy=True))
    culto = db.relationship('Culto', backref=db.backref('indisponibilidades', lazy=True), foreign_keys=[culto_id])

class SolicitacaoExcecao(db.Model):
    """Modelo para solicitacoes de excecao quando admin precisa escalar membro indisponivel."""
    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    member_id = db.Column(db.Integer, db.ForeignKey('member.id'), nullable=False)
    culto_id = db.Column(db.Integer, db.ForeignKey('culto.id'), nullable=False)
    indisponibilidade_id = db.Column(db.Integer, db.ForeignKey('indisponibilidade.id'), nullable=True)
    motivo_solicitacao = db.Column(db.Text, nullable=False)  # Por que o admin precisa escalar
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    resposta_membro = db.Column(db.Text, nullable=True)  # Resposta do membro
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    respondido_em = db.Column(db.DateTime, nullable=True)
    
    admin = db.relationship('User', backref=db.backref('solicitacoes_excecao', lazy=True))
    member = db.relationship('Member', backref=db.backref('solicitacoes_excecao_recebidas', lazy=True))
    culto = db.relationship('Culto', backref=db.backref('solicitacoes_excecao', lazy=True))
    indisponibilidade = db.relationship('Indisponibilidade', backref=db.backref('solicitacoes_excecao', lazy=True))

class Feedback(db.Model):
    """Modelo para armazenar feedback dos Usuarios."""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=True)
    email = db.Column(db.String(120), nullable=False)
    message = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(50), default='feedback')  # feedback, bug, suggestion
    status = db.Column(db.String(20), default='pending')  # pending, reviewed, resolved
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    response = db.Column(db.Text, nullable=True)  # Resposta do admin
    responded_at = db.Column(db.DateTime, nullable=True)  # Data da resposta
    responded_by = db.Column(db.Integer, nullable=True)  # ID do admin que respondeu

class PushSubscription(db.Model):
    """Modelo para armazenar inscricoes de push notifications."""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    member_id = db.Column(db.Integer, db.ForeignKey('member.id'), nullable=True)
    endpoint = db.Column(db.Text, nullable=False, unique=True)
    p256dh_key = db.Column(db.Text, nullable=False)  # Chave pública para criptografia
    auth_key = db.Column(db.Text, nullable=False)  # Chave de autenticação
    device_info = db.Column(db.String(500), nullable=True)  # User agent / info do dispositivo
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_used = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    user = db.relationship('User', backref=db.backref('push_subscriptions', lazy=True))
    member = db.relationship('Member', backref=db.backref('push_subscriptions', lazy=True))

class Configuracao(db.Model):
    """Modelo para configuracoes do sistema."""
    id = db.Column(db.Integer, primary_key=True)
    chave = db.Column(db.String(100), unique=True, nullable=False)
    valor = db.Column(db.String(200), nullable=False)
    descricao = db.Column(db.String(300), nullable=True)
    atualizado_em = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Substituicao(db.Model):
    """Modelo para solicitacoes de substituicao de escalas."""
    id = db.Column(db.Integer, primary_key=True)
    escala_id = db.Column(db.Integer, db.ForeignKey('escala.id'), nullable=False)  # Escala original
    membro_solicitante_id = db.Column(db.Integer, db.ForeignKey('member.id'), nullable=False)  # Quem esta pedindo
    membro_substituto_id = db.Column(db.Integer, db.ForeignKey('member.id'), nullable=False)  # Quem vai substituir
    status = db.Column(db.String(20), default='pendente')  # pendente, aceito, recusado, cancelado
    mensagem = db.Column(db.Text, nullable=True)  # Mensagem opcional do solicitante
    resposta = db.Column(db.Text, nullable=True)  # Resposta do substituto
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    respondido_em = db.Column(db.DateTime, nullable=True)
    
    # Relacionamentos
    escala = db.relationship('Escala', backref=db.backref('substituicoes', lazy=True))
    solicitante = db.relationship('Member', foreign_keys=[membro_solicitante_id], backref=db.backref('substituicoes_solicitadas', lazy=True))
    substituto = db.relationship('Member', foreign_keys=[membro_substituto_id], backref=db.backref('substituicoes_recebidas', lazy=True))

# Carregar Usuario para Flask-Login (suporta tanto User quanto Member)
@login_manager.user_loader
def load_user(user_id):
    """Carrega um Usuario ou membro pelo ID para autenticacao."""
    with db.session.no_autoflush:  # Evita flush automatico durante a sessao
        # Verifica o prefixo para determinar qual tabela consultar
        if isinstance(user_id, str):
            if user_id.startswith('user_'):
                # Remove o prefixo e busca na tabela User
                numeric_id = int(user_id.replace('user_', ''))
                return db.session.get(User, numeric_id)
            elif user_id.startswith('member_'):
                # Remove o prefixo e busca na tabela Member
                numeric_id = int(user_id.replace('member_', ''))
                return db.session.get(Member, numeric_id)
        
        # Compatibilidade com sessoes antigas (sem prefixo)
        # Tenta User primeiro, depois Member
        user = db.session.get(User, int(user_id))
        if not user:
            return db.session.get(Member, int(user_id))
        return user

# Context processor para disponibilizar informaeees de permissao nos templates
@app.context_processor
def inject_user_permissions():
    """Injeta variaveis de permissao em todos os templates."""
    if current_user.is_authenticated:
        user_role = getattr(current_user, 'role', ROLE_MEMBRO)
        is_old_admin = getattr(current_user, 'is_admin', False)
        
        return {
            'IS_ADMIN': user_role in ADMIN_ROLES or is_old_admin,
            'IS_PASTOR': user_role == ROLE_PASTOR,
            'IS_LIDER_BANDA': user_role == ROLE_LIDER_BANDA,
            'IS_LIDER_MINISTERIO': user_role == ROLE_LIDER_MINISTERIO,
            'IS_LIDER': user_role in [ROLE_LIDER_BANDA, ROLE_LIDER_MINISTERIO],  # Compatibilidade
            'IS_MINISTRO': user_role == ROLE_MINISTRO,
            'USER_ROLE': user_role,
            'HAS_ADMIN_ACCESS': user_role in ADMIN_ROLES or is_old_admin,
            'HAS_MINISTRO_ACCESS': user_role in ADMIN_ROLES or user_role == ROLE_MINISTRO or is_old_admin
        }
    return {
        'IS_ADMIN': False,
        'IS_PASTOR': False,
        'IS_LIDER_BANDA': False,
        'IS_LIDER_MINISTERIO': False,
        'IS_LIDER': False,
        'IS_MINISTRO': False,
        'USER_ROLE': None,
        'HAS_ADMIN_ACCESS': False,
        'HAS_MINISTRO_ACCESS': False
    }

# Configurar headers de cache para PWA e arquivos estaticos
@app.after_request
def add_cache_headers(response):
    """Adiciona headers de cache para arquivos estaticos e icones PWA."""
    if request.path.startswith('/static/'):
        # Para ícones PWA: cache curto para forçar verificação de novas versões
        if 'icon' in request.path and any(request.path.endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.ico']):
            response.headers['Cache-Control'] = 'public, max-age=3600, must-revalidate'
            response.headers['ETag'] = 'v5.0-20260316'
        # Cache de 1 ano para outros assets estáticos (fontes, etc)
        elif any(request.path.endswith(ext) for ext in ['.svg', '.gif', '.woff', '.woff2', '.ttf', '.eot']):
            response.headers['Cache-Control'] = 'public, max-age=31536000, immutable'
        # Cache de 1 dia para CSS e JS
        elif any(request.path.endswith(ext) for ext in ['.css', '.js']):
            response.headers['Cache-Control'] = 'public, max-age=86400'
    
    # Garantir que manifest e service worker sejam sempre atualizados
    if request.path in ['/static/manifest.json', '/static/sw.js']:
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
    
    return response

# Decorador para verificar se o Usuario e admin
def admin_required(f):
    """Requer acesso administrativo pleno (Admin, Pastor ou Lider)."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Verifica se o Usuario tem role de admin ou usa o is_admin antigo
        user_role = getattr(current_user, 'role', None)
        is_old_admin = getattr(current_user, 'is_admin', False)
        
        if not (user_role in ADMIN_ROLES or is_old_admin):
            flash('Acesso negado. Somente administradores podem acessar esta pegina.', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# Decorador para verificar se e ministro ou admin
def ministro_or_admin_required(f):
    """Requer acesso de ministro de louvor ou superior."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_role = getattr(current_user, 'role', ROLE_MEMBRO)
        is_old_admin = getattr(current_user, 'is_admin', False)
        
        allowed_roles = ADMIN_ROLES + [ROLE_MINISTRO]
        if not (user_role in allowed_roles or is_old_admin):
            flash('Acesso negado. Somente ministros ou administradores podem acessar esta funcionalidade.', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# funcao auxiliar para verificar se Usuario pode gerenciar musicas de uma escala
def can_manage_escala_musicas(culto_id, user):
    """
    Verifica se o Usuario pode gerenciar musicas de um culto/escala especefico.
    - Admin/Pastor/Lider: pode gerenciar qualquer escala
    - Ministro: pode gerenciar apenas escalas onde esta escalado
    - Membro comum: nao pode gerenciar
    """
    user_role = getattr(user, 'role', ROLE_MEMBRO)
    is_old_admin = getattr(user, 'is_admin', False)
    
    # Admin, Pastor e Lider podem tudo
    if user_role in ADMIN_ROLES or is_old_admin:
        return True
    
    # Ministro pode gerenciar apenas suas escalas
    if user_role == ROLE_MINISTRO:
        # Verificar se o ministro esta escalado neste culto
        # Para Member, precisamos buscar por email; para User, por id
        if isinstance(user, Member):
            escala_do_ministro = Escala.query.join(Member).filter(
                Escala.culto_id == culto_id,
                Member.email == user.email
            ).first()
        else:
            # Para User, nao he escalas vinculadas diretamente
            return False
        
        return escala_do_ministro is not None
    
    return False

# Criar um administrador padrao
def create_admin():
    """Cria um administrador padrao se nao existir."""
    email = "admin@ministry.com"
    password = "admin123"
    try:
        existing_admin = User.query.filter_by(email=email).first()
        if not existing_admin:
            new_admin = User(email=email, is_admin=True, role=ROLE_ADMIN)
            new_admin.set_password(password)
            db.session.add(new_admin)
            db.session.commit()
            print(f"? Administrador criado: {email} / {password}")
        else:
            # Atualizar role se je existe mas nao tem role definido
            if not existing_admin.role or existing_admin.role == ROLE_MEMBRO:
                existing_admin.role = ROLE_ADMIN
                existing_admin.is_admin = True
                db.session.commit()
                print(f"? Role do administrador atualizado: {email}")
            else:
                print(f"?? Administrador je existe: {email}")
    except Exception as e:
        db.session.rollback()
        print(f"?? Erro ao criar admin: {e}")

# funcao para verificar e garantir a criaeeo do banco de dados
def ensure_database_exists():
    """Verifica se o banco de dados existe e o cria, se necesserio."""
    # Garantir que a pasta instance existe (apenas para SQLite local)
    database_uri = app.config['SQLALCHEMY_DATABASE_URI']
    is_sqlite = database_uri.startswith('sqlite:///')
    
    if is_sqlite:
        try:
            os.makedirs(app.instance_path, exist_ok=True)
            print(f"Pasta instance criada/verificada em: {app.instance_path}")
        except Exception as e:
            print(f"Erro ao criar pasta instance: {e}")
            raise
    
    # Garantir que a pasta de uploads existe
    try:
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        print(f"Pasta uploads criada/verificada em: {app.config['UPLOAD_FOLDER']}")
    except Exception as e:
        print(f"Aviso: Erro ao criar pasta uploads: {e}")
    
    # Criar todas as tabelas no banco de dados
    try:
        with app.app_context():
            db.create_all()
            print(f"Tabelas do banco de dados criadas/verificadas.")
            print(f"Usando banco de dados: {'SQLite' if is_sqlite else 'PostgreSQL'}")
    except Exception as e:
        print(f"ERRO ao criar tabelas do banco de dados: {e}")
        raise

# Rotas principais
@app.route('/')
@login_required
def index():
    """Rota para a pegina inicial."""
    print(f"User is admin: {current_user.is_admin}")  # Depuraeeo para verificar is_admin
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Rota para login de Usuarios e membros."""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        try:
            # Tenta encontrar o Usuario como User ou Member
            user = User.query.filter_by(email=email).first()
            if not user:
                user = Member.query.filter_by(email=email).first()
            
            if user and user.check_password(password):
                # Verifica se e membro suspenso
                if isinstance(user, Member) and user.suspended:
                    flash('Sua conta foi suspensa. Entre em contato com o administrador.', 'error')
                    return render_template('login.html')
                
                # Marca sessao como permanente (mantem login por 30 dias)
                session.permanent = True
                
                login_user(user, remember=True)  # remember=True ativa cookie "lembrar-me"
                session['user_id'] = user.id
                session['is_admin'] = getattr(user, 'is_admin', False)  # Verifica se e admin (se User tem is_admin)
                print(f"? Login bem-sucedido: {email} (Admin: {session['is_admin']}) - sessao permanente ativada")
                return redirect(url_for('index'))
            
            flash('Login falhou. Verifique email e senha.', 'error')
            print(f"? Login falhou para: {email}")
            
        except Exception as e:
            print(f"?? Erro no login: {e}")
            import traceback
            traceback.print_exc()
            flash('Erro ao processar login. Tente novamente.', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    """Rota para logout."""
    logout_user()
    session.pop('user_id', None)
    session.pop('is_admin', None)
    return redirect(url_for('login'))

@app.route('/perfil')
@login_required
def perfil():
    """Rota para a pegina de perfil do Usuario."""
    return render_template('perfil.html')

@app.route('/get_perfil', methods=['GET'])
@login_required
def get_perfil():
    """Retorna os dados do perfil do Usuario logado."""
    try:
        # Usar current_user do Flask-Login (je carregado corretamente pelo load_user)
        user = current_user
        
        if not user or not user.is_authenticated:
            return jsonify({'success': False, 'message': 'Usuario nao encontrado'}), 404
        
        # Se for User (admin), buscar Member associado pelo email
        member = None
        if isinstance(user, User):
            member = Member.query.filter_by(email=user.email).first()
        
        # Obter role e is_admin
        user_role = getattr(user, 'role', ROLE_MEMBRO)
        is_admin = getattr(user, 'is_admin', False)
        
        perfil_data = {
            'id': user.id,
            'name': member.name if member else (user.name if isinstance(user, Member) else user.email.split('@')[0]),
            'email': user.email,
            'phone': member.phone if member else getattr(user, 'phone', ''),
            'instrument': member.instrument if member else getattr(user, 'instrument', ''),
            'avatar': getattr(user, 'avatar', 'default-avatar.png') or 'default-avatar.png',
            'is_admin': is_admin,
            'role': user_role  # Adicionar role ao retorno
        }
        
        return jsonify({'success': True, 'perfil': perfil_data})
    except Exception as e:
        print(f"Erro ao carregar perfil: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/update_perfil', methods=['POST'])
@login_required
def update_perfil():
    """Atualiza os dados do perfil do Usuario logado."""
    try:
        data = request.get_json()
        # Usar current_user do Flask-Login
        user = current_user
        
        if not user or not user.is_authenticated:
            return jsonify({'success': False, 'message': 'Usuario nao encontrado'}), 404
        
        # Se for Member, atualizar diretamente
        if isinstance(user, Member):
            if 'name' in data:
                user.name = data['name']
            if 'phone' in data:
                user.phone = data['phone']
            if 'instrument' in data:
                user.instrument = data['instrument']
            if 'password' in data and data['password']:
                user.set_password(data['password'])
        else:  # User (admin)
            # Atualizar Member associado se existir
            member = Member.query.filter_by(email=user.email).first()
            if member:
                if 'name' in data:
                    member.name = data['name']
                if 'phone' in data:
                    member.phone = data['phone']
                if 'instrument' in data:
                    member.instrument = data['instrument']
            
            # Atualizar senha do User
            if 'password' in data and data['password']:
                user.set_password(data['password'])
        
        db.session.commit()
        return jsonify({'success': True, 'message': 'Perfil atualizado com sucesso!'})
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao atualizar perfil: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/upload_avatar', methods=['POST'])
@login_required
def upload_avatar():
    """Faz upload da foto de perfil do Usuario."""
    try:
        if 'avatar' not in request.files:
            return jsonify({'success': False, 'message': 'Nenhuma imagem enviada'}), 400
        
        file = request.files['avatar']
        
        if file.filename == '':
            return jsonify({'success': False, 'message': 'Nenhum arquivo selecionado'}), 400
        
        # Verificar extensao do arquivo
        if '.' not in file.filename:
            return jsonify({'success': False, 'message': 'Arquivo invelido'}), 400
        
        ext = file.filename.rsplit('.', 1)[1].lower()
        if ext not in ALLOWED_IMAGE_EXTENSIONS:
            return jsonify({'success': False, 'message': f'Apenas arquivos {", ".join(ALLOWED_IMAGE_EXTENSIONS)} seo permitidos'}), 400
        
        # Gerar nome enico para o arquivo
        filename = secure_filename(f"avatar_{current_user.id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.{ext}")
        
        # Criar pasta de avatares se nao existir
        os.makedirs(app.config['AVATAR_FOLDER'], exist_ok=True)
        
        # Salvar arquivo
        filepath = os.path.join(app.config['AVATAR_FOLDER'], filename)
        file.save(filepath)
        
        # Atualizar banco de dados
        user = current_user
        
        if not user:
            return jsonify({'success': False, 'message': 'Usuario nao encontrado'}), 404
        
        # Remover avatar antigo se nao for o padrao
        if hasattr(user, 'avatar') and user.avatar and user.avatar != 'default-avatar.png':
            old_path = os.path.join(app.config['AVATAR_FOLDER'], user.avatar)
            if os.path.exists(old_path):
                try:
                    os.remove(old_path)
                except:
                    pass
        
        user.avatar = filename
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Foto atualizada com sucesso!', 'avatar': filename})
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao fazer upload de avatar: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/membros')
@login_required
def membros():
    """Rota para a pegina de membros."""
    print(f"User is admin in /membros: {current_user.is_admin}")  # Depuraeeo
    return render_template('membros.html')

@app.route('/get_members', methods=['GET'])
@login_required
def get_members():
    """Retorna todos os membros em formato JSON."""
    try:
        # Pegar paremetro opcional de culto_id para filtrar indispoNiveis
        culto_id = request.args.get('culto_id', type=int)
        
        with db.session.no_autoflush:
            members = Member.query.all()
        
        # Se culto_id fornecido, buscar indisponibilidades
        indisponiveis_ids = []
        if culto_id:
            indisponibilidades = Indisponibilidade.query.filter_by(
                culto_id=culto_id,
                status='approved'
            ).all()
            indisponiveis_ids = [ind.member_id for ind in indisponibilidades]
        
        members_list = []
        for member in members:
            member_data = {
                'id': member.id,
                'name': member.name,
                'instrument': member.instrument,  # Campo instrument para compatibilidade com frontend
                'email': member.email,
                'phone': member.phone,
                'suspended': member.suspended,
                'role': getattr(member, 'role', ROLE_MEMBRO),  # Nivel de permissao
                'indisponivel': member.id in indisponiveis_ids  # Flag para indicar se esta indispoNivel
            }
            members_list.append(member_data)
        
        return jsonify({'members': members_list})
    except Exception as e:
        print(f"Erro ao carregar membros: {str(e)}")
        return jsonify({'error': str(e), 'members': []}), 500

@app.route('/feedback')
@login_required
def feedback():
    """Rota para a pegina de feedback."""
    return render_template('feedback.html')

@app.route('/cultos')
@login_required
def cultos():
    """Rota para a pegina de cultos."""
    with db.session.no_autoflush:
        cultos = Culto.query.order_by(Culto.date.asc()).all()  # Ordena por data ascendente
    return render_template('cultos.html', cultos=cultos)

@app.route('/escalas')
@login_required
def escalas():
    """Rota para a pegina de escalas gerais (todas as escalas do Ministerio)."""
    return render_template('escalas.html')

@app.route('/minhas_escalas')
@login_required
def minhas_escalas():
    """Rota para a pegina de escalas pessoais (apenas escalas onde o Usuario esta escalado)."""
    return render_template('minhas_escalas.html')

@app.route('/get_escalas', methods=['GET'])
@login_required
def get_escalas():
    """Retorna todas as escalas com informaeees dos cultos e membros."""
    try:
        # Buscar todas as escalas com joins
        escalas = db.session.query(Escala, Culto, Member).join(
            Culto, Escala.culto_id == Culto.id
        ).join(
            Member, Escala.member_id == Member.id
        ).order_by(Culto.date, Culto.time).all()
        
        # Retornar lista plana de escalas no formato esperado pelo template
        escalas_list = []
        for escala, culto, membro in escalas:
            date_time_str = f"{culto.date.strftime('%Y-%m-%d')}T{culto.time.strftime('%H:%M')}"
            
            # Verificar se o culto já passou
            culto_datetime = datetime.combine(culto.date, culto.time)
            ja_passou = culto_datetime < datetime.now()
            
            escalas_list.append({
                'escala_id': escala.id,  # ID da escala para edieeo/excluseo
                'id': escala.id,
                'culto_id': culto.id,
                'culto_name': culto.description,
                'culto_date': date_time_str,
                'member_id': membro.id,
                'member_name': membro.name,
                'role': escala.role,
                'instrument': membro.instrument,
                'ja_passou': ja_passou,
                'status_confirmacao': escala.status_confirmacao,
                'data_confirmacao': escala.data_confirmacao.strftime('%Y-%m-%d %H:%M:%S') if escala.data_confirmacao else None,
                'observacao_confirmacao': escala.observacao_confirmacao
            })
        
        return jsonify({'escalas': escalas_list}), 200
    except Exception as e:
        print(f"Erro ao buscar escalas: {str(e)}")
        return jsonify({'escalas': []}), 500

@app.route('/get_minhas_escalas', methods=['GET'])
@login_required
def get_minhas_escalas():
    """Retorna as escalas onde o Usuario logado esta escalado + outros membros da mesma equipe."""
    try:
        print(f"\nDEBUG: get_minhas_escalas chamado")
        print(f"current_user: {current_user}")
        print(f"current_user.id: {current_user.id if current_user.is_authenticated else 'Not authenticated'}")
        print(f"current_user type: {type(current_user)}")
        
        # Usar current_user ao inves de session para evitar problemas
        user = current_user
        print(f"User encontrado: {user}")
        
        # Buscar o membro correspondente
        if isinstance(user, User):
            member = Member.query.filter_by(email=user.email).first()
            print(f"Membro encontrado via email: {member}")
        else:
            member = user
            print(f"Usuario ja e membro: {member}")
        
        if not member:
            print("ERRO: Nenhum membro encontrado!")
            return jsonify({'escalas': []}), 200
        
        print(f"OK - Membro: {member.name} (ID: {member.id})")
        
        # 1. Buscar cultos onde o Usuario esta escalado
        meus_cultos = db.session.query(Escala.culto_id).filter(
            Escala.member_id == member.id
        ).distinct().all()
        
        culto_ids = [c[0] for c in meus_cultos]
        print(f"Cultos onde esta escalado: {culto_ids}")
        
        if not culto_ids:
            print("INFO: Usuario nao esta escalado em nenhum culto")
            return jsonify({'escalas': []}), 200
        
        # 2. Buscar TODAS as escalas desses cultos (para mostrar a equipe completa)
        escalas = db.session.query(Escala, Culto, Member).join(
            Culto, Escala.culto_id == Culto.id
        ).join(
            Member, Escala.member_id == Member.id
        ).filter(
            Escala.culto_id.in_(culto_ids)
        ).order_by(Culto.date, Culto.time, Escala.id).all()
        
        print(f"Total de escalas (incluindo equipe): {len(escalas)}")
        
        # 3. Montar lista com marcaeeo do Usuario atual
        escalas_list = []
        for escala, culto, membro in escalas:
            date_time_str = f"{culto.date.strftime('%Y-%m-%d')}T{culto.time.strftime('%H:%M')}"
            
            # Verificar se o culto je passou
            culto_datetime = datetime.combine(culto.date, culto.time)
            ja_passou = culto_datetime < datetime.now()
            
            escalas_list.append({
                'escala_id': escala.id,
                'id': escala.id,
                'culto_id': culto.id,
                'culto_name': culto.description,
                'culto_date': date_time_str,
                'member_id': membro.id,
                'member_name': membro.name,
                'role': escala.role,
                'instrument': membro.instrument,
                'is_me': membro.id == member.id,  # Marca se e o Usuario logado
                'ja_passou': ja_passou,
                'status_confirmacao': escala.status_confirmacao,
                'data_confirmacao': escala.data_confirmacao.strftime('%Y-%m-%d %H:%M:%S') if escala.data_confirmacao else None,
                'observacao_confirmacao': escala.observacao_confirmacao
            })
        
        print(f"OK - Retornando {len(escalas_list)} escalas")
        return jsonify({'escalas': escalas_list}), 200
    except Exception as e:
        print(f"ERRO ao buscar minhas escalas: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'escalas': []}), 500

# Rotas para gerenciar cultos (apenas para admins)
@app.route('/get_cultos', methods=['GET'])
@login_required
def get_cultos():
    """Carrega a lista de cultos, ordenada por data."""
    with db.session.no_autoflush:
        cultos = Culto.query.order_by(Culto.date.asc(), Culto.time.asc()).all()
    print(f"Retornando {len(cultos)} cultos: {[(c.id, c.date, c.time, c.description) for c in cultos]}")  # Depuraeeo
    
    cultos_list = []
    for culto in cultos:
        # Combinar data e hora em um enico datetime string
        date_time_str = f"{culto.date.strftime('%Y-%m-%d')}T{culto.time.strftime('%H:%M')}"
        
        # Verificar se o culto já passou
        culto_datetime = datetime.combine(culto.date, culto.time)
        ja_passou = culto_datetime < datetime.now()
        
        cultos_list.append({
            'id': culto.id,
            'name': culto.description,  # Usar description como name
            'description': culto.description,
            'date': culto.date.strftime('%Y-%m-%d'),
            'time': culto.time.strftime('%H:%M'),
            'date_time': date_time_str,  # Campo esperado pelo template
            'ja_passou': ja_passou
        })
    
    return jsonify({'cultos': cultos_list})

@app.route('/get_culto/<int:culto_id>', methods=['GET'])
@login_required
@admin_required
def get_culto(culto_id):
    """Carrega os dados de um culto especefico (apenas para admins)."""
    with db.session.no_autoflush:
        culto = db.session.get(Culto, culto_id)
        if not culto:
            return jsonify({'error': 'Culto nao encontrado'}), 404
    return jsonify({
        'id': culto.id,
        'date': culto.date.strftime('%Y-%m-%d'),
        'time': culto.time.strftime('%H:%M'),
        'description': culto.description
    })

@app.route('/add_culto', methods=['POST'])
@login_required
@admin_required
def add_culto():
    """Adiciona um novo culto (apenas para admins)."""
    data = request.json
    print(f"Dados recebidos para add_culto: {data}")  # Depuraeeo
    
    name = data.get('name')
    date_time_str = data.get('date_time')
    description = data.get('description', '')
    
    if not all([name, date_time_str]):
        return jsonify({'success': False, 'message': 'Nome e data/hora seo obrigaterios.'}), 400
    
    try:
        # Parse date_time no formato ISO: "2026-03-15T19:30"
        date_time_obj = datetime.strptime(date_time_str, '%Y-%m-%dT%H:%M')
        date_obj = date_time_obj.date()
        time_obj = date_time_obj.time()
        
        with db.session.no_autoflush:
            existing_culto = Culto.query.filter_by(date=date_obj, time=time_obj, description=name).first()
            if existing_culto:
                print(f"Culto je existe no banco: ID {existing_culto.id}, Data {existing_culto.date}, Horerio {existing_culto.time}, Descrieeo {existing_culto.description}")  # Depuraeeo
                return jsonify({'success': False, 'message': 'Este culto je existe.'}), 400
        
        novo_culto = Culto(date=date_obj, time=time_obj, description=name)
        db.session.add(novo_culto)
        db.session.commit()
        print(f"Culto cadastrado com sucesso: {novo_culto.id}, {novo_culto.date}, {novo_culto.time}, {novo_culto.description}")  # Depuraeeo
        return jsonify({'success': True, 'message': 'Culto adicionado com sucesso!'}), 200
    except ValueError as ve:
        print(f"Erro de formato nos dados: {str(ve)}")  # Depuraeeo
        return jsonify({'success': False, 'message': f'Data ou horerio em formato invelido: {str(ve)}'}), 400
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao salvar culto: {str(e)}")  # Depuraeeo
        return jsonify({'success': False, 'message': f'Erro interno ao cadastrar culto: {str(e)}'}), 500

@app.route('/edit_culto', methods=['PUT'])
@login_required
@admin_required
def edit_culto():
    """Edita um culto existente (apenas para admins)."""
    data = request.json
    culto_id = data.get('id')
    name = data.get('name')
    date_time_str = data.get('date_time')
    description = data.get('description', '')
    
    if not all([culto_id, name, date_time_str]):
        return jsonify({'success': False, 'message': 'ID, nome e data/hora seo obrigaterios.'}), 400
    
    with db.session.no_autoflush:
        culto = db.session.get(Culto, culto_id)
        if not culto:
            return jsonify({'success': False, 'message': 'Culto nao encontrado'}), 404
    
    try:
        # Parse date_time no formato ISO: "2026-03-15T19:30"
        date_time_obj = datetime.strptime(date_time_str, '%Y-%m-%dT%H:%M')
        date_obj = date_time_obj.date()
        time_obj = date_time_obj.time()
        
        with db.session.no_autoflush:
            # Verificar se outro culto com mesmas data/hora/nome je existe
            existing = Culto.query.filter(
                Culto.id != culto_id, 
                Culto.date == date_obj, 
                Culto.time == time_obj, 
                Culto.description == name
            ).first()
            if existing:
                return jsonify({'success': False, 'message': 'Outro culto com esses dados je existe.'}), 400
        
        culto.date = date_obj
        culto.time = time_obj
        culto.description = name
        db.session.commit()
        return jsonify({'success': True, 'message': 'Culto atualizado com sucesso!'}), 200
    except ValueError as ve:
        return jsonify({'success': False, 'message': f'Data ou horerio em formato invelido: {str(ve)}'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Erro ao atualizar culto: {str(e)}'}), 500

@app.route('/delete_culto/<int:culto_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_culto(culto_id):
    """Remove um culto (apenas para admins)."""
    with db.session.no_autoflush:
        culto = db.session.get(Culto, culto_id)
        if not culto:
            return jsonify({'success': False, 'message': 'Culto nao encontrado'}), 404
    db.session.delete(culto)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Culto removido com sucesso!'}), 200

# Rotas para gerenciar membros (apenas para admins)
@app.route('/add_member', methods=['POST'])
@login_required
@admin_required
def add_member():
    """Adiciona um novo membro (apenas para admins)."""
    data = request.json
    print(f"Dados recebidos para add_member: {data}")  # Depuraeeo
    name = data.get('name')
    instrument = data.get('instrument')
    email = data.get('email')
    phone = data.get('phone')
    password = data.get('password', '123456')  # Senha padrao, caso nao fornecida
    if not all([name, email]):  # Nome e email seo obrigaterios
        return jsonify({'success': False, 'message': 'Nome e email seo obrigaterios.'}), 400
    try:
        with db.session.no_autoflush:
            existing_member = Member.query.filter_by(email=email).first()
            if existing_member:
                return jsonify({'success': False, 'message': 'Este email je esta cadastrado.'}), 400
        
        # Definir role padrao como membro
        role = data.get('role', ROLE_MEMBRO)
        if role not in [ROLE_ADMIN, ROLE_PASTOR, ROLE_LIDER_BANDA, ROLE_LIDER_MINISTERIO, ROLE_MINISTRO, ROLE_MEMBRO]:
            role = ROLE_MEMBRO
        
        novo_membro = Member(name=name, instrument=instrument, email=email, phone=phone, suspended=False, role=role)
        novo_membro.is_admin = role in ADMIN_ROLES  # Sincronizar is_admin
        novo_membro.set_password(password)  # Define a senha hashada
        db.session.add(novo_membro)
        db.session.commit()
        print(f"Membro cadastrado com sucesso: {novo_membro.id}, {novo_membro.name}, {novo_membro.email}")  # Depuraeeo
        return jsonify({'success': True, 'message': 'Membro cadastrado com sucesso! A senha padrao e 123456, e o membro pode altere-la no perfil.'}), 200
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao salvar membro: {str(e)}")  # Depuraeeo
        return jsonify({'success': False, 'message': f'Erro interno ao cadastrar membro: {str(e)}'}), 500

@app.route('/get_member/<int:member_id>', methods=['GET'])
@login_required
@admin_required
def get_member(member_id):
    """Carrega os dados de um membro especefico (apenas para admins)."""
    with db.session.no_autoflush:
        member = db.session.get(Member, member_id)
        if not member:
            return jsonify({'error': 'Membro nao encontrado'}), 404
    print(f"Retornando dados do membro {member_id}: {member.name}, suspended: {member.suspended}")  # Depuraeeo
    return jsonify({
        'id': member.id,
        'name': member.name,
        'instrument': member.instrument,
        'email': member.email,
        'phone': member.phone,
        'suspended': member.suspended,
        'role': getattr(member, 'role', ROLE_MEMBRO)
    })

@app.route('/update_member', methods=['POST'])
@login_required
@admin_required
def update_member():
    """Edita um membro existente (apenas para admins)."""
    data = request.get_json()
    print(f"Recebendo atualizaeeo para membro ID {data.get('id')}: {data}")  # Depuraeeo
    if not data or 'id' not in data:
        return jsonify({'success': False, 'message': 'Dados invelidos ou ID ausente'}), 400
    try:
        with db.session.no_autoflush:
            member = db.session.get(Member, data['id'])
            if not member:
                return jsonify({'success': False, 'message': 'Membro nao encontrado'}), 404
        
        member.name = data.get('name', member.name)
        member.instrument = data.get('instrument', member.instrument)
        member.email = data.get('email', member.email)
        member.phone = data.get('phone', member.phone)
        
        # Atualizar role (Nivel de permissao)
        if 'role' in data:
            new_role = data['role']
            if new_role in [ROLE_ADMIN, ROLE_PASTOR, ROLE_LIDER_BANDA, ROLE_LIDER_MINISTERIO, ROLE_MINISTRO, ROLE_MEMBRO]:
                member.role = new_role
                # Sincronizar is_admin com o role
                member.is_admin = new_role in ADMIN_ROLES
                print(f"Role atualizado para: {new_role}")
        
        if 'password' in data and data['password']:
            member.set_password(data['password'])
        
        db.session.commit()
        return jsonify({'success': True, 'message': 'Membro atualizado com sucesso!'})
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao atualizar membro: {str(e)}")  # Depuraeeo
        return jsonify({'success': False, 'message': f'Erro interno ao atualizar membro: {str(e)}'}), 500

@app.route('/toggle_suspend_member/<int:member_id>', methods=['POST'])
@login_required
@admin_required
def toggle_suspend_member(member_id):
    """Suspende ou reativa um membro (apenas para admins)."""
    try:
        with db.session.no_autoflush:
            member = db.session.get(Member, member_id)
            if not member:
                return jsonify({'success': False, 'message': 'Membro nao encontrado'}), 404
        print(f"Alterando status de Suspensao do membro {member_id}: {member.suspended} -> {not member.suspended}")  # Depuraeeo
        member.suspended = not member.suspended  # Alterna o estado
        db.session.commit()
        return jsonify({'success': True, 'message': f'Membro {member.suspended and "suspenso" or "reativado"} com sucesso!'})
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao suspender/reativar membro: {str(e)}")  # Depuraeeo
        return jsonify({'success': False, 'message': f'Erro interno ao suspender/reativar membro: {str(e)}'}), 500

@app.route('/delete_member/<int:member_id>', methods=['POST'])
@login_required
@admin_required
def delete_member(member_id):
    """Remove um membro (apenas para admins)."""
    try:
        with db.session.no_autoflush:
            member = db.session.get(Member, member_id)
            if not member:
                return jsonify({'success': False, 'message': 'Membro nao encontrado'}), 404
        
        print(f"Excluindo membro {member_id}: {member.name}")  # Depuraeeo
        
        # Deletar registros relacionados primeiro (se as tabelas existirem)
        try:
            # Deletar indisponibilidades relacionadas
            Indisponibilidade.query.filter_by(member_id=member_id).delete()
        except Exception as e:
            print(f"Aviso: nao foi possevel deletar indisponibilidades (tabela pode nao existir): {e}")
        
        try:
            # Deletar escalas relacionadas
            Escala.query.filter_by(member_id=member_id).delete()
        except Exception as e:
            print(f"Aviso: nao foi possevel deletar escalas: {e}")
        
        # Deletar o membro
        db.session.delete(member)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Membro excluedo com sucesso!'})
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao excluir membro: {str(e)}")  # Depuraeeo
        return jsonify({'success': False, 'message': f'Erro ao excluir membro'}), 500

# Rotas para gerenciar escalas (apenas para admins)
@app.route('/add_escala', methods=['POST'])
@login_required
@admin_required
def add_escala():
    """Adiciona uma nova escala (apenas para admins)."""
    # Aceitar tanto JSON quanto form data
    if request.is_json:
        data = request.json
    else:
        data = request.form.to_dict()
    
    member_id = data.get('member_id')
    culto_id = data.get('culto_id')
    role = data.get('role')
    if not all([member_id, culto_id, role]):
        return jsonify({'success': False, 'message': 'Dados invelidos.'}), 400
    try:
        with db.session.no_autoflush:
            # Verificar se o membro je esta escalado
            if Escala.query.filter_by(member_id=member_id, culto_id=culto_id).first():
                return jsonify({'success': False, 'message': 'Este membro je esta escalado para este culto.'}), 400
            
            # VERIFICACAO MELHORADA: Verificar se o membro esta indispoNivel para este culto
            indisponibilidade = Indisponibilidade.query.filter_by(
                member_id=member_id,
                culto_id=culto_id
            ).filter(Indisponibilidade.status.in_(['approved', 'pending'])).first()
            
            if indisponibilidade:
                member = Member.query.get(member_id)
                member_name = member.name if member else 'Membro'
                
                # Retornar informacao de que o membro esta indisponivel
                # com opcao de solicitar excecao
                return jsonify({
                    'success': False, 
                    'indisponivel': True,
                    'indisponibilidade_id': indisponibilidade.id,
                    'member_id': member_id,
                    'member_name': member_name,
                    'motivo_indisponibilidade': indisponibilidade.reason,
                    'message': f'{member_name} esta INDISPONivel para este culto. Motivo: {indisponibilidade.reason}'
                }), 400
        
        nova_escala = Escala(member_id=member_id, culto_id=culto_id, role=role)
        db.session.add(nova_escala)
        db.session.commit()
        
        # PUSH NOTIFICATION: Notificar membro sobre nova escala
        try:
            member = db.session.get(Member, member_id)
            culto = db.session.get(Culto, culto_id)
            
            if member and culto:
                # Buscar todas as subscricoes ativas do membro
                subscriptions = PushSubscription.query.filter_by(
                    member_id=member_id, 
                    is_active=True
                ).all()
                
                if subscriptions:
                    # Formatar data e hora do culto
                    from datetime import datetime as dt
                    if culto.date and culto.time:
                        culto_datetime = dt.combine(culto.date, culto.time)
                        culto_data_str = culto_datetime.strftime("%d/%m/%Y às %H:%M")
                    else:
                        culto_data_str = "data não definida"
                    
                    for sub in subscriptions:
                        send_push_notification(
                            sub,
                            f'📋 Nova Escala: {culto.description}',
                            f'Você foi escalado(a) como {role} em {culto_data_str}. Por favor, confirme sua presença!',
                            {
                                'type': 'nova_escala',
                                'url': '/minhas_escalas',
                                'escala_id': nova_escala.id,
                                'culto_id': culto_id,
                                'requireInteraction': True
                            }
                        )
        except Exception as e:
            # Não falhar a criação da escala se a notificação falhar
            print(f"Erro ao enviar notificação push: {e}")
        
        return jsonify({'success': True, 'message': 'Escala adicionada com sucesso!'}), 200
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao salvar escala: {str(e)}")  # Depuraeeo
        return jsonify({'success': False, 'message': f'Erro interno ao cadastrar escala: {str(e)}'}), 500

@app.route('/edit_escala/<int:escala_id>', methods=['POST'])
@login_required
@admin_required
def edit_escala(escala_id):
    """Edita uma escala existente (apenas para admins)."""
    data = request.json
    member_id = data.get('member_id')
    role = data.get('role')
    
    if not member_id and not role:
        return jsonify({'success': False, 'message': 'Dados invelidos.'}), 400
    
    try:
        with db.session.no_autoflush:
            escala = db.session.get(Escala, escala_id)
            if not escala:
                return jsonify({'success': False, 'message': 'Escala nao encontrada'}), 404
            
            # Atualizar campos fornecidos
            if member_id:
                escala.member_id = member_id
            if role:
                escala.role = role
                
            db.session.commit()
        return jsonify({'success': True, 'message': 'Escala atualizada com sucesso!'}), 200
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao editar escala: {str(e)}")  # Depuraeeo
        return jsonify({'success': False, 'message': f'Erro interno ao atualizar escala: {str(e)}'}), 500
        print(f"Erro ao editar escala: {str(e)}")  # Depuraeeo
        return jsonify({'success': False, 'message': f'Erro interno ao atualizar escala: {str(e)}'}), 500

@app.route('/delete_escala/<int:escala_id>', methods=['POST'])
@login_required
@admin_required
def delete_escala(escala_id):
    """Remove uma escala (apenas para admins)."""
    try:
        with db.session.no_autoflush:
            escala = db.session.get(Escala, escala_id)
            if not escala:
                return jsonify({'success': False, 'message': 'Escala nao encontrada'}), 404
        db.session.delete(escala)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Escala removida com sucesso!'}), 200
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao excluir escala: {str(e)}")  # Depuraeeo
        return jsonify({'success': False, 'message': f'Erro interno ao excluir escala: {str(e)}'}), 500

@app.route('/delete_escalas_culto/<int:culto_id>', methods=['POST'])
@login_required
@admin_required
def delete_escalas_culto(culto_id):
    """Remove todas as escalas de um culto especefico e limpa o repertorio (apenas para admins)."""
    try:
        escalas = Escala.query.filter_by(culto_id=culto_id).all()
        if not escalas:
            return jsonify({'success': False, 'message': 'Nenhuma escala encontrada para este culto'}), 404
        
        count = len(escalas)
        for escala in escalas:
            db.session.delete(escala)
        
        # Limpar tambem o repertorio do culto
        db.session.execute(
            culto_repertorio.delete().where(culto_repertorio.c.culto_id == culto_id)
        )
        
        db.session.commit()
        return jsonify({'success': True, 'message': f'{count} escala(s) removida(s) e repertorio limpo com sucesso!'}), 200
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao excluir escalas: {str(e)}")
        return jsonify({'success': False, 'message': f'Erro interno ao excluir escalas: {str(e)}'}), 500

@app.route('/delete_all_escalas', methods=['POST'])
@login_required
@admin_required
def delete_all_escalas():
    """Remove TODAS as escalas do sistema e limpa todos os repertorios (apenas para admins)."""
    try:
        count = Escala.query.count()
        
        if count == 0:
            return jsonify({'success': False, 'message': 'nao he escalas para excluir'}), 404
        
        # Remover todas as escalas
        Escala.query.delete()
        
        # Limpar tambem TODOS os repertorios de cultos
        db.session.execute(culto_repertorio.delete())
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': f'{count} escala(s) removida(s) e repertorios limpos com sucesso!'}), 200
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao excluir todas as escalas: {str(e)}")
        return jsonify({'success': False, 'message': f'Erro interno ao excluir escalas: {str(e)}'}), 500

@app.route('/limpar_escalas_orfas', methods=['POST'])
@login_required
@admin_required
def limpar_escalas_orfas():
    """Remove escalas que referenciam cultos ou membros que não existem mais."""
    try:
        # Buscar IDs de cultos e membros válidos
        cultos_validos = {c.id for c in Culto.query.all()}
        membros_validos = {m.id for m in Member.query.all()}
        
        # Buscar todas as escalas
        todas_escalas = Escala.query.all()
        escalas_removidas = 0
        
        for escala in todas_escalas:
            if escala.culto_id not in cultos_validos or escala.member_id not in membros_validos:
                print(f"[INFO] Removendo escala órfã ID {escala.id}: culto_id={escala.culto_id}, member_id={escala.member_id}")
                db.session.delete(escala)
                escalas_removidas += 1
        
        db.session.commit()
        
        if escalas_removidas > 0:
            return jsonify({
                'success': True, 
                'message': f'{escalas_removidas} escala(s) órfã(s) removida(s) com sucesso!'
            }), 200
        else:
            return jsonify({
                'success': True, 
                'message': 'Nenhuma escala órfã encontrada.'
            }), 200
    except Exception as e:
        db.session.rollback()
        print(f"[ERROR] Erro ao limpar escalas órfãs: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'Erro: {str(e)}'}), 500

@app.route('/get_escala/<int:escala_id>', methods=['GET'])
@login_required
def get_escala(escala_id):
    """Retorna dados de uma escala especefica para edieeo."""
    try:
        escala = db.session.query(Escala, Culto, Member).join(
            Culto, Escala.culto_id == Culto.id
        ).join(
            Member, Escala.member_id == Member.id
        ).filter(Escala.id == escala_id).first()
        
        if not escala:
            return jsonify({'error': 'Escala nao encontrada'}), 404
        
        e, culto, membro = escala
        return jsonify({
            'id': e.id,
            'member_id': membro.id,
            'member_name': membro.name,
            'culto_id': culto.id,
            'culto_name': culto.description,
            'role': e.role,
            'instrument': membro.instrument
        }), 200
    except Exception as e:
        print(f"Erro ao buscar escala: {str(e)}")
        return jsonify({'error': 'Erro ao buscar escala'}), 500

# ========================================
# ROTAS PARA CONFIRMACAO DE PRESENCA
# ========================================

@app.route('/confirmar_presenca/<int:escala_id>', methods=['POST'])
@login_required
def confirmar_presenca(escala_id):
    """Membro confirma que comparecer a escala."""
    try:
        data = request.json
        observacao = data.get('observacao', '') if data else ''
        
        escala = db.session.get(Escala, escala_id)
        if not escala:
            return jsonify({'success': False, 'message': 'Escala não encontrada'}), 404
        
        # Verificar se é o membro da escala
        user = current_user
        if isinstance(user, User):
            member = Member.query.filter_by(email=user.email).first()
        else:
            member = user
        
        if not member or escala.member_id != member.id:
            return jsonify({'success': False, 'message': 'Sem permissão para confirmar esta escala'}), 403
        
        # Atualizar status
        escala.status_confirmacao = 'confirmado'
        escala.data_confirmacao = datetime.utcnow()
        escala.observacao_confirmacao = observacao
        
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': 'Presença confirmada com sucesso!',
            'status': 'confirmado'
        }), 200
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao confirmar presença: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'Erro ao confirmar presença: {str(e)}'}), 500

@app.route('/negar_presenca/<int:escala_id>', methods=['POST'])
@login_required
def negar_presenca(escala_id):
    """Membro informa que não poderá comparecer."""
    try:
        data = request.json
        motivo = data.get('motivo', '') if data else ''
        
        if not motivo or not motivo.strip():
            return jsonify({'success': False, 'message': 'Motivo é obrigatório'}), 400
        
        escala = db.session.get(Escala, escala_id)
        if not escala:
            return jsonify({'success': False, 'message': 'Escala não encontrada'}), 404
        
        # Verificar se é o membro da escala
        user = current_user
        if isinstance(user, User):
            member = Member.query.filter_by(email=user.email).first()
        else:
            member = user
        
        if not member or escala.member_id != member.id:
            return jsonify({'success': False, 'message': 'Sem permissão para modificar esta escala'}), 403
        
        # Atualizar status
        escala.status_confirmacao = 'negado'
        escala.data_confirmacao = datetime.utcnow()
        escala.observacao_confirmacao = motivo
        
        # Criar aviso para notificar admins
        try:
            culto = db.session.get(Culto, escala.culto_id)
            culto_info = f"{culto.description} - {culto.date.strftime('%d/%m/%Y')}" if culto else "Culto"
            
            aviso = Aviso(
                title=f"⚠️ Ausência Confirmada - {member.name}",
                message=f"{member.name} informou que não poderá estar presente no {culto_info} como {escala.role}.\n\nMotivo: {motivo}",
                priority='high',
                created_by=None,  # Sistema
                active=True
            )
            db.session.add(aviso)
        except Exception as notif_error:
            # Não falhar a operação se a notificação falhar
            print(f"Aviso: Não foi possível criar notificação: {notif_error}")
        
        db.session.commit()
        
        # PUSH NOTIFICATION: Notificar administradores sobre ausência
        try:
            culto = db.session.get(Culto, escala.culto_id)
            culto_info = f"{culto.description} em {culto.date.strftime('%d/%m/%Y')}" if culto else "Culto"
            
            # Buscar todos os admins e lideres
            admin_users = User.query.filter(
                (User.role == 'admin') | (User.role.like('%lider%'))
            ).all()
            
            for admin in admin_users:
                # Buscar subscricoes do admin
                subscriptions = PushSubscription.query.filter_by(
                    user_id=admin.id,
                    is_active=True
                ).all()
                
                for sub in subscriptions:
                    send_push_notification(
                        sub,
                        f'⚠️ Ausência Confirmada - {member.name}',
                        f'{member.name} não poderá comparecer ao {culto_info} como {escala.role}',
                        {
                            'type': 'ausencia_confirmada',
                            'url': '/escalas',
                            'escala_id': escala_id,
                            'culto_id': escala.culto_id,
                            'requireInteraction': True
                        }
                    )
        except Exception as e:
            # Não falhar a operação se a notificação falhar
            print(f"Erro ao enviar notificações push aos admins: {e}")
        
        return jsonify({
            'success': True, 
            'message': 'Ausência registrada. O administrador foi notificado.',
            'status': 'negado'
        }), 200
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao negar presença: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'Erro ao registrar ausência: {str(e)}'}), 500

@app.route('/get_status_confirmacoes/<int:culto_id>', methods=['GET'])
@login_required
@admin_required
def get_status_confirmacoes(culto_id):
    """Admin vê status de confirmações de um culto."""
    try:
        escalas = Escala.query.filter_by(culto_id=culto_id).all()
        
        confirmados = 0
        pendentes = 0
        negados = 0
        
        result = []
        for escala in escalas:
            member = Member.query.get(escala.member_id)
            
            result.append({
                'escala_id': escala.id,
                'member_name': member.name if member else 'Desconhecido',
                'role': escala.role,
                'status_confirmacao': escala.status_confirmacao,
                'data_confirmacao': escala.data_confirmacao.strftime('%d/%m/%Y %H:%M') if escala.data_confirmacao else None,
                'observacao': escala.observacao_confirmacao
            })
            
            if escala.status_confirmacao == 'confirmado':
                confirmados += 1
            elif escala.status_confirmacao == 'negado':
                negados += 1
            else:
                pendentes += 1
        
        total = len(escalas)
        percentual_confirmacao = (confirmados / total * 100) if total > 0 else 0
        
        return jsonify({
            'escalas': result,
            'resumo': {
                'total': total,
                'confirmados': confirmados,
                'pendentes': pendentes,
                'negados': negados,
                'percentual_confirmacao': round(percentual_confirmacao, 1)
            }
        }), 200
    except Exception as e:
        print(f"Erro ao buscar status de confirmações: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'escalas': [], 'resumo': {}}), 500

@app.route('/resetar_confirmacoes/<int:culto_id>', methods=['POST'])
@login_required
@admin_required
def resetar_confirmacoes(culto_id):
    """Admin reseta confirmações após o culto (opcional)."""
    try:
        escalas = Escala.query.filter_by(culto_id=culto_id).all()
        
        for escala in escalas:
            escala.status_confirmacao = 'pendente'
            escala.data_confirmacao = None
            escala.observacao_confirmacao = None
        
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': 'Confirmações resetadas com sucesso.'
        }), 200
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao resetar confirmações: {str(e)}")
        return jsonify({'success': False, 'message': f'Erro: {str(e)}'}), 500

# ========================================
# PUSH NOTIFICATIONS
# ========================================

def send_push_notification(subscription_info, title, body, data=None, icon='/static/icon-192x192.png', badge='/static/icon-72x72.png'):
    """
    Envia uma notificação push para um dispositivo inscrito.
    
    Args:
        subscription_info: Objeto PushSubscription do banco ou dict com endpoint, keys
        title: Título da notificação
        body: Corpo da notificação
        data: Dados adicionais (dict)
        icon: Caminho do ícone
        badge: Caminho do badge
    """
    print(f"\n🚀 [PUSH] Iniciando envio de notificação...")
    print(f"   📌 Título: {title}")
    print(f"   📌 Body: {body[:50]}...")
    
    if not VAPID_PRIVATE_KEY or not VAPID_PUBLIC_KEY:
        print("⚠️  VAPID keys não configuradas. Execute: python gerar_vapid_keys.py")
        return False
    
    try:
        # Montar payload da notificação
        payload = {
            'title': title,
            'body': body,
            'icon': icon,
            'badge': badge,
            'vibrate': [200, 100, 200],
            'data': data or {},
            'actions': []
        }
        
        # Adicionar actions personalizadas baseadas no tipo
        if data and 'type' in data:
            if data['type'] == 'nova_escala':
                payload['actions'] = [
                    {'action': 'view', 'title': '👁️ Ver Escala'},
                    {'action': 'confirm', 'title': '✅ Confirmar Presença'}
                ]
            elif data['type'] == 'lembrete_confirmacao':
                payload['actions'] = [
                    {'action': 'confirm', 'title': '✅ Confirmar'},
                    {'action': 'deny', 'title': '❌ Não Poderei'}
                ]
        
        # Preparar subscription dict
        if hasattr(subscription_info, 'endpoint'):
            # É um objeto PushSubscription do banco
            subscription = {
                'endpoint': subscription_info.endpoint,
                'keys': {
                    'p256dh': subscription_info.p256dh_key,
                    'auth': subscription_info.auth_key
                }
            }
            print(f"   🔑 Endpoint: {subscription_info.endpoint[:60]}...")
        else:
            # Já é um dict
            subscription = subscription_info
            print(f"   🔑 Endpoint (dict): {subscription_info.get('endpoint', 'N/A')[:60]}...")
        
        print(f"   📡 Enviando via webpush...")
        
        # Carregar chave VAPID usando from_file (mais confiável que conversão PEM→DER)
        vapid_obj = None
        if VAPID_PRIVATE_KEY and os.path.exists(VAPID_PRIVATE_KEY):
            try:
                # Criar objeto Vapid diretamente do arquivo PEM
                vapid_obj = Vapid.from_file(VAPID_PRIVATE_KEY)
                print(f"   ✅ Objeto Vapid criado de {VAPID_PRIVATE_KEY}")
            except Exception as e:
                print(f"   ❌ Erro ao criar Vapid object: {e}")
                return False
        else:
            print(f"   ❌ VAPID key file não encontrado: {VAPID_PRIVATE_KEY}")
            return False
        
        # Extrair audience (scheme + host + port) do endpoint
        from urllib.parse import urlparse
        parsed_endpoint = urlparse(subscription['endpoint'])
        audience = f"{parsed_endpoint.scheme}://{parsed_endpoint.netloc}"
        
        # Preparar claims VAPID (incluindo 'aud')
        vapid_claims = {
            "sub": VAPID_CLAIMS_EMAIL,
            "aud": audience
        }
        print(f"   🎯 Audience: {audience}")
        
        # Gerar headers VAPID manualmente
        vapid_headers = vapid_obj.sign(vapid_claims)
        print(f"   ✅ VAPID headers gerados: {list(vapid_headers.keys())}")
        
        # Enviar notificação com headers VAPID pré-gerados
        response = webpush(
            subscription_info=subscription,
            data=json.dumps(payload),
            vapid_claims=vapid_claims,
            vapid_private_key=vapid_obj  # Passar objeto Vapid
        )
        
        print(f"   ✅ Resposta: Status {response.status_code}")
        return True
        
    except WebPushException as e:
        print(f"❌ Erro ao enviar push notification: {e}")
        # Se o endpoint retornou 410 (Gone), a subscription expirou
        if e.response and e.response.status_code == 410:
            try:
                # Desativar subscription no banco
                if hasattr(subscription_info, 'endpoint'):
                    sub = PushSubscription.query.filter_by(endpoint=subscription_info.endpoint).first()
                    if sub:
                        sub.is_active = False
                        db.session.commit()
                        print(f"⚠️  Subscription desativada (endpoint expirado): {subscription_info.endpoint[:50]}...")
            except Exception as db_error:
                print(f"Erro ao desativar subscription: {db_error}")
        return False
    except Exception as e:
        print(f"❌ Erro inesperado ao enviar notificação: {e}")
        import traceback
        traceback.print_exc()
        return False

@app.route('/get_vapid_public_key', methods=['GET'])
def get_vapid_public_key():
    """Retorna a chave pública VAPID para o frontend."""
    if not VAPID_PUBLIC_KEY:
        return jsonify({'error': 'VAPID keys não configuradas'}), 500
    return jsonify({'publicKey': VAPID_PUBLIC_KEY}), 200

@app.route('/push_subscribe', methods=['POST'])
@login_required
def push_subscribe():
    """Salva uma inscrição de push notification."""
    try:
        data = request.get_json()
        
        if not data or 'subscription' not in data:
            return jsonify({'success': False, 'message': 'Dados de inscrição inválidos'}), 400
        
        subscription = data['subscription']
        endpoint = subscription.get('endpoint')
        keys = subscription.get('keys', {})
        
        if not endpoint or not keys.get('p256dh') or not keys.get('auth'):
            return jsonify({'success': False, 'message': 'Subscription incompleta'}), 400
        
        # Identificar usuário
        user = current_user
        user_id = user.id if isinstance(user, User) else None
        member_id = None
        
        if isinstance(user, User):
            member = Member.query.filter_by(email=user.email).first()
            member_id = member.id if member else None
        else:
            member_id = user.id
        
        # Verificar se já existe
        existing = PushSubscription.query.filter_by(endpoint=endpoint).first()
        
        if existing:
            # Atualizar existente
            existing.p256dh_key = keys['p256dh']
            existing.auth_key = keys['auth']
            existing.is_active = True
            existing.last_used = datetime.utcnow()
            existing.device_info = request.headers.get('User-Agent', '')[:500]
        else:
            # Criar nova
            new_subscription = PushSubscription(
                user_id=user_id,
                member_id=member_id,
                endpoint=endpoint,
                p256dh_key=keys['p256dh'],
                auth_key=keys['auth'],
                device_info=request.headers.get('User-Agent', '')[:500]
            )
            db.session.add(new_subscription)
        
        db.session.commit()
        
        # Enviar notificação de boas-vindas
        send_push_notification(
            subscription,
            '🔔 Notificações Ativadas!',
            'Você receberá alertas sobre escalas, avisos e confirmações.',
            {'type': 'welcome', 'url': '/'}
        )
        
        return jsonify({
            'success': True,
            'message': 'Inscrição salva com sucesso!'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao salvar subscription: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'Erro: {str(e)}'}), 500

@app.route('/push_unsubscribe', methods=['POST'])
@login_required
def push_unsubscribe():
    """Remove uma inscrição de push notification."""
    try:
        data = request.get_json()
        endpoint = data.get('endpoint')
        
        if not endpoint:
            return jsonify({'success': False, 'message': 'Endpoint não fornecido'}), 400
        
        subscription = PushSubscription.query.filter_by(endpoint=endpoint).first()
        
        if subscription:
            db.session.delete(subscription)
            db.session.commit()
            return jsonify({'success': True, 'message': 'Inscrição removida!'}), 200
        else:
            return jsonify({'success': False, 'message': 'Inscrição não encontrada'}), 404
            
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao remover subscription: {str(e)}")
        return jsonify({'success': False, 'message': f'Erro: {str(e)}'}), 500

@app.route('/push_test', methods=['POST'])
@login_required
def push_test():
    """Envia uma notificação de teste (apenas para usuário atual)."""
    try:
        user = current_user
        user_id = user.id if isinstance(user, User) else None
        member_id = None
        
        # Usar MESMA lógica de detecção do push_subscribe
        if isinstance(user, User):
            member = Member.query.filter_by(email=user.email).first()
            member_id = member.id if member else None
        else:
            member_id = user.id
        
        # DEBUG: Mostrar IDs detectados
        print(f"\n🔍 DEBUG push_test:")
        print(f"   current_user type: {type(user).__name__}")
        print(f"   user_id: {user_id}")
        print(f"   member_id: {member_id}")
        
        # Buscar subscriptions que correspondam a este usuário
        # Busca por user_id OU member_id para cobrir ambos os casos
        from sqlalchemy import or_
        
        query_filters = [PushSubscription.is_active == True]
        user_filters = []
        
        if user_id:
            user_filters.append(PushSubscription.user_id == user_id)
        if member_id:
            user_filters.append(PushSubscription.member_id == member_id)
        
        if user_filters:
            query_filters.append(or_(*user_filters))
            subscriptions = PushSubscription.query.filter(*query_filters).all()
        else:
            subscriptions = []
        
        # DEBUG: Mostrar resultado da query
        print(f"   Subscriptions encontradas: {len(subscriptions)}")
        for sub in subscriptions:
            print(f"   - Sub ID {sub.id}: user_id={sub.user_id}, member_id={sub.member_id}")
        
        if not subscriptions:
            return jsonify({'success': False, 'message': 'Nenhuma inscrição ativa encontrada'}), 404
        
        # Enviar para todas as subscriptions
        sent_count = 0
        for sub in subscriptions:
            success = send_push_notification(
                sub,
                '🧪 Notificação de Teste',
                'Se você está vendo isso, as notificações estão funcionando perfeitamente!',
                {'type': 'test', 'timestamp': datetime.utcnow().isoformat()}
            )
            if success:
                sent_count += 1
        
        return jsonify({
            'success': True,
            'message': f'Notificação de teste enviada para {sent_count} dispositivo(s)!'
        }), 200
        
    except Exception as e:
        print(f"Erro ao enviar notificação de teste: {str(e)}")
        return jsonify({'success': False, 'message': f'Erro: {str(e)}'}), 500

# ========================================
# ROTAS PARA musicas DO CULTO (repertorio)
# ========================================

@app.route('/get_culto_musicas/<int:culto_id>', methods=['GET'])
@login_required
def get_culto_musicas(culto_id):
    """Retorna as musicas selecionadas para um culto especefico."""
    try:
        culto = db.session.get(Culto, culto_id)
        if not culto:
            return jsonify({'error': 'Culto nao encontrado'}), 404
        
        # Buscar musicas do culto com ordem
        musicas_query = db.session.query(Repertorio, culto_repertorio.c.order).join(
            culto_repertorio, Repertorio.id == culto_repertorio.c.repertorio_id
        ).filter(culto_repertorio.c.culto_id == culto_id).order_by(culto_repertorio.c.order)
        
        musicas = [{
            'id': m.id,
            'title': m.title,
            'artist': m.artist,
            'key_tone': m.key_tone,
            'tempo': m.tempo,
            'category': m.category,
            'link_video': m.link_video,
            'link_audio': m.link_audio,
            'audio_file': m.audio_file,
            'order': order
        } for m, order in musicas_query]
        
        return jsonify({'musicas': musicas}), 200
    except Exception as e:
        print(f"Erro ao buscar musicas do culto: {str(e)}")
        return jsonify({'error': 'Erro ao buscar musicas'}), 500

@app.route('/add_musica_culto', methods=['POST'])
@login_required
def add_musica_culto():
    """Adiciona uma musica ao culto. Permitido para Admin/Pastor/Lider e Ministros escalados."""
    data = request.json
    culto_id = data.get('culto_id')
    repertorio_id = data.get('repertorio_id')
    
    if not culto_id or not repertorio_id:
        return jsonify({'success': False, 'message': 'Dados invelidos'}), 400
    
    # Verificar permissao
    if not can_manage_escala_musicas(culto_id, current_user):
        return jsonify({'success': False, 'message': 'Voce nao tem permissao para gerenciar musicas desta escala'}), 403
    
    try:
        culto = db.session.get(Culto, culto_id)
        musica = db.session.get(Repertorio, repertorio_id)
        
        if not culto or not musica:
            return jsonify({'success': False, 'message': 'Culto ou musica nao encontrado'}), 404
        
        # Verificar se je existe
        existe = db.session.query(culto_repertorio).filter_by(
            culto_id=culto_id, 
            repertorio_id=repertorio_id
        ).first()
        
        if existe:
            return jsonify({'success': False, 'message': 'musica je adicionada a este culto'}), 400
        
        # Obter prexima ordem
        max_order = db.session.query(db.func.max(culto_repertorio.c.order)).filter(
            culto_repertorio.c.culto_id == culto_id
        ).scalar() or 0
        
        # Adicionar musica
        stmt = culto_repertorio.insert().values(
            culto_id=culto_id,
            repertorio_id=repertorio_id,
            order=max_order + 1
        )
        db.session.execute(stmt)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'musica adicionada ao culto!'}), 200
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao adicionar musica ao culto: {str(e)}")
        return jsonify({'success': False, 'message': f'Erro: {str(e)}'}), 500

@app.route('/remove_musica_culto', methods=['POST'])
@login_required
def remove_musica_culto():
    """Remove uma musica do culto. Permitido para Admin/Pastor/Lider e Ministros escalados."""
    data = request.json
    culto_id = data.get('culto_id')
    repertorio_id = data.get('repertorio_id')
    
    if not culto_id or not repertorio_id:
        return jsonify({'success': False, 'message': 'Dados invelidos'}), 400
    
    # Verificar permissao
    if not can_manage_escala_musicas(culto_id, current_user):
        return jsonify({'success': False, 'message': 'Voce nao tem permissao para gerenciar musicas desta escala'}), 403
    
    try:
        stmt = culto_repertorio.delete().where(
            db.and_(
                culto_repertorio.c.culto_id == culto_id,
                culto_repertorio.c.repertorio_id == repertorio_id
            )
        )
        db.session.execute(stmt)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'musica removida do culto!'}), 200
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao remover musica do culto: {str(e)}")
        return jsonify({'success': False, 'message': f'Erro: {str(e)}'}), 500

@app.route('/get_estatisticas_musicas', methods=['GET'])
@login_required
@admin_required
def get_estatisticas_musicas():
    """Retorna estatesticas de musicas mais cantadas."""
    try:
        mes = request.args.get('mes', type=int)
        ano = request.args.get('ano', type=int)
        
        # Base query
        query = db.session.query(
            Repertorio.id,
            Repertorio.title,
            Repertorio.artist,
            Repertorio.key_tone,
            db.func.count(culto_repertorio.c.culto_id).label('vezes')
        ).join(
            culto_repertorio, Repertorio.id == culto_repertorio.c.repertorio_id
        ).join(
            Culto, culto_repertorio.c.culto_id == Culto.id
        )
        
        # Aplicar filtros
        if mes and ano:
            query = query.filter(
                db.extract('month', Culto.date) == mes,
                db.extract('year', Culto.date) == ano
            )
        elif ano:
            query = query.filter(db.extract('year', Culto.date) == ano)
        
        # Agrupar e ordenar
        query = query.group_by(
            Repertorio.id,
            Repertorio.title,
            Repertorio.artist,
            Repertorio.key_tone
        ).order_by(db.desc('vezes'))
        
        ranking_completo = [{
            'id': r.id,
            'titulo': r.title,
            'artista': r.artist,
            'tom': r.key_tone,
            'vezes': r.vezes
        } for r in query.all()]
        
        top_10 = ranking_completo[:10]
        
        # Estatesticas gerais
        total_musicas_diferentes = len(ranking_completo)
        
        # Contar cultos no pereodo
        cultos_query = db.session.query(db.func.count(db.distinct(Culto.id)))
        if mes and ano:
            cultos_query = cultos_query.filter(
                db.extract('month', Culto.date) == mes,
                db.extract('year', Culto.date) == ano
            )
        elif ano:
            cultos_query = cultos_query.filter(db.extract('year', Culto.date) == ano)
        
        total_cultos = cultos_query.scalar() or 0
        
        musica_mais_popular = ranking_completo[0]['titulo'] if ranking_completo else None
        
        return jsonify({
            'success': True,
            'top_10': top_10,
            'ranking_completo': ranking_completo,
            'total_musicas_diferentes': total_musicas_diferentes,
            'total_cultos': total_cultos,
            'musica_mais_popular': musica_mais_popular
        }), 200
    except Exception as e:
        print(f"Erro ao buscar estatesticas: {str(e)}")
        return jsonify({'success': False, 'message': f'Erro: {str(e)}'}), 500

@app.route('/reorder_musicas_culto', methods=['POST'])
@login_required
@admin_required
def reorder_musicas_culto():
    """Reordena as musicas de um culto."""
    data = request.json
    culto_id = data.get('culto_id')
    musicas_order = data.get('musicas_order')  # Lista de IDs na nova ordem
    
    if not culto_id or not musicas_order:
        return jsonify({'success': False, 'message': 'Dados invelidos'}), 400
    
    try:
        for index, musica_id in enumerate(musicas_order, 1):
            stmt = culto_repertorio.update().where(
                db.and_(
                    culto_repertorio.c.culto_id == culto_id,
                    culto_repertorio.c.repertorio_id == musica_id
                )
            ).values(order=index)
            db.session.execute(stmt)
        
        db.session.commit()
        return jsonify({'success': True, 'message': 'Ordem das musicas atualizada!'}), 200
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao reordenar musicas: {str(e)}")
        return jsonify({'success': False, 'message': f'Erro: {str(e)}'}), 500

# Rotas para carregar dados dinemicos
@app.route('/get_user_data', methods=['GET'])
@login_required
def get_user_data():
    """Carrega dados do Usuario logado (User ou Member), priorizando o nome do membro."""
    # Usa current_user do Flask-Login, que je interpreta os prefixos corretamente
    user = current_user
    
    if not user or not user.is_authenticated:
        return jsonify({'logged_in': False})
    
    # Determina o nome e role
    if isinstance(user, User):
        # Para um User (admin), tenta encontrar o Member associado pelo email
        member = Member.query.filter_by(email=user.email).first()
        name = member.name if member else user.email.split('@')[0]
        role = ROLE_ADMIN
    else:  # Member
        name = user.name
        role = user.role if hasattr(user, 'role') else ROLE_MEMBRO
    
    print(f"User data: {name}, role: {role}, is_admin: {isinstance(user, User)}")  # Depuraeeo
    
    # Obter avatar
    avatar = getattr(user, 'avatar', 'default-avatar.png') or 'default-avatar.png'
    
    return jsonify({
        'logged_in': True,
        'name': name,
        'email': user.email,
        'role': role,
        'instrument': user.instrument if hasattr(user, 'instrument') and user.instrument else 'N/A',
        'phone': user.phone if hasattr(user, 'phone') and user.phone else 'N/A',
        'is_admin': isinstance(user, User),
        'avatar': avatar
    })

@app.route('/get_announcements', methods=['GET'])
@login_required
def get_announcements():
    """Carrega avisos ativos para a pegina inicial."""
    try:
        announcements = Aviso.query.filter_by(active=True).order_by(Aviso.created_at.desc()).limit(5).all()
        return jsonify([{
            'id': aviso.id,
            'title': aviso.title,
            'text': aviso.message,
            'priority': aviso.priority,
            'created_at': aviso.created_at.strftime('%Y-%m-%d %H:%M')
        } for aviso in announcements])
    except:
        # Fallback para avisos simulados se houver erro
        return jsonify([
            {"title": "Bem-vindo!", "text": "Ensaio geral marcado para sexta-feira es 19h."},
            {"title": "Novo Recurso", "text": "Novo repertorio dispoNivel no app!"}
        ])

@app.route('/get_user_scales', methods=['GET'])
@login_required
def get_user_scales():
    """Carrega as escalas do Usuario logado (User ou Member)."""
    with db.session.no_autoflush:
        user = current_user
        member = Member.query.filter_by(email=user.email).first() if isinstance(user, User) else user
        if member:
            escalas = Escala.query.join(Culto).filter(Escala.member_id == member.id).all()
            return jsonify([{
                'culto': {
                    'date': escala.culto.date.strftime('%Y-%m-%d'),
                    'time': escala.culto.time.strftime('%H:%M'),
                    'description': escala.culto.description
                },
                'role': escala.role
            } for escala in escalas])
    return jsonify([]), 200

@app.route('/get_cult_calendar', methods=['GET'])
@login_required
def get_cult_calendar():
    """Carrega o calenderio de cultos, ordenado por data."""
    with db.session.no_autoflush:
        cultos = Culto.query.order_by(Culto.date.asc()).all()
    return jsonify([{
        'id': culto.id,
        'date': culto.date.strftime('%Y-%m-%d'),
        'time': culto.time.strftime('%H:%M'),
        'description': culto.description
    } for culto in cultos])

@app.route('/get_membros', methods=['GET'])
@login_required
def get_membros():
    """Carrega a lista de membros."""
    with db.session.no_autoflush:
        membros = Member.query.all()
    print(f"Retornando {len(membros)} membros")  # Depuraeeo
    return jsonify([{
        'id': member.id,
        'name': member.name,
        'instrument': member.instrument,
        'email': member.email,
        'phone': member.phone,
        'suspended': member.suspended
    } for member in membros])

@app.route('/submit_feedback', methods=['POST'])
@login_required
def submit_feedback():
    """Processa feedback enviado pelo Usuario."""
    data = request.json
    feedback_text = data.get('feedback')
    feedback_type = data.get('type', 'feedback')
    
    with db.session.no_autoflush:
        user = current_user
    user_email = user.email
    user_id = user.id

    if feedback_text and user_email:
        try:
            novo_feedback = Feedback(
                user_id=user_id,
                email=user_email,
                message=feedback_text,
                type=feedback_type
            )
            db.session.add(novo_feedback)
            db.session.commit()
            print(f"Feedback recebido de {user_email}: {feedback_text}")
            return jsonify({'success': True, 'message': 'Feedback enviado com sucesso!'}), 200
        except Exception as e:
            db.session.rollback()
            print(f"Erro ao salvar feedback: {str(e)}")
            return jsonify({'success': False, 'message': f'Erro ao enviar feedback: {str(e)}'}), 500
    return jsonify({'success': False, 'message': 'Erro ao enviar feedback. Tente novamente.'}), 400

@app.route('/get_feedbacks', methods=['GET'])
@login_required
def get_feedbacks():
    """Retorna todos os feedbacks (apenas para admin)."""
    with db.session.no_autoflush:
        user = current_user
    
    if not user.is_admin:
        return jsonify({'error': 'Acesso negado'}), 403
    
    try:
        feedbacks = Feedback.query.order_by(Feedback.created_at.desc()).all()
        feedbacks_list = []
        
        for fb in feedbacks:
            # Buscar informaeees do membro pelo email
            member = Member.query.filter_by(email=fb.email).first()
            member_name = member.name if member else 'Usuario nao encontrado'
            member_role = member.instrument if (member and member.instrument) else 'Membro'
            
            feedbacks_list.append({
                'id': fb.id,
                'email': fb.email,
                'member_name': member_name,
                'member_role': member_role,
                'message': fb.message,
                'type': fb.type,
                'status': fb.status,
                'created_at': fb.created_at.strftime('%d/%m/%Y %H:%M') if fb.created_at else '',
                'response': fb.response,
                'responded_at': fb.responded_at.strftime('%d/%m/%Y %H:%M') if fb.responded_at else None
            })
        
        return jsonify({'feedbacks': feedbacks_list}), 200
    except Exception as e:
        print(f"Erro ao buscar feedbacks: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/get_my_feedbacks', methods=['GET'])
@login_required
def get_my_feedbacks():
    """Retorna os feedbacks do Usuario logado."""
    with db.session.no_autoflush:
        user = current_user
    
    try:
        # Buscar feedbacks do Usuario pelo email
        feedbacks = Feedback.query.filter_by(email=user.email).order_by(Feedback.created_at.desc()).all()
        feedbacks_list = []
        
        for fb in feedbacks:
            feedbacks_list.append({
                'id': fb.id,
                'message': fb.message,
                'type': fb.type,
                'status': fb.status,
                'created_at': fb.created_at.strftime('%d/%m/%Y %H:%M') if fb.created_at else '',
                'response': fb.response,
                'responded_at': fb.responded_at.strftime('%d/%m/%Y %H:%M') if fb.responded_at else None
            })
        
        return jsonify({'feedbacks': feedbacks_list}), 200
    except Exception as e:
        print(f"Erro ao buscar meus feedbacks: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/respond_feedback/<int:feedback_id>', methods=['POST'])
@login_required
def respond_feedback(feedback_id):
    """Responde a um feedback (apenas para admin)."""
    with db.session.no_autoflush:
        user = current_user
    
    if not user.is_admin:
        return jsonify({'error': 'Acesso negado'}), 403
    
    data = request.json
    response_text = data.get('response')
    new_status = data.get('status', 'reviewed')
    
    if not response_text:
        return jsonify({'success': False, 'message': 'Resposta e obrigateria'}), 400
    
    try:
        feedback = db.session.get(Feedback, feedback_id)
        if not feedback:
            return jsonify({'success': False, 'message': 'Feedback nao encontrado'}), 404
        
        feedback.response = response_text
        feedback.responded_at = datetime.utcnow()
        feedback.responded_by = user.id
        feedback.status = new_status
        
        db.session.commit()
        
        # TODO: Enviar email para o Usuario com a resposta
        
        return jsonify({'success': True, 'message': 'Resposta enviada com sucesso!'}), 200
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao responder feedback: {str(e)}")
        return jsonify({'success': False, 'message': f'Erro: {str(e)}'}), 500

@app.route('/update_feedback_status/<int:feedback_id>', methods=['POST'])
@login_required
def update_feedback_status(feedback_id):
    """Atualiza o status de um feedback (apenas para admin)."""
    with db.session.no_autoflush:
        user = current_user
    
    if not user.is_admin:
        return jsonify({'error': 'Acesso negado'}), 403
    
    data = request.json
    new_status = data.get('status')
    
    if not new_status:
        return jsonify({'success': False, 'message': 'Status e obrigaterio'}), 400
    
    try:
        feedback = db.session.get(Feedback, feedback_id)
        if not feedback:
            return jsonify({'success': False, 'message': 'Feedback nao encontrado'}), 404
        
        feedback.status = new_status
        db.session.commit()
        
        print(f"? Status do feedback {feedback_id} atualizado para: {new_status}")
        return jsonify({'success': True, 'message': 'Status atualizado com sucesso!'}), 200
    except Exception as e:
        db.session.rollback()
        print(f"? Erro ao atualizar status: {str(e)}")
        return jsonify({'success': False, 'message': f'Erro: {str(e)}'}), 500

@app.route('/edit_feedback/<int:feedback_id>', methods=['POST'])
@login_required
def edit_feedback(feedback_id):
    """Edita a resposta de um feedback (apenas para admin)."""
    with db.session.no_autoflush:
        user = current_user
    
    if not user.is_admin:
        return jsonify({'error': 'Acesso negado'}), 403
    
    data = request.json
    new_response = data.get('response')
    new_status = data.get('status')
    
    if not new_response:
        return jsonify({'success': False, 'message': 'Resposta e obrigateria'}), 400
    
    try:
        feedback = db.session.get(Feedback, feedback_id)
        if not feedback:
            return jsonify({'success': False, 'message': 'Feedback nao encontrado'}), 404
        
        feedback.response = new_response
        if new_status:
            feedback.status = new_status
        feedback.responded_at = datetime.utcnow()
        feedback.responded_by = user.id
        
        db.session.commit()
        
        print(f"?? Feedback {feedback_id} editado por admin {user.email}")
        return jsonify({'success': True, 'message': 'Feedback editado com sucesso!'}), 200
    except Exception as e:
        db.session.rollback()
        print(f"? Erro ao editar feedback: {str(e)}")
        return jsonify({'success': False, 'message': f'Erro: {str(e)}'}), 500

@app.route('/delete_feedback/<int:feedback_id>', methods=['DELETE', 'POST'])
@login_required
def delete_feedback(feedback_id):
    """Deleta um feedback (apenas para admin)."""
    with db.session.no_autoflush:
        user = current_user
    
    if not user.is_admin:
        return jsonify({'error': 'Acesso negado'}), 403
    
    try:
        feedback = db.session.get(Feedback, feedback_id)
        if not feedback:
            return jsonify({'success': False, 'message': 'Feedback nao encontrado'}), 404
        
        db.session.delete(feedback)
        db.session.commit()
        
        print(f"??? Feedback {feedback_id} deletado por admin {user.email}")
        return jsonify({'success': True, 'message': 'Feedback deletado com sucesso!'}), 200
    except Exception as e:
        db.session.rollback()
        print(f"? Erro ao deletar feedback: {str(e)}")
        return jsonify({'success': False, 'message': f'Erro: {str(e)}'}), 500

# ========================================
# ROTAS PARA substituicao DE ESCALAS
# ========================================
@app.route('/substituicoes')
@login_required
def substituicoes():
    """Pegina de substituieees de escalas."""
    return render_template('substituicoes.html')

@app.route('/get_minhas_escalas_substituiveis', methods=['GET'])
@login_required
def get_minhas_escalas_substituiveis():
    """Retorna as escalas do membro logado que podem ser substituedas."""
    try:
        # Obter member_id correto (User ou Member)
        user = current_user
        if isinstance(user, User):
            member = Member.query.filter_by(email=user.email).first()
            if not member:
                return jsonify([]), 200
            member_id = member.id
        else:
            member_id = user.id
        
        # Buscar escalas futuras do membro
        escalas = db.session.query(Escala, Culto).join(
            Culto, Escala.culto_id == Culto.id
        ).filter(
            Escala.member_id == member_id,
            Culto.date >= date.today()
        ).order_by(Culto.date, Culto.time).all()
        
        escalas_list = []
        for escala, culto in escalas:
            # Verificar se je tem substituicao pendente ou aceita
            sub_existente = Substituicao.query.filter_by(
                escala_id=escala.id,
                status='pendente'
            ).first() or Substituicao.query.filter_by(
                escala_id=escala.id,
                status='aceito'
            ).first()
            
            # Verificar se o culto je passou
            culto_datetime = datetime.combine(culto.date, culto.time)
            ja_passou = culto_datetime < datetime.now()
            
            escalas_list.append({
                'id': escala.id,
                'culto_id': culto.id,
                'culto_data': culto.date.strftime('%d/%m/%Y'),
                'culto_hora': culto.time.strftime('%H:%M'),
                'culto_descricao': culto.description,
                'funcao': escala.role,
                'tem_substituicao': sub_existente is not None,
                'ja_passou': ja_passou,
                'substituicao_status': sub_existente.status if sub_existente else None
            })
        
        return jsonify(escalas_list), 200
    except Exception as e:
        print(f"? Erro ao buscar escalas substitueveis: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/get_membros_mesma_funcao/<int:escala_id>', methods=['GET'])
@login_required
def get_membros_mesma_funcao(escala_id):
    """Retorna membros do mesmo instrumento/funcao que podem substituir."""
    try:
        escala = db.session.get(Escala, escala_id)
        if not escala:
            return jsonify({'error': 'Escala nao encontrada'}), 404
        
        # Buscar membros com o mesmo instrumento, exceto o solicitante
        funcao = escala.role
        member_id = current_user.id
        
        # Extrair apenas o instrumento base (sem "Principal", "Base", etc)
        funcao_base = funcao.split()[0] if funcao else ''
        
        membros = Member.query.filter(
            Member.id != member_id,
            Member.suspended == False,
            Member.instrument.like(f'%{funcao_base}%')
        ).all()
        
        membros_list = [{
            'id': m.id,
            'name': m.name,
            'instrument': m.instrument
        } for m in membros]
        
        return jsonify(membros_list), 200
    except Exception as e:
        print(f"? Erro ao buscar membros: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/solicitar_substituicao', methods=['POST'])
@login_required
def solicitar_substituicao():
    """Cria uma solicitaeeo de substituicao."""
    try:
        data = request.get_json()
        escala_id = data.get('escala_id')
        membro_substituto_id = data.get('membro_substituto_id')
        mensagem = data.get('mensagem', '')
        
        # Obter member_id correto (User ou Member)
        user = current_user
        if isinstance(user, User):
            member = Member.query.filter_by(email=user.email).first()
            if not member:
                return jsonify({'success': False, 'message': 'Membro nao encontrado'}), 404
            member_id = member.id
        else:
            member_id = user.id
        
        # Validaeees
        escala = db.session.get(Escala, escala_id)
        if not escala:
            return jsonify({'success': False, 'message': 'Escala nao encontrada'}), 404
        
        if escala.member_id != member_id:
            return jsonify({'success': False, 'message': 'Voce nao esta nesta escala'}), 403
        
        # Verificar se je existe substituicao pendente ou aceita
        sub_existente = Substituicao.query.filter_by(
            escala_id=escala_id
        ).filter(
            Substituicao.status.in_(['pendente', 'aceito'])
        ).first()
        
        if sub_existente:
            return jsonify({'success': False, 'message': 'Je existe uma substituicao para esta escala'}), 400
        
        # Criar substituicao
        substituicao = Substituicao(
            escala_id=escala_id,
            membro_solicitante_id=member_id,
            membro_substituto_id=membro_substituto_id,
            mensagem=mensagem,
            status='pendente'
        )
        
        db.session.add(substituicao)
        db.session.commit()
        
        print(f"? substituicao solicitada: Escala {escala_id}, Substituto {membro_substituto_id}")
        return jsonify({'success': True, 'message': 'Solicitacao enviada com sucesso!'}), 200
    except Exception as e:
        db.session.rollback()
        print(f"? Erro ao solicitar substituicao: {str(e)}")
        return jsonify({'success': False, 'message': f'Erro: {str(e)}'}), 500

@app.route('/get_substituicoes_pendentes', methods=['GET'])
@login_required
def get_substituicoes_pendentes():
    """Retorna substituieees pendentes para o membro logado."""
    try:
        # Obter member_id correto (User ou Member)
        user = current_user
        if isinstance(user, User):
            member = Member.query.filter_by(email=user.email).first()
            if not member:
                return jsonify([]), 200
            member_id = member.id
        else:
            member_id = user.id
        
        substituicoes = db.session.query(Substituicao, Escala, Culto, Member).join(
            Escala, Substituicao.escala_id == Escala.id
        ).join(
            Culto, Escala.culto_id == Culto.id
        ).join(
            Member, Substituicao.membro_solicitante_id == Member.id
        ).filter(
            Substituicao.membro_substituto_id == member_id,
            Substituicao.status == 'pendente'
        ).order_by(Culto.date, Culto.time).all()
        
        subs_list = []
        for sub, escala, culto, solicitante in substituicoes:
            # Verificar se o culto je passou
            culto_datetime = datetime.combine(culto.date, culto.time)
            ja_passou = culto_datetime < datetime.now()
            
            subs_list.append({
                'id': sub.id,
                'culto_data': culto.date.strftime('%d/%m/%Y'),
                'culto_hora': culto.time.strftime('%H:%M'),
                'culto_descricao': culto.description,
                'funcao': escala.role,
                'solicitante_nome': solicitante.name,
                'mensagem': sub.mensagem,
                'criado_em': sub.criado_em.strftime('%d/%m/%Y %H:%M'),
                'ja_passou': ja_passou
            })
        
        return jsonify(subs_list), 200
    except Exception as e:
        print(f"? Erro ao buscar substituieees pendentes: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/responder_substituicao/<int:sub_id>', methods=['POST'])
@login_required
def responder_substituicao(sub_id):
    """Aceita ou recusa uma solicitaeeo de substituicao."""
    try:
        # Obter member_id correto (User ou Member)
        user = current_user
        if isinstance(user, User):
            member = Member.query.filter_by(email=user.email).first()
            if not member:
                return jsonify({'success': False, 'message': 'Membro nao encontrado'}), 404
            member_id = member.id
        else:
            member_id = user.id
        
        data = request.get_json()
        acao = data.get('acao')  # 'aceitar' ou 'recusar'
        resposta_msg = data.get('resposta', '')
        
        substituicao = db.session.get(Substituicao, sub_id)
        if not substituicao:
            return jsonify({'success': False, 'message': 'substituicao nao encontrada'}), 404
        
        if substituicao.membro_substituto_id != member_id:
            return jsonify({'success': False, 'message': 'Voce nao pode responder esta solicitaeeo'}), 403
        
        if substituicao.status != 'pendente':
            return jsonify({'success': False, 'message': 'Esta solicitaeeo je foi respondida'}), 400
        
        # Atualizar status
        if acao == 'aceitar':
            substituicao.status = 'aceito'
            # Atualizar a escala original para apontar para o substituto
            escala = db.session.get(Escala, substituicao.escala_id)
            escala.member_id = substituicao.membro_substituto_id
        else:
            substituicao.status = 'recusado'
        
        substituicao.resposta = resposta_msg
        substituicao.respondido_em = datetime.utcnow()
        
        db.session.commit()
        
        member_name = member.name if isinstance(user, User) else user.name
        print(f"? substituicao {sub_id} {acao}(a) por {member_name}")
        return jsonify({'success': True, 'message': f'Substituicao {acao}(a) com sucesso!'}), 200
    except Exception as e:
        db.session.rollback()
        print(f"? Erro ao responder substituicao: {str(e)}")
        return jsonify({'success': False, 'message': f'Erro: {str(e)}'}), 500

@app.route('/get_todas_substituicoes_admin', methods=['GET'])
@login_required
@admin_required
def get_todas_substituicoes_admin():
    """Retorna todas as substituieees para o painel admin."""
    try:
        substituicoes = db.session.query(Substituicao, Escala, Culto, Member, Member).join(
            Escala, Substituicao.escala_id == Escala.id
        ).join(
            Culto, Escala.culto_id == Culto.id
        ).join(
            Member, Substituicao.membro_solicitante_id == Member.id
        ).join(
            Member, Substituicao.membro_substituto_id == Member.id,
            aliased=True
        ).order_by(Substituicao.criado_em.desc()).all()
        
        subs_list = []
        for sub, escala, culto, solicitante, substituto in substituicoes:
            subs_list.append({
                'id': sub.id,
                'culto_data': culto.date.strftime('%d/%m/%Y'),
                'culto_hora': culto.time.strftime('%H:%M'),
                'culto_descricao': culto.description,
                'funcao': escala.role,
                'solicitante_nome': solicitante.name,
                'substituto_nome': substituto.name,
                'status': sub.status,
                'mensagem': sub.mensagem,
                'resposta': sub.resposta,
                'criado_em': sub.criado_em.strftime('%d/%m/%Y %H:%M'),
                'respondido_em': sub.respondido_em.strftime('%d/%m/%Y %H:%M') if sub.respondido_em else None
            })
        
        return jsonify(subs_list), 200
    except Exception as e:
        print(f"? Erro ao buscar substituieees admin: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/cancelar_substituicao/<int:sub_id>', methods=['POST'])
@login_required
def cancelar_substituicao(sub_id):
    """Cancela uma substituicao pendente (apenas o solicitante pode cancelar)."""
    try:
        # Obter member_id correto (User ou Member)
        user = current_user
        if isinstance(user, User):
            member = Member.query.filter_by(email=user.email).first()
            if not member:
                return jsonify({'success': False, 'message': 'Membro nao encontrado'}), 404
            member_id = member.id
        else:
            member_id = user.id
        
        substituicao = db.session.get(Substituicao, sub_id)
        if not substituicao:
            return jsonify({'success': False, 'message': 'substituicao nao encontrada'}), 404
        
        if substituicao.membro_solicitante_id != member_id:
            return jsonify({'success': False, 'message': 'Voce nao pode cancelar esta solicitaeeo'}), 403
        
        if substituicao.status != 'pendente':
            return jsonify({'success': False, 'message': 'Apenas substituieees pendentes podem ser canceladas'}), 400
        
        substituicao.status = 'cancelado'
        db.session.commit()
        
        member_name = member.name if isinstance(user, User) else user.name
        print(f"? substituicao {sub_id} cancelada por {member_name}")
        return jsonify({'success': True, 'message': 'Substituicao cancelada com sucesso!'}), 200
    except Exception as e:
        db.session.rollback()
        print(f"? Erro ao cancelar substituicao: {str(e)}")
        return jsonify({'success': False, 'message': f'Erro: {str(e)}'}), 500

@app.route('/get_historico_substituicoes', methods=['GET'])
@login_required
def get_historico_substituicoes():
    """Retorna o historico de substituieees do membro atual (solicitadas e recebidas)."""
    try:
        # Obter member_id correto (User ou Member)
        user = current_user
        if isinstance(user, User):
            member = Member.query.filter_by(email=user.email).first()
            if not member:
                return jsonify([]), 200
            member_id = member.id
        else:
            member_id = user.id
        
        # Criar aliases para os dois Members (solicitante e substituto)
        Solicitante = aliased(Member)
        Substituto = aliased(Member)
        
        # Buscar substituieees onde o usuario foi solicitante OU substituto
        substituicoes = db.session.query(Substituicao, Escala, Culto, Solicitante, Substituto).join(
            Escala, Substituicao.escala_id == Escala.id
        ).join(
            Culto, Escala.culto_id == Culto.id
        ).join(
            Solicitante, Substituicao.membro_solicitante_id == Solicitante.id
        ).outerjoin(
            Substituto, Substituicao.membro_substituto_id == Substituto.id
        ).filter(
            db.or_(
                Substituicao.membro_solicitante_id == member_id,
                Substituicao.membro_substituto_id == member_id
            ),
            Substituicao.status.in_(['aceito', 'recusado', 'cancelado'])
        ).order_by(Substituicao.respondido_em.desc()).all()
        
        historico = []
        for sub, escala, culto, solicitante, substituto in substituicoes:
            # Verificar se ja passou
            culto_datetime = datetime.combine(culto.date, culto.time)
            ja_passou = culto_datetime < datetime.now()
            
            historico.append({
                'id': sub.id,
                'culto_data': culto.date.strftime('%d/%m/%Y'),
                'culto_hora': culto.time.strftime('%H:%M'),
                'culto_descricao': culto.description,
                'funcao': escala.role,
                'solicitante_nome': solicitante.name,
                'substituto_nome': substituto.name if substituto else 'N/A',
                'status': sub.status,
                'mensagem': sub.mensagem,
                'resposta': sub.resposta,
                'criado_em': sub.criado_em.strftime('%d/%m/%Y %H:%M'),
                'respondido_em': sub.respondido_em.strftime('%d/%m/%Y %H:%M') if sub.respondido_em else None,
                'eu_solicitei': sub.membro_solicitante_id == member_id,
                'ja_passou': ja_passou
            })
        
        return jsonify(historico), 200
    except Exception as e:
        print(f"? Erro ao buscar historico de substituieees: {str(e)}")
        return jsonify({'error': str(e)}), 500

# ========================================
# ROTAS PARA AVISOS/notificacoes
# ========================================
@app.route('/avisos')
@login_required
def avisos():
    """Pegina de avisos."""
    return render_template('avisos.html')

@app.route('/get_avisos', methods=['GET'])
@login_required
def get_avisos():
    """Carrega todos os avisos ativos."""
    try:
        avisos = Aviso.query.filter_by(active=True).order_by(Aviso.created_at.desc()).all()
        return jsonify([{
            'id': aviso.id,
            'title': aviso.title,
            'message': aviso.message,
            'priority': aviso.priority,
            'created_at': aviso.created_at.strftime('%Y-%m-%d %H:%M')
        } for aviso in avisos]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/add_aviso', methods=['POST'])
@login_required
@admin_required
def add_aviso():
    """Adiciona um novo aviso (apenas admins)."""
    print("\n" + "="*60)
    print("🔔 [ADD_AVISO] Função chamada!")
    print("="*60)
    
    data = request.json
    title = data.get('title')
    message = data.get('message')
    priority = data.get('priority', 'normal')
    
    print(f"📝 Dados recebidos:")
    print(f"   Título: {title}")
    print(f"   Mensagem: {message[:50]}...")
    print(f"   Prioridade: {priority}")
    
    if not all([title, message]):
        return jsonify({'success': False, 'message': 'Tetulo e mensagem seo obrigaterios.'}), 400
    
    try:
        print(f"\n💾 Criando aviso no banco...")
        novo_aviso = Aviso(
            title=title,
            message=message,
            priority=priority,
            created_by=session['user_id']
        )
        db.session.add(novo_aviso)
        db.session.commit()
        print(f"✅ Aviso criado com ID: {novo_aviso.id}")
        
        # PUSH NOTIFICATION: Notificar todos os usuários sobre novo aviso
        try:
            print(f"\n🔔 [AVISO] Tentando enviar notificações push...")
            
            # Buscar todas as subscricoes ativas
            subscriptions = PushSubscription.query.filter_by(is_active=True).all()
            print(f"   📊 Subscriptions ativas encontradas: {len(subscriptions)}")
            
            if subscriptions:
                # Determinar emoji baseado na prioridade
                emoji = '📢'
                if priority == 'high':
                    emoji = '⚠️'
                elif priority == 'urgent':
                    emoji = '🚨'
                
                # Truncar mensagem para preview
                message_preview = message[:100] + ('...' if len(message) > 100 else '')
                
                print(f"   📝 Título: {emoji} {title}")
                print(f"   📝 Preview: {message_preview[:50]}...")
                
                sent_count = 0
                for idx, sub in enumerate(subscriptions, 1):
                    print(f"   📤 Enviando para subscription #{idx} (ID: {sub.id})...")
                    try:
                        success = send_push_notification(
                            sub,
                            f'{emoji} {title}',
                            message_preview,
                            {
                                'type': 'novo_aviso',
                                'url': '/avisos',
                                'aviso_id': novo_aviso.id,
                                'priority': priority,
                                'requireInteraction': priority in ['high', 'urgent']
                            }
                        )
                        if success:
                            sent_count += 1
                            print(f"      ✅ Enviada com sucesso!")
                        else:
                            print(f"      ❌ Falhou (send_push_notification retornou False)")
                    except Exception as sub_error:
                        print(f"      ❌ Erro: {sub_error}")
                
                print(f"   ✅ Total enviadas: {sent_count}/{len(subscriptions)}\n")
            else:
                print(f"   ⚠️ Nenhuma subscription ativa encontrada!\n")
        except Exception as e:
            # Não falhar a criação do aviso se a notificação falhar
            print(f"❌ Erro ao enviar notificações push: {e}")
            import traceback
            traceback.print_exc()
        
        return jsonify({'success': True, 'message': 'Aviso criado com sucesso!'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Erro ao criar aviso: {str(e)}'}), 500

@app.route('/edit_aviso/<int:aviso_id>', methods=['PUT'])
@login_required
@admin_required
def edit_aviso(aviso_id):
    """Edita um aviso existente (apenas admins)."""
    data = request.json
    title = data.get('title')
    message = data.get('message')
    priority = data.get('priority')
    
    if not all([title, message, priority]):
        return jsonify({'success': False, 'message': 'Tetulo, mensagem e prioridade seo obrigaterios.'}), 400
    
    try:
        aviso = db.session.get(Aviso, aviso_id)
        if not aviso:
            return jsonify({'success': False, 'message': 'Aviso nao encontrado'}), 404
        
        aviso.title = title
        aviso.message = message
        aviso.priority = priority
        db.session.commit()
        return jsonify({'success': True, 'message': 'Aviso atualizado com sucesso!'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Erro ao atualizar aviso: {str(e)}'}), 500

@app.route('/delete_aviso/<int:aviso_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_aviso(aviso_id):
    """Remove um aviso (apenas admins)."""
    try:
        aviso = db.session.get(Aviso, aviso_id)
        if not aviso:
            return jsonify({'success': False, 'message': 'Aviso nao encontrado'}), 404
        aviso.active = False  # Desativa ao inves de deletar
        db.session.commit()
        return jsonify({'success': True, 'message': 'Aviso removido com sucesso!'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Erro ao remover aviso: {str(e)}'}), 500

# ========================================
# ROTAS PARA repertorio MUSICAL
# ========================================
@app.route('/repertorio')
@login_required
def repertorio():
    """Pegina de repertorio musical."""
    return render_template('repertorio.html')

@app.route('/get_repertorio', methods=['GET'])
@login_required
def get_repertorio():
    """Carrega todo o repertorio musical."""
    try:
        musicas = Repertorio.query.order_by(Repertorio.title.asc()).all()
        return jsonify({
            'repertorio': [{
                'id': musica.id,
                'title': musica.title,
                'artist': musica.artist,
                'key_tone': musica.key_tone,
                'tempo': musica.tempo,
                'link_video': musica.link_video,
                'link_audio': musica.link_audio,
                'audio_file': musica.audio_file,  # Arquivo local de audio
                'lyrics': musica.lyrics,
                'notes': musica.notes,
                'category': musica.category
            } for musica in musicas]
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/add_musica', methods=['POST'])
@login_required
@admin_required
def add_musica():
    """Adiciona uma nova musica ao repertorio (apenas admins)."""
    # Suporta tanto JSON quanto multipart/form-data (com arquivos)
    if request.is_json:
        data = request.json
    else:
        data = request.form
    
    title = data.get('title')
    artist = data.get('artist')
    key_tone = data.get('key_tone')
    tempo = data.get('tempo')
    link_video = data.get('link_video')
    link_audio = data.get('link_audio')
    lyrics = data.get('lyrics')
    notes = data.get('notes')
    category = data.get('category')
    
    if not title:
        return jsonify({'success': False, 'message': 'Tetulo e obrigaterio.'}), 400
    
    # Processar arquivo de audio se houver
    audio_filename = None
    if 'audio_file' in request.files:
        file = request.files['audio_file']
        if file and file.filename and allowed_audio_file(file.filename):
            # Gerar nome enico para o arquivo
            original_ext = file.filename.rsplit('.', 1)[1].lower()
            audio_filename = f"{secrets.token_hex(8)}_{secure_filename(file.filename)}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], audio_filename)
            file.save(filepath)
    
    try:
        nova_musica = Repertorio(
            title=title,
            artist=artist,
            key_tone=key_tone,
            tempo=tempo,
            link_video=link_video,
            link_audio=link_audio,
            audio_file=audio_filename,  # Arquivo local (VS/playback)
            lyrics=lyrics,
            notes=notes,
            category=category,
            added_by=session['user_id']
        )
        db.session.add(nova_musica)
        db.session.commit()
        return jsonify({'success': True, 'message': 'musica adicionada com sucesso!'}), 200
    except Exception as e:
        db.session.rollback()
        # Se houve erro, remover o arquivo salvo
        if audio_filename:
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], audio_filename)
            if os.path.exists(filepath):
                os.remove(filepath)
        return jsonify({'success': False, 'message': f'Erro ao adicionar musica: {str(e)}'}), 500

@app.route('/update_musica/<int:musica_id>', methods=['POST', 'PUT'])
@login_required
@admin_required
def update_musica(musica_id):
    """Atualiza uma musica do repertorio (apenas admins)."""
    # Aceitar tanto JSON quanto FormData
    if request.is_json:
        data = request.json
    else:
        data = request.form
    
    try:
        musica = db.session.get(Repertorio, musica_id)
        if not musica:
            return jsonify({'success': False, 'message': 'musica nao encontrada'}), 404
        
        # Atualizar campos
        if 'title' in data:
            musica.title = data.get('title')
        if 'artist' in data:
            musica.artist = data.get('artist')
        if 'key_tone' in data:
            musica.key_tone = data.get('key_tone')
        if 'tempo' in data:
            musica.tempo = data.get('tempo')
        if 'link_video' in data:
            musica.link_video = data.get('link_video')
        if 'link_audio' in data:
            musica.link_audio = data.get('link_audio')
        if 'lyrics' in data:
            musica.lyrics = data.get('lyrics')
        if 'notes' in data:
            musica.notes = data.get('notes')
        if 'category' in data:
            musica.category = data.get('category')
        
        # Processar arquivo de audio se houver
        if 'audio_file' in request.files:
            file = request.files['audio_file']
            if file and file.filename and allowed_audio_file(file.filename):
                # Remover arquivo antigo se existir
                if musica.audio_file:
                    old_filepath = os.path.join(app.config['UPLOAD_FOLDER'], musica.audio_file)
                    if os.path.exists(old_filepath):
                        os.remove(old_filepath)
                
                # Salvar novo arquivo
                original_ext = file.filename.rsplit('.', 1)[1].lower()
                audio_filename = f"{secrets.token_hex(8)}_{secure_filename(file.filename)}"
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], audio_filename)
                file.save(filepath)
                musica.audio_file = audio_filename
        
        db.session.commit()
        return jsonify({'success': True, 'message': 'musica atualizada com sucesso!'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Erro ao atualizar musica: {str(e)}'}), 500

@app.route('/delete_musica/<int:musica_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_musica(musica_id):
    """Remove uma musica do repertorio (apenas admins)."""
    try:
        musica = db.session.get(Repertorio, musica_id)
        if not musica:
            return jsonify({'success': False, 'message': 'musica nao encontrada'}), 404
        
        # Remover arquivo de audio se existir
        if musica.audio_file:
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], musica.audio_file)
            if os.path.exists(filepath):
                os.remove(filepath)
        
        db.session.delete(musica)
        db.session.commit()
        return jsonify({'success': True, 'message': 'musica removida com sucesso!'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Erro ao remover musica: {str(e)}'}), 500

@app.route('/uploads/<filename>')
@login_required
def uploaded_file(filename):
    """Serve arquivos de audio do direterio de uploads."""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# ========================================
# ROTAS PARA INDISPONIBILIDADE
# ========================================
@app.route('/indisponibilidade')
@login_required
def indisponibilidade():
    """Pegina de indisponibilidade."""
    return render_template('indisponibilidade.html')

@app.route('/get_periodo_indisponibilidade', methods=['GET'])
@login_required
def get_periodo_indisponibilidade():
    """Verifica se o pereodo de indisponibilidade esta aberto (controlado pelo admin)."""
    try:
        # Buscar configuracao
        config = Configuracao.query.filter_by(chave='indisponibilidade_aberta').first()
        
        if not config:
            # Criar configuracao padrao (fechado)
            config = Configuracao(
                chave='indisponibilidade_aberta',
                valor='false',
                descricao='Controla se membros podem registrar indisponibilidades'
            )
            db.session.add(config)
            db.session.commit()
        
        periodo_aberto = config.valor.lower() == 'true'
        
        if periodo_aberto:
            mensagem = "Pereodo ABERTO! Voce pode registrar suas indisponibilidades."
        else:
            mensagem = "Pereodo FECHADO. Aguarde o administrador abrir o pereodo de registro."
        
        return jsonify({
            'periodo_aberto': periodo_aberto,
            'mensagem': mensagem,
            'atualizado_em': config.atualizado_em.strftime('%d/%m/%Y %H:%M') if config.atualizado_em else None
        }), 200
    except Exception as e:
        print(f"Erro ao verificar pereodo de indisponibilidade: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/toggle_periodo_indisponibilidade', methods=['POST'])
@login_required
@admin_required
def toggle_periodo_indisponibilidade():
    """Abre ou fecha o pereodo de registro de indisponibilidades (apenas admin)."""
    print("[DEBUG] funcao toggle_periodo_indisponibilidade chamada!")
    try:
        # Buscar ou criar configuracao
        config = Configuracao.query.filter_by(chave='indisponibilidade_aberta').first()
        print(f"[DEBUG] Config encontrada: {config}")
        
        if not config:
            print("[DEBUG] Config nao existe, criando nova...")
            config = Configuracao(
                chave='indisponibilidade_aberta',
                valor='false',
                descricao='Controla se membros podem registrar indisponibilidades'
            )
            db.session.add(config)
        
        # Alternar valor
        valor_atual = config.valor.lower()
        novo_valor = 'false' if valor_atual == 'true' else 'true'
        print(f"[DEBUG] Alterando de '{valor_atual}' para '{novo_valor}'")
        
        config.valor = novo_valor
        config.atualizado_em = datetime.utcnow()
        
        db.session.commit()
        print("[DEBUG] Commit realizado com sucesso!")
        
        status = "ABERTO" if novo_valor == 'true' else "FECHADO"
        
        resultado = {
            'success': True,
            'periodo_aberto': novo_valor == 'true',
            'status': status,
            'mensagem': f'Pereodo de indisponibilidade agora esta {status}.'
        }
        print(f"[DEBUG] Retornando: {resultado}")
        
        return jsonify(resultado), 200
    except Exception as e:
        db.session.rollback()
        print(f"[ERROR] Erro ao alternar pereodo: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/get_todas_indisponibilidades_admin', methods=['GET'])
@login_required
@admin_required
def get_todas_indisponibilidades_admin():
    """Retorna todas as indisponibilidades cadastradas (apenas admin)."""
    try:
        indisponibilidades = Indisponibilidade.query.order_by(
            Indisponibilidade.date_start.desc(),
            Indisponibilidade.created_at.desc()
        ).all()
        
        result = []
        for ind in indisponibilidades:
            try:
                # Buscar membro com tratamento de erro
                member_name = 'Membro desconhecido'
                if ind.member_id:
                    member = Member.query.get(ind.member_id)
                    if member:
                        member_name = member.name
                
                # Buscar culto com tratamento de erro
                culto_description = None
                if ind.culto_id:
                    culto = Culto.query.get(ind.culto_id)
                    if culto:
                        culto_description = culto.description
                
                # Formatar pereodo de data
                if ind.date_end and ind.date_end != ind.date_start:
                    date_formatted = f"{ind.date_start.strftime('%d/%m/%Y')} a {ind.date_end.strftime('%d/%m/%Y')}"
                else:
                    date_formatted = ind.date_start.strftime('%d/%m/%Y')
                
                result.append({
                    'id': ind.id,
                    'member_id': ind.member_id,
                    'member_name': member_name,
                    'culto_id': ind.culto_id,
                    'culto_description': culto_description,
                    'date': ind.date_start.strftime('%Y-%m-%d'),
                    'date_formatted': date_formatted,
                    'date_start': ind.date_start.strftime('%Y-%m-%d'),
                    'date_end': ind.date_end.strftime('%Y-%m-%d') if ind.date_end else None,
                    'reason': ind.reason if ind.reason else '',
                    'status': ind.status if ind.status else 'pending',
                    'created_at': ind.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                    'created_at_formatted': ind.created_at.strftime('%d/%m/%Y %H:%M')
                })
            except Exception as e:
                print(f"Erro ao processar indisponibilidade {ind.id}: {str(e)}")
                continue
        
        return jsonify({
            'indisponibilidades': result
        }), 200
    except Exception as e:
        print(f"Erro ao buscar todas as indisponibilidades: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e), 'indisponibilidades': []}), 500

@app.route('/delete_indisponibilidade_admin/<int:indisp_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_indisponibilidade_admin(indisp_id):
    """Exclui uma indisponibilidade (apenas admin)."""
    try:
        indisponibilidade = Indisponibilidade.query.get_or_404(indisp_id)
        
        # Guardar informaeees para log
        member_name = indisponibilidade.member.name if indisponibilidade.member else 'Desconhecido'
        date_str = indisponibilidade.date_start.strftime('%d/%m/%Y')
        
        db.session.delete(indisponibilidade)
        db.session.commit()
        
        print(f"[ADMIN] Indisponibilidade exclueda: {member_name} - {date_str}")
        
        return jsonify({
            'success': True,
            'message': f'Indisponibilidade de {member_name} exclueda com sucesso!'
        }), 200
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao excluir indisponibilidade: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/get_cultos_disponiveis', methods=['GET'])
@login_required
def get_cultos_disponiveis():
    """Retorna cultos futuros para seleeeo de indisponibilidade."""
    try:
        # Buscar cultos a partir de hoje
        cultos_futuros = Culto.query.filter(
            Culto.date >= date.today()
        ).order_by(Culto.date.asc(), Culto.time.asc()).all()
        
        return jsonify({
            'cultos': [{
                'id': culto.id,
                'description': culto.description,
                'date': culto.date.strftime('%Y-%m-%d'),
                'time': culto.time.strftime('%H:%M'),
                'date_formatted': culto.date.strftime('%d/%m/%Y')
            } for culto in cultos_futuros]
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/get_indisponibilidades', methods=['GET'])
@login_required
def get_indisponibilidades():
    """Carrega indisponibilidades do Usuario logado."""
    try:
        user = current_user
        member = Member.query.filter_by(email=user.email).first() if isinstance(user, User) else user
        
        if member:
            indisponibilidades = Indisponibilidade.query.filter_by(member_id=member.id).order_by(Indisponibilidade.created_at.desc()).all()
            
            result = []
            for ind in indisponibilidades:
                item = {
                    'id': ind.id,
                    'data_inicio': ind.date_start.strftime('%Y-%m-%d'),
                    'data_fim': ind.date_end.strftime('%Y-%m-%d') if ind.date_end else None,
                    'motivo': ind.reason or '',
                    'status': ind.status,
                    'resposta_admin': ind.admin_response,
                    'created_at': ind.created_at.isoformat() if ind.created_at else None,
                    'member_name': member.name,
                    'culto_id': ind.culto_id
                }
                
                # Se for indisponibilidade para culto especefico, buscar info do culto
                if ind.culto_id:
                    culto = Culto.query.get(ind.culto_id)
                    if culto:
                        item['culto_description'] = culto.description
                        item['culto_date'] = culto.date.strftime('%d/%m/%Y')
                        item['culto_time'] = culto.time.strftime('%H:%M')
                
                result.append(item)
            
            return jsonify(result), 200
        return jsonify([]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/add_indisponibilidade', methods=['POST'])
@login_required
def add_indisponibilidade():
    """Adiciona uma nova indisponibilidade."""
    try:
        # Verificar se o pereodo de registro esta aberto (controle do admin)
        config = Configuracao.query.filter_by(chave='indisponibilidade_aberta').first()
        if not config or config.valor.lower() != 'true':
            return jsonify({
                'success': False, 
                'message': 'Pereodo fechado! O administrador nao liberou o registro de indisponibilidades no momento.'
            }), 403
        
        data = request.json
        cultos_ids = data.get('cultos_ids', [])  # Lista de IDs de cultos (modo cultos específicos)
        data_inicio = data.get('data_inicio')  # Data início (modo período)
        data_fim = data.get('data_fim')  # Data fim (modo período)
        reason = data.get('motivo')
        
        if not reason or reason.strip() == '':
            return jsonify({'success': False, 'message': 'Motivo e obrigaterio.'}), 400
        
        user = current_user
        member = Member.query.filter_by(email=user.email).first() if isinstance(user, User) else user
        
        if not member:
            return jsonify({'success': False, 'message': 'Membro nao encontrado.'}), 404
        
        indisponibilidades_criadas = 0
        
        # MODO 1: Cultos específicos
        if cultos_ids and len(cultos_ids) > 0:
            # Criar uma indisponibilidade para cada culto selecionado
            for culto_id in cultos_ids:
                # Verificar se o culto existe
                culto = Culto.query.get(culto_id)
                if not culto:
                    continue
                
                # Verificar se je existe indisponibilidade para este culto
                existe = Indisponibilidade.query.filter_by(
                    member_id=member.id,
                    culto_id=culto_id
                ).first()
                
                if existe:
                    continue  # Pular se je existe
                
                # Criar indisponibilidade
                nova_indisponibilidade = Indisponibilidade(
                    member_id=member.id,
                    culto_id=culto_id,
                    date_start=culto.date,
                    date_end=culto.date,
                    reason=reason,
                    status='approved'  # Auto-aprovado pois foi feito no pereodo correto
                )
                db.session.add(nova_indisponibilidade)
                indisponibilidades_criadas += 1
        
        # MODO 2: Período de datas
        elif data_inicio and data_fim:
            from datetime import datetime
            try:
                dt_inicio = datetime.strptime(data_inicio, '%Y-%m-%d').date()
                dt_fim = datetime.strptime(data_fim, '%Y-%m-%d').date()
            except ValueError:
                return jsonify({'success': False, 'message': 'Formato de data invalido.'}), 400
            
            if dt_fim < dt_inicio:
                return jsonify({'success': False, 'message': 'Data fim deve ser maior ou igual à data início.'}), 400
            
            # Buscar todos os cultos neste período
            cultos_no_periodo = Culto.query.filter(
                Culto.date >= dt_inicio,
                Culto.date <= dt_fim
            ).all()
            
            if len(cultos_no_periodo) == 0:
                return jsonify({
                    'success': False, 
                    'message': f'Nenhum culto encontrado no período de {dt_inicio.strftime("%d/%m/%Y")} a {dt_fim.strftime("%d/%m/%Y")}.'
                }), 400
            
            # Criar indisponibilidade para cada culto no período
            for culto in cultos_no_periodo:
                # Verificar se je existe indisponibilidade para este culto
                existe = Indisponibilidade.query.filter_by(
                    member_id=member.id,
                    culto_id=culto.id
                ).first()
                
                if existe:
                    continue  # Pular se je existe
                
                # Criar indisponibilidade
                nova_indisponibilidade = Indisponibilidade(
                    member_id=member.id,
                    culto_id=culto.id,
                    date_start=culto.date,
                    date_end=culto.date,
                    reason=reason,
                    status='approved'
                )
                db.session.add(nova_indisponibilidade)
                indisponibilidades_criadas += 1
        
        else:
            return jsonify({'success': False, 'message': 'Selecione cultos ou informe um período de datas.'}), 400
        
        db.session.commit()
        
        if indisponibilidades_criadas == 0:
            return jsonify({
                'success': False, 
                'message': 'Nenhuma indisponibilidade foi criada. Talvez voce je tenha registrado para esses cultos.'
            }), 400
        
        return jsonify({
            'success': True, 
            'message': f'{indisponibilidades_criadas} indisponibilidade(s) registrada(s) com sucesso!'
        }), 200
    except Exception as e:
        db.session.rollback()
        print(f"[ERROR] Erro ao registrar indisponibilidade: {str(e)}")
        return jsonify({'success': False, 'message': f'Erro ao registrar indisponibilidade: {str(e)}'}), 500

@app.route('/delete_indisponibilidade/<int:ind_id>', methods=['DELETE'])
@login_required
def delete_indisponibilidade(ind_id):
    """Remove uma indisponibilidade."""
    try:
        ind = db.session.get(Indisponibilidade, ind_id)
        if not ind:
            return jsonify({'success': False, 'message': 'Indisponibilidade nao encontrada'}), 404
        
        # Verifica se o Usuario pode deletar (preprio ou admin)
        user = current_user
        member = Member.query.filter_by(email=user.email).first() if isinstance(user, User) else user
        
        if ind.member_id != member.id and not getattr(user, 'is_admin', False):
            return jsonify({'success': False, 'message': 'Sem permissao para deletar esta indisponibilidade'}), 403
        
        db.session.delete(ind)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Indisponibilidade removida com sucesso!'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Erro ao remover indisponibilidade: {str(e)}'}), 500

# ROTAS PARA SOLICITACOES DE EXCECAO
# ========================================
@app.route('/solicitar_excecao', methods=['POST'])
@login_required
@admin_required
def solicitar_excecao():
    """Admin solicita excecao para escalar membro indisponivel."""
    try:
        data = request.json
        member_id = data.get('member_id')
        culto_id = data.get('culto_id')
        indisponibilidade_id = data.get('indisponibilidade_id')
        motivo_solicitacao = data.get('motivo_solicitacao', '').strip()
        
        if not all([member_id, culto_id, motivo_solicitacao]):
            return jsonify({'success': False, 'message': 'Dados invalidos.'}), 400
        
        # Verificar se je existe solicitacao pendente
        solicitacao_existente = SolicitacaoExcecao.query.filter_by(
            member_id=member_id,
            culto_id=culto_id,
            status='pending'
        ).first()
        
        if solicitacao_existente:
            return jsonify({
                'success': False, 
                'message': 'Je existe uma solicitacao pendente para este membro neste culto.'
            }), 400
        
        # Criar nova solicitacao
        nova_solicitacao = SolicitacaoExcecao(
            admin_id=current_user.id,
            member_id=member_id,
            culto_id=culto_id,
            indisponibilidade_id=indisponibilidade_id,
            motivo_solicitacao=motivo_solicitacao,
            status='pending'
        )
        
        db.session.add(nova_solicitacao)
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': 'Solicitacao enviada! O membro receberá a notificacao.'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao solicitar excecao: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/get_minhas_solicitacoes_excecao', methods=['GET'])
@login_required
def get_minhas_solicitacoes_excecao():
    """Retorna solicitacoes de excecao recebidas pelo membro."""
    try:
        user = current_user
        member = Member.query.filter_by(email=user.email).first() if isinstance(user, User) else user
        
        if not member:
            return jsonify([]), 200
        
        solicitacoes = SolicitacaoExcecao.query.filter_by(
            member_id=member.id
        ).order_by(SolicitacaoExcecao.created_at.desc()).all()
        
        result = []
        for sol in solicitacoes:
            admin = User.query.get(sol.admin_id)
            culto = Culto.query.get(sol.culto_id)
            
            result.append({
                'id': sol.id,
                'admin_name': admin.username if admin else 'Administrador',
                'culto_description': culto.description if culto else '',
                'culto_date': culto.date.strftime('%d/%m/%Y') if culto else '',
                'culto_time': culto.time.strftime('%H:%M') if culto else '',
                'motivo_solicitacao': sol.motivo_solicitacao,
                'status': sol.status,
                'resposta_membro': sol.resposta_membro,
                'created_at': sol.created_at.strftime('%d/%m/%Y %H:%M'),
                'respondido_em': sol.respondido_em.strftime('%d/%m/%Y %H:%M') if sol.respondido_em else None
            })
        
        return jsonify(result), 200
        
    except Exception as e:
        print(f"Erro ao buscar solicitacoes: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/responder_solicitacao_excecao/<int:sol_id>', methods=['POST'])
@login_required
def responder_solicitacao_excecao(sol_id):
    """Membro responde (aprova/rejeita) solicitacao de excecao."""
    try:
        data = request.json
        resposta = data.get('resposta')  # 'approved' ou 'rejected'
        resposta_texto = data.get('resposta_texto', '').strip()
        role = data.get('role', 'Ministro')  # Funcao para a escala (se aprovado)
        
        if resposta not in ['approved', 'rejected']:
            return jsonify({'success': False, 'message': 'Resposta invalida.'}), 400
        
        solicitacao = db.session.get(SolicitacaoExcecao, sol_id)
        if not solicitacao:
            return jsonify({'success': False, 'message': 'Solicitacao nao encontrada.'}), 404
        
        # Verificar se o usuario e o membro da solicitacao
        user = current_user
        member = Member.query.filter_by(email=user.email).first() if isinstance(user, User) else user
        
        if not member or solicitacao.member_id != member.id:
            return jsonify({'success': False, 'message': 'Sem permissao.'}), 403
        
        if solicitacao.status != 'pending':
            return jsonify({'success': False, 'message': 'Esta solicitacao je foi respondida.'}), 400
        
        # Atualizar solicitacao
        solicitacao.status = resposta
        solicitacao.resposta_membro = resposta_texto
        solicitacao.respondido_em = datetime.utcnow()
        
        # Se aprovado, criar a escala automaticamente
        if resposta == 'approved':
            # Verificar se je nao foi escalado
            escala_existente = Escala.query.filter_by(
                member_id=solicitacao.member_id,
                culto_id=solicitacao.culto_id
            ).first()
            
            if not escala_existente:
                nova_escala = Escala(
                    member_id=solicitacao.member_id,
                    culto_id=solicitacao.culto_id,
                    role=role
                )
                db.session.add(nova_escala)
        
        db.session.commit()
        
        mensagem = 'Solicitacao aprovada! Voce foi escalado(a).' if resposta == 'approved' else 'Solicitacao recusada.'
        
        return jsonify({'success': True, 'message': mensagem}), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao responder solicitacao: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/get_solicitacoes_excecao_admin', methods=['GET'])
@login_required
@admin_required
def get_solicitacoes_excecao_admin():
    """Admin visualiza todas as solicitacoes de excecao."""
    try:
        solicitacoes = SolicitacaoExcecao.query.order_by(
            SolicitacaoExcecao.created_at.desc()
        ).all()
        
        result = []
        for sol in solicitacoes:
            admin = User.query.get(sol.admin_id)
            member = Member.query.get(sol.member_id)
            culto = Culto.query.get(sol.culto_id)
            
            result.append({
                'id': sol.id,
                'admin_name': admin.username if admin else 'Admin',
                'member_name': member.name if member else 'Membro',
                'culto_description': culto.description if culto else '',
                'culto_date': culto.date.strftime('%d/%m/%Y') if culto else '',
                'culto_time': culto.time.strftime('%H:%M') if culto else '',
                'motivo_solicitacao': sol.motivo_solicitacao,
                'status': sol.status,
                'resposta_membro': sol.resposta_membro,
                'created_at': sol.created_at.strftime('%d/%m/%Y %H:%M'),
                'respondido_em': sol.respondido_em.strftime('%d/%m/%Y %H:%M') if sol.respondido_em else None
            })
       
        return jsonify(result), 200
        
    except Exception as e:
        print(f"Erro ao buscar solicitacoes admin: {str(e)}")
        return jsonify({'error': str(e)}), 500

# ========================================

@app.route('/get_indisponibilidades_admin', methods=['GET'])
@login_required
@admin_required
def get_indisponibilidades_admin():
    """Retorna todas as indisponibilidades para administradores (apenas cultos futuros)."""
    try:
        # Buscar indisponibilidades de cultos futuros
        hoje = date.today()
        
        indisponibilidades = db.session.query(
            Indisponibilidade, Member, Culto
        ).join(
            Member, Indisponibilidade.member_id == Member.id
        ).join(
            Culto, Indisponibilidade.culto_id == Culto.id
        ).filter(
            Culto.date >= hoje,
            Indisponibilidade.status == 'approved'
        ).order_by(
            Culto.date.asc(), Culto.time.asc()
        ).all()
        
        result = []
        for ind, member, culto in indisponibilidades:
            result.append({
                'id': ind.id,
                'member_id': member.id,
                'member_name': member.name,
                'member_instrument': member.instrument,
                'culto_id': culto.id,
                'culto_description': culto.description,
                'culto_date': culto.date.strftime('%Y-%m-%d'),
                'culto_date_formatted': culto.date.strftime('%d/%m/%Y'),
                'culto_time': culto.time.strftime('%H:%M'),
                'motivo': ind.reason or '',
                'created_at': ind.created_at.isoformat() if ind.created_at else None
            })
        
        return jsonify(result), 200
    except Exception as e:
        print(f"[ERROR] Erro ao buscar indisponibilidades admin: {str(e)}")
        return jsonify({'error': str(e)}), 500

# ========================================
# DASHBOARD ADMINISTRATIVO
# ========================================
@app.route('/dashboard')
@login_required
@admin_required
def dashboard():
    """Dashboard administrativo com estatesticas."""
    return render_template('dashboard.html')

@app.route('/estatisticas')
@login_required
@admin_required
def estatisticas():
    """Pegina de estatesticas de musicas."""
    return render_template('estatisticas.html')

@app.route('/get_dashboard_stats', methods=['GET'])
@login_required
@admin_required
def get_dashboard_stats():
    """Retorna estatesticas para o dashboard administrativo."""
    try:
        # Estatesticas gerais - todas exibindo totais cadastrados
        total_membros = Member.query.count()
        membros_ativos = Member.query.filter_by(suspended=False).count()
        total_cultos = Culto.query.count()
        
        # Contagem de escalas com tratamento robusto
        # Contar apenas escalas com culto e membro válidos (mesma lógica de /get_escalas)
        try:
            # Primeiro, contar todas as escalas no banco
            total_escalas_raw = Escala.query.count()
            
            # Depois, contar apenas as válidas (com JOIN)
            total_escalas = db.session.query(Escala).join(
                Culto, Escala.culto_id == Culto.id
            ).join(
                Member, Escala.member_id == Member.id
            ).count()
            
            print(f"[DEBUG] Escalas no banco (total): {total_escalas_raw}")
            print(f"[DEBUG] Escalas válidas (com JOIN): {total_escalas}")
            
            # Se houver diferença, há escalas órfãs
            if total_escalas_raw > total_escalas:
                print(f"[WARNING] Há {total_escalas_raw - total_escalas} escala(s) órfã(s) no banco!")
        except Exception as escala_error:
            print(f"[ERROR] Erro ao contar escalas: {str(escala_error)}")
            import traceback
            traceback.print_exc()
            total_escalas = 0
        
        total_musicas = Repertorio.query.count()
        total_avisos = Aviso.query.filter_by(active=True).count()
        feedbacks_pendentes = Feedback.query.filter_by(status='pending').count()
        
        # NOVO: Contagem de confirmacoes pendentes (apenas cultos futuros)
        confirmacoes_pendentes = db.session.query(Escala).join(
            Culto, Escala.culto_id == Culto.id
        ).filter(
            Escala.status_confirmacao == 'pendente',
            Culto.date >= date.today()
        ).count()
        
        # Membros por instrumento
        membros_por_instrumento = db.session.query(
            Member.instrument, 
            db.func.count(Member.id)
        ).group_by(Member.instrument).all()
        
        # Preximos cultos
        proximos_cultos = Culto.query.filter(
            Culto.date >= date.today()
        ).order_by(Culto.date.asc()).limit(5).all()
        
        # Avisos recentes
        avisos_recentes = Aviso.query.filter_by(active=True).order_by(
            Aviso.created_at.desc()
        ).limit(5).all()
        
        print(f"[DEBUG] Dashboard Stats: Membros={total_membros}, Cultos={total_cultos}, Escalas={total_escalas}, musicas={total_musicas}")
        
        response_data = {
            'total_membros': total_membros,
            'membros_ativos': total_membros,  # Mostrar total cadastrado na home
            'total_cultos': total_cultos,
            'total_escalas': total_escalas,
            'total_musicas': total_musicas,
            'total_avisos': total_avisos,
            'feedbacks_pendentes': feedbacks_pendentes,
            'confirmacoes_pendentes': confirmacoes_pendentes,  # NOVO
            'membros_por_instrumento': [{
                'instrumento': inst or 'nao definido',
                'quantidade': qtd
            } for inst, qtd in membros_por_instrumento],
            'proximos_cultos': [{
                'date': culto.date.strftime('%Y-%m-%d'),
                'time': culto.time.strftime('%H:%M'),
                'description': culto.description
            } for culto in proximos_cultos],
            'avisos_recentes': [{
                'title': aviso.title,
                'message': aviso.message,
                'priority': aviso.priority,
                'created_at': aviso.created_at.strftime('%Y-%m-%d %H:%M')
            } for aviso in avisos_recentes]
        }
        
        response = jsonify(response_data)
        # Garantir que não seja cacheado
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response, 200
    except Exception as e:
        print(f"[ERROR] Dashboard stats error: {str(e)}")
        import traceback
        traceback.print_exc()
        # Retornar valores padrão em caso de erro
        return jsonify({
            'total_membros': 0,
            'membros_ativos': 0,
            'total_cultos': 0,
            'total_escalas': 0,
            'total_musicas': 0,
            'total_avisos': 0,
            'feedbacks_pendentes': 0,
            'membros_por_instrumento': [],
            'proximos_cultos': [],
            'avisos_recentes': []
        }), 200

@app.route('/get_ranking_escalas', methods=['GET'])
@login_required
@admin_required
def get_ranking_escalas():
    """Retorna ranking de membros por participaeeo em escalas (mes e ano)."""
    try:
        hoje = date.today()
        periodo = request.args.get('periodo', 'mes')  # 'mes' ou 'ano'
        
        # Definir data de inecio
        if periodo == 'mes':
            data_inicio = date(hoje.year, hoje.month, 1)
        else:  # ano
            data_inicio = date(hoje.year, 1, 1)
        
        # Buscar escalas do pereodo
        escalas_periodo = db.session.query(
            Member.id,
            Member.name,
            Member.instrument,
            db.func.count(Escala.id).label('total_escalas')
        ).join(
            Escala, Member.id == Escala.member_id
        ).join(
            Culto, Escala.culto_id == Culto.id
        ).filter(
            Culto.date >= data_inicio,
            Culto.date <= hoje
        ).group_by(
            Member.id, Member.name, Member.instrument
        ).order_by(
            db.func.count(Escala.id).desc()
        ).all()
        
        # Incluir membros sem escalas
        membros_com_escalas_ids = [e.id for e in escalas_periodo]
        membros_sem_escalas = Member.query.filter(
            ~Member.id.in_(membros_com_escalas_ids),
            Member.suspended == False
        ).all()
        
        resultado = []
        
        # Membros com escalas
        for membro in escalas_periodo:
            resultado.append({
                'id': membro.id,
                'name': membro.name,
                'instrument': membro.instrument,
                'total_escalas': membro.total_escalas
            })
        
        # Membros sem escalas
        for membro in membros_sem_escalas:
            resultado.append({
                'id': membro.id,
                'name': membro.name,
                'instrument': membro.instrument,
                'total_escalas': 0
            })
        
        return jsonify({
            'periodo': periodo,
            'ranking': resultado
        }), 200
        
    except Exception as e:
        print(f"[ERROR] Ranking escalas error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/get_ranking_indisponibilidades', methods=['GET'])
@login_required
@admin_required
def get_ranking_indisponibilidades():
    """Retorna ranking de indisponibilidades por membro e por culto."""
    try:
        hoje = date.today()
        
        # Ranking por membro
        ranking_membros = db.session.query(
            Member.id,
            Member.name,
            Member.instrument,
            db.func.count(Indisponibilidade.id).label('total_indisponibilidades')
        ).join(
            Indisponibilidade, Member.id == Indisponibilidade.member_id
        ).join(
            Culto, Indisponibilidade.culto_id == Culto.id
        ).filter(
            Culto.date >= hoje,
            Indisponibilidade.status == 'approved'
        ).group_by(
            Member.id, Member.name, Member.instrument
        ).order_by(
            db.func.count(Indisponibilidade.id).desc()
        ).limit(10).all()
        
        # Ranking por culto
        ranking_cultos = db.session.query(
            Culto.id,
            Culto.description,
            Culto.date,
            Culto.time,
            db.func.count(Indisponibilidade.id).label('total_indisponibilidades')
        ).join(
            Indisponibilidade, Culto.id == Indisponibilidade.culto_id
        ).filter(
            Culto.date >= hoje,
            Indisponibilidade.status == 'approved'
        ).group_by(
            Culto.id, Culto.description, Culto.date, Culto.time
        ).order_by(
            db.func.count(Indisponibilidade.id).desc()
        ).limit(10).all()
        
        return jsonify({
            'ranking_membros': [{
                'id': m.id,
                'name': m.name,
                'instrument': m.instrument,
                'total': m.total_indisponibilidades
            } for m in ranking_membros],
            'ranking_cultos': [{
                'id': c.id,
                'description': c.description,
                'date': c.date.strftime('%d/%m/%Y'),
                'time': c.time.strftime('%H:%M'),
                'total': c.total_indisponibilidades
            } for c in ranking_cultos]
        }), 200
        
    except Exception as e:
        print(f"[ERROR] Ranking indisponibilidades error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/get_all_feedbacks', methods=['GET'])
@login_required
@admin_required
def get_all_feedbacks():
    """Retorna todos os feedbacks (apenas admins)."""
    try:
        feedbacks = Feedback.query.order_by(Feedback.created_at.desc()).all()
        return jsonify([{
            'id': fb.id,
            'email': fb.email,
            'message': fb.message,
            'type': fb.type,
            'status': fb.status,
            'created_at': fb.created_at.strftime('%Y-%m-%d %H:%M')
        } for fb in feedbacks]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500



# ========================================
# ROTAS PWA - SERVICE WORKER E MANIFEST
# ========================================
@app.route('/sw.js')
def service_worker():
    """Serve o Service Worker da raiz do site."""
    return send_from_directory('static', 'sw.js', mimetype='application/javascript')

@app.route('/manifest.json')
def manifest():
    """Serve o manifest.json da raiz do site."""
    return send_from_directory('static', 'manifest.json', mimetype='application/manifest+json')

# ========================================
# INICIALIZAeeO DO BANCO DE DADOS
# ========================================
# Este cedigo roda tanto em desenvolvimento quanto em producao (Gunicorn)
try:
    ensure_database_exists()
    with app.app_context():
        create_admin()  # Adiciona o administrador padrao
    print("? Aplicaeeo inicializada com sucesso!")
except Exception as e:
    print(f"? ERRO na inicializaeeo: {e}")
    import traceback
    traceback.print_exc()

# ====================================================================
# ENDPOINT TEMPORÁRIO - MIGRAÇÃO DE BANCO DE DADOS
# ====================================================================
@app.route('/admin/migrate-escala-columns', methods=['GET'])
def admin_migrate_escala():
    """
    Endpoint temporário para adicionar colunas de confirmação à tabela escala.
    Acesse: https://appml-tbcw.onrender.com/admin/migrate-escala-columns
    REMOVER APÓS EXECUTAR A MIGRAÇÃO!
    """
    try:
        # Verificar tipo de banco de dados
        db_url = os.environ.get('DATABASE_URL', '')
        is_postgres = 'postgresql' in db_url or 'postgres' in db_url
        
        result = {
            'database': 'PostgreSQL' if is_postgres else 'SQLite',
            'changes': [],
            'errors': [],
            'status': 'success'
        }
        
        with db.engine.begin() as conn:
            # Função para verificar se coluna existe
            def column_exists(table, column):
                if is_postgres:
                    query = db.text("""
                        SELECT column_name 
                        FROM information_schema.columns 
                        WHERE table_name = :table AND column_name = :column
                    """)
                    return conn.execute(query, {'table': table, 'column': column}).fetchone() is not None
                else:
                    info = conn.execute(db.text(f"PRAGMA table_info({table})")).fetchall()
                    return any(row[1] == column for row in info)
            
            # 1. Adicionar status_confirmacao
            if not column_exists('escala', 'status_confirmacao'):
                if is_postgres:
                    conn.execute(db.text(
                        "ALTER TABLE escala ADD COLUMN status_confirmacao VARCHAR(20) DEFAULT 'pendente'"
                    ))
                else:
                    conn.execute(db.text(
                        "ALTER TABLE escala ADD COLUMN status_confirmacao VARCHAR(20) DEFAULT 'pendente'"
                    ))
                result['changes'].append('✅ Coluna status_confirmacao adicionada')
            else:
                result['changes'].append('ℹ️ Coluna status_confirmacao já existe')
            
            # 2. Adicionar data_confirmacao
            if not column_exists('escala', 'data_confirmacao'):
                if is_postgres:
                    conn.execute(db.text(
                        "ALTER TABLE escala ADD COLUMN data_confirmacao TIMESTAMP NULL"
                    ))
                else:
                    conn.execute(db.text(
                        "ALTER TABLE escala ADD COLUMN data_confirmacao DATETIME NULL"
                    ))
                result['changes'].append('✅ Coluna data_confirmacao adicionada')
            else:
                result['changes'].append('ℹ️ Coluna data_confirmacao já existe')
            
            # 3. Adicionar observacao_confirmacao
            if not column_exists('escala', 'observacao_confirmacao'):
                conn.execute(db.text(
                    "ALTER TABLE escala ADD COLUMN observacao_confirmacao TEXT NULL"
                ))
                result['changes'].append('✅ Coluna observacao_confirmacao adicionada')
            else:
                result['changes'].append('ℹ️ Coluna observacao_confirmacao já existe')
            
            # 4. Atualizar registros existentes
            update_result = conn.execute(db.text(
                "UPDATE escala SET status_confirmacao = 'pendente' WHERE status_confirmacao IS NULL"
            ))
            result['changes'].append(f'✅ {update_result.rowcount} escalas atualizadas com status pendente')
            
            # 5. Contar total de escalas
            count = conn.execute(db.text("SELECT COUNT(*) FROM escala")).fetchone()[0]
            result['total_escalas'] = count
            
    except Exception as e:
        result['status'] = 'error'
        result['errors'].append(str(e))
        import traceback
        result['traceback'] = traceback.format_exc()
    
    # Retornar HTML formatado
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Migração de Banco de Dados</title>
        <meta charset="utf-8">
        <style>
            body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; }}
            h1 {{ color: {'#28a745' if result['status'] == 'success' else '#dc3545'}; }}
            .success {{ color: #28a745; }}
            .error {{ color: #dc3545; }}
            .info {{ color: #17a2b8; }}
            pre {{ background: #f4f4f4; padding: 10px; border-radius: 5px; overflow-x: auto; }}
            .box {{ border: 2px solid #ddd; padding: 15px; margin: 10px 0; border-radius: 5px; }}
        </style>
    </head>
    <body>
        <h1>🔄 Migração de Banco de Dados</h1>
        
        <div class="box">
            <h2>Status: <span class="{'success' if result['status'] == 'success' else 'error'}">{result['status'].upper()}</span></h2>
            <p><strong>Banco de Dados:</strong> {result['database']}</p>
            <p><strong>Total de Escalas:</strong> {result.get('total_escalas', 'N/A')}</p>
        </div>
        
        <div class="box">
            <h3>Alterações Realizadas:</h3>
            <ul>
                {''.join([f'<li>{change}</li>' for change in result['changes']])}
            </ul>
        </div>
        
        {f'''
        <div class="box error">
            <h3>❌ Erros:</h3>
            <ul>
                {''.join([f'<li>{error}</li>' for error in result['errors']])}
            </ul>
            <pre>{result.get('traceback', '')}</pre>
        </div>
        ''' if result['errors'] else ''}
        
        <div class="box success">
            <h3>✅ Próximos Passos:</h3>
            <ol>
                <li>Recarregue a página principal do site (Ctrl+F5)</li>
                <li>Verifique se os erros de "column does not exist" sumiram dos logs</li>
                <li><strong>IMPORTANTE:</strong> Remova este endpoint do código após a migração!</li>
            </ol>
        </div>
        
        <p><a href="/">← Voltar para página inicial</a></p>
    </body>
    </html>
    """
    
    return html

if __name__ == '__main__':
    # configuracao de ambiente para execucao local
    port = int(os.environ.get('PORT', 5000))
    debug_mode = os.environ.get('FLASK_ENV', 'development') == 'development'
    
    app.run(host='0.0.0.0', port=port, debug=debug_mode)
