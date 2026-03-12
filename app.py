from flask import Flask, render_template, jsonify, request, redirect, url_for, session, flash, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_required, login_user, logout_user, current_user
from datetime import datetime, date
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import secrets
import os
from functools import wraps  # Importando wraps para decoradores
from dotenv import load_dotenv

# Carrega variáveis de ambiente do arquivo .env
load_dotenv()

# Configuração do Flask
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(16))  # Usa variável de ambiente ou gera uma chave

# Configura o banco de dados SQLite na pasta 'instance'
# Em produção, use DATABASE_URL do ambiente (ex: PostgreSQL do Heroku)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///' + os.path.join(app.instance_path, 'ministry.db'))
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Desativa notificações de modificação para performance
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')  # Pasta para uploads de áudio
app.config['MAX_CONTENT_LENGTH'] = int(os.environ.get('MAX_CONTENT_LENGTH', 50 * 1024 * 1024))  # 50 MB max file size

# Extensões de arquivo permitidas
ALLOWED_AUDIO_EXTENSIONS = {'mp3', 'wav', 'ogg', 'm4a', 'aac', 'flac'}

# Configuração para CSRF (opcional, caso queira usar Flask-WTF)
# Desativando temporariamente para testes, caso o Flask-WTF não esteja instalado
app.config['WTF_CSRF_ENABLED'] = False  # Desativa proteção CSRF temporariamente para testes
app.config['WTF_CSRF_CHECK_DEFAULT'] = False  # Desativa verificação CSRF por padrão temporariamente

# Garante que a pasta 'instance' exista
try:
    os.makedirs(app.instance_path, exist_ok=True)
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)  # Criar pasta de uploads
except OSError as e:
    print(f"Erro ao criar pastas: {e}")

# Função auxiliar para validar extensão de arquivo de áudio
def allowed_audio_file(filename):
    """Verifica se a extensão do arquivo é permitida."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_AUDIO_EXTENSIONS

# Configuração do banco de dados
db = SQLAlchemy(app)

# Configuração do Flask-Login para autenticação
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # Define a rota de login como padrão

# Configuração opcional do Flask-WTF para CSRF
try:
    from flask_wtf.csrf import CSRFProtect
    csrf = CSRFProtect(app)
except ImportError:
    print("Flask-WTF não instalado. Proteção CSRF desativada. Instale com 'pip install flask-wtf' para habilitar.")
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['WTF_CSRF_CHECK_DEFAULT'] = False

# Modelos para o banco de dados
class User(db.Model, UserMixin):
    """Modelo para usuários administradores."""
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)  # Armazena o hash da senha
    is_admin = db.Column(db.Boolean, default=False)

    def set_password(self, password):
        """Define a senha como hash para o usuário."""
        self.password = generate_password_hash(password)

    def check_password(self, password):
        """Verifica se a senha fornecida corresponde ao hash armazenado."""
        return check_password_hash(self.password, password)

class Member(db.Model, UserMixin):
    """Modelo para membros comuns do ministério."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    instrument = db.Column(db.String(120), nullable=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    password = db.Column(db.String(120), nullable=False)  # Armazena o hash da senha para membros
    suspended = db.Column(db.Boolean, default=False)  # Campo para indicar suspensão
    is_admin = db.Column(db.Boolean, default=False)  # Membros nunca são admin (sempre False)

    def set_password(self, password):
        """Define a senha como hash para o membro."""
        self.password = generate_password_hash(password)

    def check_password(self, password):
        """Verifica se a senha fornecida corresponde ao hash armazenado."""
        return check_password_hash(self.password, password)

# Tabela de associação para relacionamento many-to-many entre Culto e Repertorio
culto_repertorio = db.Table('culto_repertorio',
    db.Column('culto_id', db.Integer, db.ForeignKey('culto.id'), primary_key=True),
    db.Column('repertorio_id', db.Integer, db.ForeignKey('repertorio.id'), primary_key=True),
    db.Column('order', db.Integer, default=0)  # Ordem das músicas no culto
)

class Culto(db.Model):
    """Modelo para cultos do ministério."""
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    time = db.Column(db.Time, nullable=False)  # Alterado para db.Time para melhor manipulação
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

    member = db.relationship('Member', backref=db.backref('escalas', lazy=True))
    culto = db.relationship('Culto', backref=db.backref('escalas', lazy=True))

class Aviso(db.Model):
    """Modelo para avisos/notificações do ministério."""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    priority = db.Column(db.String(20), default='normal')  # low, normal, high, urgent
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    active = db.Column(db.Boolean, default=True)

class Repertorio(db.Model):
    """Modelo para repertório musical."""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    artist = db.Column(db.String(120), nullable=True)
    key_tone = db.Column(db.String(20), nullable=True)  # Tom da música (ex: C, D, Em)
    tempo = db.Column(db.String(20), nullable=True)  # Tempo/andamento
    link_video = db.Column(db.String(300), nullable=True)
    link_audio = db.Column(db.String(300), nullable=True)
    audio_file = db.Column(db.String(300), nullable=True)  # Arquivo de áudio local (VS)
    lyrics = db.Column(db.Text, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    category = db.Column(db.String(50), nullable=True)  # louvor, adoração, etc
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
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    admin_response = db.Column(db.Text, nullable=True)  # Resposta do administrador
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    member = db.relationship('Member', backref=db.backref('indisponibilidades', lazy=True))
    culto = db.relationship('Culto', backref=db.backref('indisponibilidades', lazy=True), foreign_keys=[culto_id])

class Feedback(db.Model):
    """Modelo para armazenar feedback dos usuários."""
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

class Configuracao(db.Model):
    """Modelo para configurações do sistema."""
    id = db.Column(db.Integer, primary_key=True)
    chave = db.Column(db.String(100), unique=True, nullable=False)
    valor = db.Column(db.String(200), nullable=False)
    descricao = db.Column(db.String(300), nullable=True)
    atualizado_em = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# Carregar usuário para Flask-Login (suporta tanto User quanto Member)
@login_manager.user_loader
def load_user(user_id):
    """Carrega um usuário ou membro pelo ID para autenticação."""
    with db.session.no_autoflush:  # Evita flush automático durante a sessão
        user = db.session.get(User, int(user_id))
        if not user:
            return db.session.get(Member, int(user_id))
        return user

# Decorador para verificar se o usuário é admin
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            flash('Acesso negado. Somente administradores podem acessar esta página.', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# Criar um administrador padrão
def create_admin():
    """Cria um administrador padrão se não existir."""
    email = "admin@ministeriodelouvor.com"
    password = "admin123"
    with db.session.no_autoflush:
        existing_admin = User.query.filter_by(email=email).first()
        if not existing_admin:
            new_admin = User(email=email)
            new_admin.set_password(password)
            new_admin.is_admin = True
            db.session.add(new_admin)
            db.session.commit()
            print("Administrador criado com sucesso.")
        else:
            print("Administrador já existente.")

# Função para verificar e garantir a criação do banco de dados
def ensure_database_exists():
    """Verifica se o banco de dados existe e o cria, se necessário."""
    db_path = os.path.join(app.instance_path, 'ministry.db')
    if not os.path.exists(db_path):
        with app.app_context():
            db.create_all()
            print(f"Banco de dados 'ministry.db' criado em: {db_path}")
            create_admin()  # Cria o admin imediatamente após criar o banco
    else:
        print(f"Banco de dados 'ministry.db' já existe em: {db_path}")
        # Garantir que todas as tabelas existam (para novos modelos adicionados)
        with app.app_context():
            db.create_all()
            print("Verificação de tabelas concluída.")

# Rotas principais
@app.route('/')
@login_required
def index():
    """Rota para a página inicial."""
    print(f"User is admin: {current_user.is_admin}")  # Depuração para verificar is_admin
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Rota para login de usuários e membros."""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Tenta encontrar o usuário como User ou Member
        with db.session.no_autoflush:
            user = User.query.filter_by(email=email).first()
            if not user:
                user = Member.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            login_user(user)
            session['user_id'] = user.id
            session['is_admin'] = getattr(user, 'is_admin', False)  # Verifica se é admin (só User tem is_admin)
            print(f"Login bem-sucedido para {email}, is_admin: {session['is_admin']}")  # Depuração
            return redirect(url_for('index'))
        flash('Login falhou. Verifique email e senha.', 'error')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    """Rota para logout."""
    logout_user()
    session.pop('user_id', None)
    session.pop('is_admin', None)
    return redirect(url_for('login'))

@app.route('/membros')
@login_required
def membros():
    """Rota para a página de membros."""
    print(f"User is admin in /membros: {current_user.is_admin}")  # Depuração
    return render_template('membros.html')

@app.route('/get_members', methods=['GET'])
@login_required
def get_members():
    """Retorna todos os membros em formato JSON."""
    try:
        # Pegar parâmetro opcional de culto_id para filtrar indisponíveis
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
                'indisponivel': member.id in indisponiveis_ids  # Flag para indicar se está indisponível
            }
            members_list.append(member_data)
        
        return jsonify({'members': members_list})
    except Exception as e:
        print(f"Erro ao carregar membros: {str(e)}")
        return jsonify({'error': str(e), 'members': []}), 500

@app.route('/feedback')
@login_required
def feedback():
    """Rota para a página de feedback."""
    return render_template('feedback.html')

@app.route('/cultos')
@login_required
def cultos():
    """Rota para a página de cultos."""
    with db.session.no_autoflush:
        cultos = Culto.query.order_by(Culto.date.asc()).all()  # Ordena por data ascendente
    return render_template('cultos.html', cultos=cultos)

@app.route('/escalas')
@login_required
def escalas():
    """Rota para a página de escalas gerais (todas as escalas do ministério)."""
    return render_template('escalas.html')

@app.route('/minhas_escalas')
@login_required
def minhas_escalas():
    """Rota para a página de escalas pessoais (apenas escalas onde o usuário está escalado)."""
    return render_template('minhas_escalas.html')

@app.route('/get_escalas', methods=['GET'])
@login_required
def get_escalas():
    """Retorna todas as escalas com informações dos cultos e membros."""
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
            escalas_list.append({
                'escala_id': escala.id,  # ID da escala para edição/exclusão
                'id': escala.id,
                'culto_id': culto.id,
                'culto_name': culto.description,
                'culto_date': date_time_str,
                'member_id': membro.id,
                'member_name': membro.name,
                'role': escala.role,
                'instrument': membro.instrument
            })
        
        return jsonify({'escalas': escalas_list}), 200
    except Exception as e:
        print(f"Erro ao buscar escalas: {str(e)}")
        return jsonify({'escalas': []}), 500

@app.route('/get_minhas_escalas', methods=['GET'])
@login_required
def get_minhas_escalas():
    """Retorna apenas as escalas onde o usuário logado está escalado."""
    try:
        # Identificar o usuário logado
        user = db.session.get(User, session['user_id']) or db.session.get(Member, session['user_id'])
        
        # Buscar o membro correspondente
        if isinstance(user, User):
            member = Member.query.filter_by(email=user.email).first()
        else:
            member = user
        
        if not member:
            return jsonify({'escalas': []}), 200
        
        # Buscar escalas apenas deste membro
        escalas = db.session.query(Escala, Culto, Member).join(
            Culto, Escala.culto_id == Culto.id
        ).join(
            Member, Escala.member_id == Member.id
        ).filter(
            Escala.member_id == member.id
        ).order_by(Culto.date, Culto.time).all()
        
        # Retornar lista plana de escalas
        escalas_list = []
        for escala, culto, membro in escalas:
            date_time_str = f"{culto.date.strftime('%Y-%m-%d')}T{culto.time.strftime('%H:%M')}"
            escalas_list.append({
                'escala_id': escala.id,
                'id': escala.id,
                'culto_id': culto.id,
                'culto_name': culto.description,
                'culto_date': date_time_str,
                'member_id': membro.id,
                'member_name': membro.name,
                'role': escala.role,
                'instrument': membro.instrument
            })
        
        return jsonify({'escalas': escalas_list}), 200
    except Exception as e:
        print(f"Erro ao buscar minhas escalas: {str(e)}")
        return jsonify({'escalas': []}), 500

# Rotas para gerenciar cultos (apenas para admins)
@app.route('/get_cultos', methods=['GET'])
@login_required
def get_cultos():
    """Carrega a lista de cultos, ordenada por data."""
    with db.session.no_autoflush:
        cultos = Culto.query.order_by(Culto.date.asc(), Culto.time.asc()).all()
    print(f"Retornando {len(cultos)} cultos: {[(c.id, c.date, c.time, c.description) for c in cultos]}")  # Depuração
    
    cultos_list = []
    for culto in cultos:
        # Combinar data e hora em um único datetime string
        date_time_str = f"{culto.date.strftime('%Y-%m-%d')}T{culto.time.strftime('%H:%M')}"
        cultos_list.append({
            'id': culto.id,
            'name': culto.description,  # Usar description como name
            'description': culto.description,
            'date': culto.date.strftime('%Y-%m-%d'),
            'time': culto.time.strftime('%H:%M'),
            'date_time': date_time_str  # Campo esperado pelo template
        })
    
    return jsonify({'cultos': cultos_list})

@app.route('/get_culto/<int:culto_id>', methods=['GET'])
@login_required
@admin_required
def get_culto(culto_id):
    """Carrega os dados de um culto específico (apenas para admins)."""
    with db.session.no_autoflush:
        culto = db.session.get(Culto, culto_id)
        if not culto:
            return jsonify({'error': 'Culto não encontrado'}), 404
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
    print(f"Dados recebidos para add_culto: {data}")  # Depuração
    
    name = data.get('name')
    date_time_str = data.get('date_time')
    description = data.get('description', '')
    
    if not all([name, date_time_str]):
        return jsonify({'success': False, 'message': 'Nome e data/hora são obrigatórios.'}), 400
    
    try:
        # Parse date_time no formato ISO: "2026-03-15T19:30"
        date_time_obj = datetime.strptime(date_time_str, '%Y-%m-%dT%H:%M')
        date_obj = date_time_obj.date()
        time_obj = date_time_obj.time()
        
        with db.session.no_autoflush:
            existing_culto = Culto.query.filter_by(date=date_obj, time=time_obj, description=name).first()
            if existing_culto:
                print(f"Culto já existe no banco: ID {existing_culto.id}, Data {existing_culto.date}, Horário {existing_culto.time}, Descrição {existing_culto.description}")  # Depuração
                return jsonify({'success': False, 'message': 'Este culto já existe.'}), 400
        
        novo_culto = Culto(date=date_obj, time=time_obj, description=name)
        db.session.add(novo_culto)
        db.session.commit()
        print(f"Culto cadastrado com sucesso: {novo_culto.id}, {novo_culto.date}, {novo_culto.time}, {novo_culto.description}")  # Depuração
        return jsonify({'success': True, 'message': 'Culto adicionado com sucesso!'}), 200
    except ValueError as ve:
        print(f"Erro de formato nos dados: {str(ve)}")  # Depuração
        return jsonify({'success': False, 'message': f'Data ou horário em formato inválido: {str(ve)}'}), 400
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao salvar culto: {str(e)}")  # Depuração
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
        return jsonify({'success': False, 'message': 'ID, nome e data/hora são obrigatórios.'}), 400
    
    with db.session.no_autoflush:
        culto = db.session.get(Culto, culto_id)
        if not culto:
            return jsonify({'success': False, 'message': 'Culto não encontrado'}), 404
    
    try:
        # Parse date_time no formato ISO: "2026-03-15T19:30"
        date_time_obj = datetime.strptime(date_time_str, '%Y-%m-%dT%H:%M')
        date_obj = date_time_obj.date()
        time_obj = date_time_obj.time()
        
        with db.session.no_autoflush:
            # Verificar se outro culto com mesmas data/hora/nome já existe
            existing = Culto.query.filter(
                Culto.id != culto_id, 
                Culto.date == date_obj, 
                Culto.time == time_obj, 
                Culto.description == name
            ).first()
            if existing:
                return jsonify({'success': False, 'message': 'Outro culto com esses dados já existe.'}), 400
        
        culto.date = date_obj
        culto.time = time_obj
        culto.description = name
        db.session.commit()
        return jsonify({'success': True, 'message': 'Culto atualizado com sucesso!'}), 200
    except ValueError as ve:
        return jsonify({'success': False, 'message': f'Data ou horário em formato inválido: {str(ve)}'}), 400
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
            return jsonify({'success': False, 'message': 'Culto não encontrado'}), 404
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
    print(f"Dados recebidos para add_member: {data}")  # Depuração
    name = data.get('name')
    instrument = data.get('instrument')
    email = data.get('email')
    phone = data.get('phone')
    password = data.get('password', '123456')  # Senha padrão, caso não fornecida
    if not all([name, email]):  # Nome e email são obrigatórios
        return jsonify({'success': False, 'message': 'Nome e email são obrigatórios.'}), 400
    try:
        with db.session.no_autoflush:
            existing_member = Member.query.filter_by(email=email).first()
            if existing_member:
                return jsonify({'success': False, 'message': 'Este email já está cadastrado.'}), 400
        novo_membro = Member(name=name, instrument=instrument, email=email, phone=phone, suspended=False)
        novo_membro.set_password(password)  # Define a senha hashada
        db.session.add(novo_membro)
        db.session.commit()
        print(f"Membro cadastrado com sucesso: {novo_membro.id}, {novo_membro.name}, {novo_membro.email}")  # Depuração
        return jsonify({'success': True, 'message': 'Membro cadastrado com sucesso! A senha padrão é 123456, e o membro pode alterá-la no perfil.'}), 200
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao salvar membro: {str(e)}")  # Depuração
        return jsonify({'success': False, 'message': f'Erro interno ao cadastrar membro: {str(e)}'}), 500

@app.route('/get_member/<int:member_id>', methods=['GET'])
@login_required
@admin_required
def get_member(member_id):
    """Carrega os dados de um membro específico (apenas para admins)."""
    with db.session.no_autoflush:
        member = db.session.get(Member, member_id)
        if not member:
            return jsonify({'error': 'Membro não encontrado'}), 404
    print(f"Retornando dados do membro {member_id}: {member.name}, suspended: {member.suspended}")  # Depuração
    return jsonify({
        'id': member.id,
        'name': member.name,
        'instrument': member.instrument,
        'email': member.email,
        'phone': member.phone,
        'suspended': member.suspended
    })

@app.route('/update_member', methods=['POST'])
@login_required
@admin_required
def update_member():
    """Edita um membro existente (apenas para admins)."""
    data = request.get_json()
    print(f"Recebendo atualização para membro ID {data.get('id')}: {data}")  # Depuração
    if not data or 'id' not in data:
        return jsonify({'success': False, 'message': 'Dados inválidos ou ID ausente'}), 400
    try:
        with db.session.no_autoflush:
            member = db.session.get(Member, data['id'])
            if not member:
                return jsonify({'success': False, 'message': 'Membro não encontrado'}), 404
        member.name = data.get('name', member.name)
        member.instrument = data.get('instrument', member.instrument)
        member.email = data.get('email', member.email)
        member.phone = data.get('phone', member.phone)
        if 'password' in data and data['password']:
            member.set_password(data['password'])
        db.session.commit()
        return jsonify({'success': True, 'message': 'Membro atualizado com sucesso!'})
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao atualizar membro: {str(e)}")  # Depuração
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
                return jsonify({'success': False, 'message': 'Membro não encontrado'}), 404
        print(f"Alterando status de suspensão do membro {member_id}: {member.suspended} -> {not member.suspended}")  # Depuração
        member.suspended = not member.suspended  # Alterna o estado
        db.session.commit()
        return jsonify({'success': True, 'message': f'Membro {member.suspended and "suspenso" or "reativado"} com sucesso!'})
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao suspender/reativar membro: {str(e)}")  # Depuração
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
                return jsonify({'success': False, 'message': 'Membro não encontrado'}), 404
        
        print(f"Excluindo membro {member_id}: {member.name}")  # Depuração
        
        # Deletar registros relacionados primeiro (se as tabelas existirem)
        try:
            # Deletar indisponibilidades relacionadas
            Indisponibilidade.query.filter_by(member_id=member_id).delete()
        except Exception as e:
            print(f"Aviso: Não foi possível deletar indisponibilidades (tabela pode não existir): {e}")
        
        try:
            # Deletar escalas relacionadas
            Escala.query.filter_by(member_id=member_id).delete()
        except Exception as e:
            print(f"Aviso: Não foi possível deletar escalas: {e}")
        
        # Deletar o membro
        db.session.delete(member)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Membro excluído com sucesso!'})
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao excluir membro: {str(e)}")  # Depuração
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
        return jsonify({'success': False, 'message': 'Dados inválidos.'}), 400
    try:
        with db.session.no_autoflush:
            # Verificar se o membro já está escalado
            if Escala.query.filter_by(member_id=member_id, culto_id=culto_id).first():
                return jsonify({'success': False, 'message': 'Este membro já está escalado para este culto.'}), 400
            
            # NOVA VERIFICAÇÃO: Verificar se o membro está indisponível para este culto
            indisponibilidade = Indisponibilidade.query.filter_by(
                member_id=member_id,
                culto_id=culto_id,
                status='approved'
            ).first()
            
            if indisponibilidade:
                member = Member.query.get(member_id)
                member_name = member.name if member else 'Membro'
                return jsonify({
                    'success': False, 
                    'message': f'{member_name} está INDISPONÍVEL para este culto. Motivo: {indisponibilidade.reason}'
                }), 400
        
        nova_escala = Escala(member_id=member_id, culto_id=culto_id, role=role)
        db.session.add(nova_escala)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Escala adicionada com sucesso!'}), 200
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao salvar escala: {str(e)}")  # Depuração
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
        return jsonify({'success': False, 'message': 'Dados inválidos.'}), 400
    
    try:
        with db.session.no_autoflush:
            escala = db.session.get(Escala, escala_id)
            if not escala:
                return jsonify({'success': False, 'message': 'Escala não encontrada'}), 404
            
            # Atualizar campos fornecidos
            if member_id:
                escala.member_id = member_id
            if role:
                escala.role = role
                
            db.session.commit()
        return jsonify({'success': True, 'message': 'Escala atualizada com sucesso!'}), 200
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao editar escala: {str(e)}")  # Depuração
        return jsonify({'success': False, 'message': f'Erro interno ao atualizar escala: {str(e)}'}), 500
        print(f"Erro ao editar escala: {str(e)}")  # Depuração
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
                return jsonify({'success': False, 'message': 'Escala não encontrada'}), 404
        db.session.delete(escala)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Escala removida com sucesso!'}), 200
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao excluir escala: {str(e)}")  # Depuração
        return jsonify({'success': False, 'message': f'Erro interno ao excluir escala: {str(e)}'}), 500

@app.route('/delete_escalas_culto/<int:culto_id>', methods=['POST'])
@login_required
@admin_required
def delete_escalas_culto(culto_id):
    """Remove todas as escalas de um culto específico (apenas para admins)."""
    try:
        escalas = Escala.query.filter_by(culto_id=culto_id).all()
        if not escalas:
            return jsonify({'success': False, 'message': 'Nenhuma escala encontrada para este culto'}), 404
        
        count = len(escalas)
        for escala in escalas:
            db.session.delete(escala)
        
        db.session.commit()
        return jsonify({'success': True, 'message': f'{count} escala(s) removida(s) com sucesso!'}), 200
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao excluir escalas: {str(e)}")
        return jsonify({'success': False, 'message': f'Erro interno ao excluir escalas: {str(e)}'}), 500

@app.route('/delete_all_escalas', methods=['POST'])
@login_required
@admin_required
def delete_all_escalas():
    """Remove TODAS as escalas do sistema (apenas para admins)."""
    try:
        count = Escala.query.count()
        
        if count == 0:
            return jsonify({'success': False, 'message': 'Não há escalas para excluir'}), 404
        
        Escala.query.delete()
        db.session.commit()
        
        return jsonify({'success': True, 'message': f'{count} escala(s) removida(s) com sucesso!'}), 200
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao excluir todas as escalas: {str(e)}")
        return jsonify({'success': False, 'message': f'Erro interno ao excluir escalas: {str(e)}'}), 500

@app.route('/get_escala/<int:escala_id>', methods=['GET'])
@login_required
def get_escala(escala_id):
    """Retorna dados de uma escala específica para edição."""
    try:
        escala = db.session.query(Escala, Culto, Member).join(
            Culto, Escala.culto_id == Culto.id
        ).join(
            Member, Escala.member_id == Member.id
        ).filter(Escala.id == escala_id).first()
        
        if not escala:
            return jsonify({'error': 'Escala não encontrada'}), 404
        
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
# ROTAS PARA MÚSICAS DO CULTO (REPERTÓRIO)
# ========================================

@app.route('/get_culto_musicas/<int:culto_id>', methods=['GET'])
@login_required
def get_culto_musicas(culto_id):
    """Retorna as músicas selecionadas para um culto específico."""
    try:
        culto = db.session.get(Culto, culto_id)
        if not culto:
            return jsonify({'error': 'Culto não encontrado'}), 404
        
        # Buscar músicas do culto com ordem
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
        print(f"Erro ao buscar músicas do culto: {str(e)}")
        return jsonify({'error': 'Erro ao buscar músicas'}), 500

@app.route('/add_musica_culto', methods=['POST'])
@login_required
@admin_required
def add_musica_culto():
    """Adiciona uma música ao culto."""
    data = request.json
    culto_id = data.get('culto_id')
    repertorio_id = data.get('repertorio_id')
    
    if not culto_id or not repertorio_id:
        return jsonify({'success': False, 'message': 'Dados inválidos'}), 400
    
    try:
        culto = db.session.get(Culto, culto_id)
        musica = db.session.get(Repertorio, repertorio_id)
        
        if not culto or not musica:
            return jsonify({'success': False, 'message': 'Culto ou música não encontrado'}), 404
        
        # Verificar se já existe
        existe = db.session.query(culto_repertorio).filter_by(
            culto_id=culto_id, 
            repertorio_id=repertorio_id
        ).first()
        
        if existe:
            return jsonify({'success': False, 'message': 'Música já adicionada a este culto'}), 400
        
        # Obter próxima ordem
        max_order = db.session.query(db.func.max(culto_repertorio.c.order)).filter(
            culto_repertorio.c.culto_id == culto_id
        ).scalar() or 0
        
        # Adicionar música
        stmt = culto_repertorio.insert().values(
            culto_id=culto_id,
            repertorio_id=repertorio_id,
            order=max_order + 1
        )
        db.session.execute(stmt)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Música adicionada ao culto!'}), 200
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao adicionar música ao culto: {str(e)}")
        return jsonify({'success': False, 'message': f'Erro: {str(e)}'}), 500

@app.route('/remove_musica_culto', methods=['POST'])
@login_required
@admin_required
def remove_musica_culto():
    """Remove uma música do culto."""
    data = request.json
    culto_id = data.get('culto_id')
    repertorio_id = data.get('repertorio_id')
    
    if not culto_id or not repertorio_id:
        return jsonify({'success': False, 'message': 'Dados inválidos'}), 400
    
    try:
        stmt = culto_repertorio.delete().where(
            db.and_(
                culto_repertorio.c.culto_id == culto_id,
                culto_repertorio.c.repertorio_id == repertorio_id
            )
        )
        db.session.execute(stmt)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Música removida do culto!'}), 200
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao remover música do culto: {str(e)}")
        return jsonify({'success': False, 'message': f'Erro: {str(e)}'}), 500

@app.route('/get_estatisticas_musicas', methods=['GET'])
@login_required
@admin_required
def get_estatisticas_musicas():
    """Retorna estatísticas de músicas mais cantadas."""
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
        
        # Estatísticas gerais
        total_musicas_diferentes = len(ranking_completo)
        
        # Contar cultos no período
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
        print(f"Erro ao buscar estatísticas: {str(e)}")
        return jsonify({'success': False, 'message': f'Erro: {str(e)}'}), 500

@app.route('/reorder_musicas_culto', methods=['POST'])
@login_required
@admin_required
def reorder_musicas_culto():
    """Reordena as músicas de um culto."""
    data = request.json
    culto_id = data.get('culto_id')
    musicas_order = data.get('musicas_order')  # Lista de IDs na nova ordem
    
    if not culto_id or not musicas_order:
        return jsonify({'success': False, 'message': 'Dados inválidos'}), 400
    
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
        return jsonify({'success': True, 'message': 'Ordem das músicas atualizada!'}), 200
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao reordenar músicas: {str(e)}")
        return jsonify({'success': False, 'message': f'Erro: {str(e)}'}), 500

# Rotas para carregar dados dinâmicos
@app.route('/get_user_data', methods=['GET'])
@login_required
def get_user_data():
    """Carrega dados do usuário logado (User ou Member), priorizando o nome do membro."""
    with db.session.no_autoflush:
        user = db.session.get(User, session['user_id'])
        if not user:
            user = db.session.get(Member, session['user_id'])
        if isinstance(user, User):
            # Para um User (admin), tenta encontrar o Member associado pelo email
            member = Member.query.filter_by(email=user.email).first()
            name = member.name if member else user.email.split('@')[0]  # Usa o nome do member ou o username antes do '@'
        else:  # Membro comum
            name = user.name  # Usa o nome diretamente do Member
    
    print(f"User data: {name}, is_admin: {getattr(user, 'is_admin', False)}")  # Depuração
    return jsonify({
        'logged_in': True,
        'name': name,
        'email': user.email,
        'instrument': user.instrument if hasattr(user, 'instrument') and user.instrument else 'N/A',
        'phone': user.phone if hasattr(user, 'phone') and user.phone else 'N/A',
        'is_admin': getattr(user, 'is_admin', False)
    })

@app.route('/get_announcements', methods=['GET'])
@login_required
def get_announcements():
    """Carrega avisos ativos para a página inicial."""
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
            {"title": "Bem-vindo!", "text": "Ensaio geral marcado para sexta-feira às 19h."},
            {"title": "Novo Recurso", "text": "Novo repertório disponível no app!"}
        ])

@app.route('/get_user_scales', methods=['GET'])
@login_required
def get_user_scales():
    """Carrega as escalas do usuário logado (User ou Member)."""
    with db.session.no_autoflush:
        user = db.session.get(User, session['user_id']) or db.session.get(Member, session['user_id'])
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
    """Carrega o calendário de cultos, ordenado por data."""
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
    print(f"Retornando {len(membros)} membros")  # Depuração
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
    """Processa feedback enviado pelo usuário."""
    data = request.json
    feedback_text = data.get('feedback')
    feedback_type = data.get('type', 'feedback')
    
    with db.session.no_autoflush:
        user = db.session.get(User, session['user_id']) or db.session.get(Member, session['user_id'])
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
        user = db.session.get(User, session['user_id']) or db.session.get(Member, session['user_id'])
    
    if not user.is_admin:
        return jsonify({'error': 'Acesso negado'}), 403
    
    try:
        feedbacks = Feedback.query.order_by(Feedback.created_at.desc()).all()
        feedbacks_list = []
        
        for fb in feedbacks:
            # Buscar informações do membro pelo email
            member = Member.query.filter_by(email=fb.email).first()
            member_name = member.name if member else 'Usuário não encontrado'
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
    """Retorna os feedbacks do usuário logado."""
    with db.session.no_autoflush:
        user = db.session.get(User, session['user_id']) or db.session.get(Member, session['user_id'])
    
    try:
        # Buscar feedbacks do usuário pelo email
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
        user = db.session.get(User, session['user_id']) or db.session.get(Member, session['user_id'])
    
    if not user.is_admin:
        return jsonify({'error': 'Acesso negado'}), 403
    
    data = request.json
    response_text = data.get('response')
    new_status = data.get('status', 'reviewed')
    
    if not response_text:
        return jsonify({'success': False, 'message': 'Resposta é obrigatória'}), 400
    
    try:
        feedback = db.session.get(Feedback, feedback_id)
        if not feedback:
            return jsonify({'success': False, 'message': 'Feedback não encontrado'}), 404
        
        feedback.response = response_text
        feedback.responded_at = datetime.utcnow()
        feedback.responded_by = user.id
        feedback.status = new_status
        
        db.session.commit()
        
        # TODO: Enviar email para o usuário com a resposta
        
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
        user = db.session.get(User, session['user_id']) or db.session.get(Member, session['user_id'])
    
    if not user.is_admin:
        return jsonify({'error': 'Acesso negado'}), 403
    
    data = request.json
    new_status = data.get('status')
    
    if not new_status:
        return jsonify({'success': False, 'message': 'Status é obrigatório'}), 400
    
    try:
        feedback = db.session.get(Feedback, feedback_id)
        if not feedback:
            return jsonify({'success': False, 'message': 'Feedback não encontrado'}), 404
        
        feedback.status = new_status
        db.session.commit()
        
        print(f"✅ Status do feedback {feedback_id} atualizado para: {new_status}")
        return jsonify({'success': True, 'message': 'Status atualizado com sucesso!'}), 200
    except Exception as e:
        db.session.rollback()
        print(f"❌ Erro ao atualizar status: {str(e)}")
        return jsonify({'success': False, 'message': f'Erro: {str(e)}'}), 500

@app.route('/delete_feedback/<int:feedback_id>', methods=['DELETE', 'POST'])
@login_required
def delete_feedback(feedback_id):
    """Deleta um feedback (apenas para admin)."""
    with db.session.no_autoflush:
        user = db.session.get(User, session['user_id']) or db.session.get(Member, session['user_id'])
    
    if not user.is_admin:
        return jsonify({'error': 'Acesso negado'}), 403
    
    try:
        feedback = db.session.get(Feedback, feedback_id)
        if not feedback:
            return jsonify({'success': False, 'message': 'Feedback não encontrado'}), 404
        
        db.session.delete(feedback)
        db.session.commit()
        
        print(f"🗑️ Feedback {feedback_id} deletado por admin {user.email}")
        return jsonify({'success': True, 'message': 'Feedback deletado com sucesso!'}), 200
    except Exception as e:
        db.session.rollback()
        print(f"❌ Erro ao deletar feedback: {str(e)}")
        return jsonify({'success': False, 'message': f'Erro: {str(e)}'}), 500

# ========================================
# ROTAS PARA AVISOS/NOTIFICAÇÕES
# ========================================
@app.route('/avisos')
@login_required
def avisos():
    """Página de avisos."""
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
    data = request.json
    title = data.get('title')
    message = data.get('message')
    priority = data.get('priority', 'normal')
    
    if not all([title, message]):
        return jsonify({'success': False, 'message': 'Título e mensagem são obrigatórios.'}), 400
    
    try:
        novo_aviso = Aviso(
            title=title,
            message=message,
            priority=priority,
            created_by=session['user_id']
        )
        db.session.add(novo_aviso)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Aviso criado com sucesso!'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Erro ao criar aviso: {str(e)}'}), 500

@app.route('/delete_aviso/<int:aviso_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_aviso(aviso_id):
    """Remove um aviso (apenas admins)."""
    try:
        aviso = db.session.get(Aviso, aviso_id)
        if not aviso:
            return jsonify({'success': False, 'message': 'Aviso não encontrado'}), 404
        aviso.active = False  # Desativa ao invés de deletar
        db.session.commit()
        return jsonify({'success': True, 'message': 'Aviso removido com sucesso!'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Erro ao remover aviso: {str(e)}'}), 500

# ========================================
# ROTAS PARA REPERTÓRIO MUSICAL
# ========================================
@app.route('/repertorio')
@login_required
def repertorio():
    """Página de repertório musical."""
    return render_template('repertorio.html')

@app.route('/get_repertorio', methods=['GET'])
@login_required
def get_repertorio():
    """Carrega todo o repertório musical."""
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
                'audio_file': musica.audio_file,  # Arquivo local de áudio
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
    """Adiciona uma nova música ao repertório (apenas admins)."""
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
        return jsonify({'success': False, 'message': 'Título é obrigatório.'}), 400
    
    # Processar arquivo de áudio se houver
    audio_filename = None
    if 'audio_file' in request.files:
        file = request.files['audio_file']
        if file and file.filename and allowed_audio_file(file.filename):
            # Gerar nome único para o arquivo
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
        return jsonify({'success': True, 'message': 'Música adicionada com sucesso!'}), 200
    except Exception as e:
        db.session.rollback()
        # Se houve erro, remover o arquivo salvo
        if audio_filename:
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], audio_filename)
            if os.path.exists(filepath):
                os.remove(filepath)
        return jsonify({'success': False, 'message': f'Erro ao adicionar música: {str(e)}'}), 500

@app.route('/update_musica/<int:musica_id>', methods=['PUT'])
@login_required
@admin_required
def update_musica(musica_id):
    """Atualiza uma música do repertório (apenas admins)."""
    data = request.json
    
    try:
        musica = db.session.get(Repertorio, musica_id)
        if not musica:
            return jsonify({'success': False, 'message': 'Música não encontrada'}), 404
        
        musica.title = data.get('title', musica.title)
        musica.artist = data.get('artist', musica.artist)
        musica.key_tone = data.get('key_tone', musica.key_tone)
        musica.tempo = data.get('tempo', musica.tempo)
        musica.link_video = data.get('link_video', musica.link_video)
        musica.link_audio = data.get('link_audio', musica.link_audio)
        musica.lyrics = data.get('lyrics', musica.lyrics)
        musica.notes = data.get('notes', musica.notes)
        musica.category = data.get('category', musica.category)
        
        db.session.commit()
        return jsonify({'success': True, 'message': 'Música atualizada com sucesso!'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Erro ao atualizar música: {str(e)}'}), 500

@app.route('/delete_musica/<int:musica_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_musica(musica_id):
    """Remove uma música do repertório (apenas admins)."""
    try:
        musica = db.session.get(Repertorio, musica_id)
        if not musica:
            return jsonify({'success': False, 'message': 'Música não encontrada'}), 404
        
        # Remover arquivo de áudio se existir
        if musica.audio_file:
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], musica.audio_file)
            if os.path.exists(filepath):
                os.remove(filepath)
        
        db.session.delete(musica)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Música removida com sucesso!'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Erro ao remover música: {str(e)}'}), 500

@app.route('/uploads/<filename>')
@login_required
def uploaded_file(filename):
    """Serve arquivos de áudio do diretório de uploads."""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# ========================================
# ROTAS PARA INDISPONIBILIDADE
# ========================================
@app.route('/indisponibilidade')
@login_required
def indisponibilidade():
    """Página de indisponibilidade."""
    return render_template('indisponibilidade.html')

@app.route('/get_periodo_indisponibilidade', methods=['GET'])
@login_required
def get_periodo_indisponibilidade():
    """Verifica se o período de indisponibilidade está aberto (controlado pelo admin)."""
    try:
        # Buscar configuração
        config = Configuracao.query.filter_by(chave='indisponibilidade_aberta').first()
        
        if not config:
            # Criar configuração padrão (fechado)
            config = Configuracao(
                chave='indisponibilidade_aberta',
                valor='false',
                descricao='Controla se membros podem registrar indisponibilidades'
            )
            db.session.add(config)
            db.session.commit()
        
        periodo_aberto = config.valor.lower() == 'true'
        
        if periodo_aberto:
            mensagem = "Período ABERTO! Você pode registrar suas indisponibilidades."
        else:
            mensagem = "Período FECHADO. Aguarde o administrador abrir o período de registro."
        
        return jsonify({
            'periodo_aberto': periodo_aberto,
            'mensagem': mensagem,
            'atualizado_em': config.atualizado_em.strftime('%d/%m/%Y %H:%M') if config.atualizado_em else None
        }), 200
    except Exception as e:
        print(f"Erro ao verificar período de indisponibilidade: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/toggle_periodo_indisponibilidade', methods=['POST'])
@login_required
@admin_required
def toggle_periodo_indisponibilidade():
    """Abre ou fecha o período de registro de indisponibilidades (apenas admin)."""
    print("[DEBUG] Função toggle_periodo_indisponibilidade chamada!")
    try:
        # Buscar ou criar configuração
        config = Configuracao.query.filter_by(chave='indisponibilidade_aberta').first()
        print(f"[DEBUG] Config encontrada: {config}")
        
        if not config:
            print("[DEBUG] Config não existe, criando nova...")
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
            'mensagem': f'Período de indisponibilidade agora está {status}.'
        }
        print(f"[DEBUG] Retornando: {resultado}")
        
        return jsonify(resultado), 200
    except Exception as e:
        db.session.rollback()
        print(f"[ERROR] Erro ao alternar período: {str(e)}")
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
                
                # Formatar período de data
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
        
        # Guardar informações para log
        member_name = indisponibilidade.member.name if indisponibilidade.member else 'Desconhecido'
        date_str = indisponibilidade.date_start.strftime('%d/%m/%Y')
        
        db.session.delete(indisponibilidade)
        db.session.commit()
        
        print(f"[ADMIN] Indisponibilidade excluída: {member_name} - {date_str}")
        
        return jsonify({
            'success': True,
            'message': f'Indisponibilidade de {member_name} excluída com sucesso!'
        }), 200
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao excluir indisponibilidade: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/get_cultos_disponiveis', methods=['GET'])
@login_required
def get_cultos_disponiveis():
    """Retorna cultos futuros para seleção de indisponibilidade."""
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
    """Carrega indisponibilidades do usuário logado."""
    try:
        user = db.session.get(User, session['user_id']) or db.session.get(Member, session['user_id'])
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
                
                # Se for indisponibilidade para culto específico, buscar info do culto
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
        # Verificar se o período de registro está aberto (controle do admin)
        config = Configuracao.query.filter_by(chave='indisponibilidade_aberta').first()
        if not config or config.valor.lower() != 'true':
            return jsonify({
                'success': False, 
                'message': 'Período fechado! O administrador não liberou o registro de indisponibilidades no momento.'
            }), 403
        
        data = request.json
        cultos_ids = data.get('cultos_ids', [])  # Lista de IDs de cultos
        reason = data.get('motivo')
        
        if not cultos_ids or len(cultos_ids) == 0:
            return jsonify({'success': False, 'message': 'Selecione pelo menos um culto.'}), 400
        
        if not reason or reason.strip() == '':
            return jsonify({'success': False, 'message': 'Motivo é obrigatório.'}), 400
        
        user = db.session.get(User, session['user_id']) or db.session.get(Member, session['user_id'])
        member = Member.query.filter_by(email=user.email).first() if isinstance(user, User) else user
        
        if not member:
            return jsonify({'success': False, 'message': 'Membro não encontrado.'}), 404
        
        # Criar uma indisponibilidade para cada culto selecionado
        indisponibilidades_criadas = 0
        for culto_id in cultos_ids:
            # Verificar se o culto existe
            culto = Culto.query.get(culto_id)
            if not culto:
                continue
            
            # Verificar se já existe indisponibilidade para este culto
            existe = Indisponibilidade.query.filter_by(
                member_id=member.id,
                culto_id=culto_id
            ).first()
            
            if existe:
                continue  # Pular se já existe
            
            # Criar indisponibilidade
            nova_indisponibilidade = Indisponibilidade(
                member_id=member.id,
                culto_id=culto_id,
                date_start=culto.date,
                date_end=culto.date,
                reason=reason,
                status='approved'  # Auto-aprovado pois foi feito no período correto
            )
            db.session.add(nova_indisponibilidade)
            indisponibilidades_criadas += 1
        
        db.session.commit()
        
        if indisponibilidades_criadas == 0:
            return jsonify({
                'success': False, 
                'message': 'Nenhuma indisponibilidade foi criada. Talvez você já tenha registrado para esses cultos.'
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
            return jsonify({'success': False, 'message': 'Indisponibilidade não encontrada'}), 404
        
        # Verifica se o usuário pode deletar (próprio ou admin)
        user = db.session.get(User, session['user_id']) or db.session.get(Member, session['user_id'])
        member = Member.query.filter_by(email=user.email).first() if isinstance(user, User) else user
        
        if ind.member_id != member.id and not getattr(user, 'is_admin', False):
            return jsonify({'success': False, 'message': 'Sem permissão para deletar esta indisponibilidade'}), 403
        
        db.session.delete(ind)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Indisponibilidade removida com sucesso!'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Erro ao remover indisponibilidade: {str(e)}'}), 500

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
    """Dashboard administrativo com estatísticas."""
    return render_template('dashboard.html')

@app.route('/estatisticas')
@login_required
@admin_required
def estatisticas():
    """Página de estatísticas de músicas."""
    return render_template('estatisticas.html')

@app.route('/get_dashboard_stats', methods=['GET'])
@login_required
@admin_required
def get_dashboard_stats():
    """Retorna estatísticas para o dashboard administrativo."""
    try:
        # Estatísticas gerais - todas exibindo totais cadastrados
        total_membros = Member.query.count()
        membros_ativos = Member.query.filter_by(suspended=False).count()
        total_cultos = Culto.query.count()
        total_escalas = Escala.query.count()
        total_musicas = Repertorio.query.count()
        total_avisos = Aviso.query.filter_by(active=True).count()
        feedbacks_pendentes = Feedback.query.filter_by(status='pending').count()
        
        # Membros por instrumento
        membros_por_instrumento = db.session.query(
            Member.instrument, 
            db.func.count(Member.id)
        ).group_by(Member.instrument).all()
        
        # Próximos cultos
        proximos_cultos = Culto.query.filter(
            Culto.date >= date.today()
        ).order_by(Culto.date.asc()).limit(5).all()
        
        # Avisos recentes
        avisos_recentes = Aviso.query.filter_by(active=True).order_by(
            Aviso.created_at.desc()
        ).limit(5).all()
        
        print(f"[DEBUG] Dashboard Stats: Membros={total_membros}, Cultos={total_cultos}, Escalas={total_escalas}, Músicas={total_musicas}")
        
        return jsonify({
            'total_membros': total_membros,
            'membros_ativos': total_membros,  # Mostrar total cadastrado na home
            'total_cultos': total_cultos,
            'total_escalas': total_escalas,
            'total_musicas': total_musicas,
            'total_avisos': total_avisos,
            'feedbacks_pendentes': feedbacks_pendentes,
            'membros_por_instrumento': [{
                'instrumento': inst or 'Não definido',
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
        }), 200
    except Exception as e:
        print(f"[ERROR] Dashboard stats error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/get_ranking_escalas', methods=['GET'])
@login_required
@admin_required
def get_ranking_escalas():
    """Retorna ranking de membros por participação em escalas (mês e ano)."""
    try:
        hoje = date.today()
        periodo = request.args.get('periodo', 'mes')  # 'mes' ou 'ano'
        
        # Definir data de início
        if periodo == 'mes':
            data_inicio = date(hoje.year, hoje.month, 1)
        else:  # ano
            data_inicio = date(hoje.year, 1, 1)
        
        # Buscar escalas do período
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

if __name__ == '__main__':
    # Garante que o banco de dados seja criado antes de rodar o servidor
    ensure_database_exists()
    with app.app_context():
        create_admin()  # Adiciona o administrador padrão
    
    # Configuração de ambiente
    port = int(os.environ.get('PORT', 5000))
    debug_mode = os.environ.get('FLASK_ENV', 'development') == 'development'
    
    app.run(host='0.0.0.0', port=port, debug=debug_mode)