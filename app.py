from flask import Flask, render_template, jsonify, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_required, login_user, logout_user, current_user
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
import secrets
import os

# Configuração do Flask
app = Flask(__name__)
app.secret_key = secrets.token_hex(16)  # Gera uma chave segura para sessões

# Configura o banco de dados SQLite na pasta 'instance'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(app.instance_path, 'ministry.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Desativa notificações de modificação para performance
app.config['UPLOAD_FOLDER'] = 'uploads'  # Pasta para uploads (ex.: áudio)

# Garante que a pasta 'instance' exista
try:
    os.makedirs(app.instance_path, exist_ok=True)
except OSError as e:
    print(f"Erro ao criar pasta 'instance': {e}")

# Configuração do banco de dados
db = SQLAlchemy(app)

# Configuração do Flask-Login para autenticação
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # Define a rota de login como padrão

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

    def set_password(self, password):
        """Define a senha como hash para o membro."""
        self.password = generate_password_hash(password)

    def check_password(self, password):
        """Verifica se a senha fornecida corresponde ao hash armazenado."""
        return check_password_hash(self.password, password)

class Culto(db.Model):
    """Modelo para cultos do ministério."""
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    time = db.Column(db.String(5), nullable=False)  # Formato: "HH:MM"
    description = db.Column(db.String(255), nullable=False)

class Escala(db.Model):
    """Modelo para escalas de membros em cultos."""
    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey('member.id'), nullable=False)
    culto_id = db.Column(db.Integer, db.ForeignKey('culto.id'), nullable=False)
    role = db.Column(db.String(120), nullable=False)  # Ex.: "Guitarrista Principal"

    member = db.relationship('Member', backref=db.backref('escalas', lazy=True))
    culto = db.relationship('Culto', backref=db.backref('escalas', lazy=True))

# Carregar usuário para Flask-Login (suporta tanto User quanto Member)
@login_manager.user_loader
def load_user(user_id):
    """Carrega um usuário ou membro pelo ID para autenticação."""
    user = User.query.get(int(user_id))
    if not user:
        return Member.query.get(int(user_id))
    return user

# Criar um administrador padrão
def create_admin():
    """Cria um administrador padrão se não existir."""
    email = "admin@ministeriodelouvor.com"
    password = "admin123"
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
    else:
        print(f"Banco de dados 'ministry.db' já existe em: {db_path}")

# Rotas principais
@app.route('/')
@login_required
def index():
    """Rota para a página inicial."""
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Rota para login de usuários e membros."""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Tenta encontrar o usuário como User ou Member
        user = User.query.filter_by(email=email).first()
        if not user:
            user = Member.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            login_user(user)
            session['user_id'] = user.id
            session['is_admin'] = getattr(user, 'is_admin', False)  # Verifica se é admin (só User tem is_admin)
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
    return render_template('membros.html')

@app.route('/feedback')
@login_required
def feedback():
    """Rota para a página de feedback."""
    return render_template('feedback.html')

@app.route('/cultos')
@login_required
def cultos():
    """Rota para a página de cultos."""
    cultos = Culto.query.all()
    return render_template('cultos.html', cultos=cultos)

@app.route('/escalas')
@login_required
def escalas():
    """Rota para a página de escalas."""
    user = User.query.get(session['user_id']) or Member.query.get(session['user_id'])
    member = Member.query.filter_by(email=user.email).first() if isinstance(user, User) else user
    if member:
        escalas = Escala.query.join(Culto).filter(Escala.member_id == member.id).all()
    else:
        escalas = []
    return render_template('escalas.html', escalas=escalas)

# Rotas administrativas
@app.route('/painel_administrativo')
@login_required
def painel_administrativo():
    """Rota para o painel administrativo (apenas para admins)."""
    if not current_user.is_admin:
        flash('Acesso negado. Somente administradores podem acessar esta página.', 'error')
        return redirect(url_for('index'))
    cultos = Culto.query.all()
    membros = Member.query.all()
    escalas = Escala.query.all()
    return render_template('painel_administrativo.html', cultos=cultos, membros=membros, escalas=escalas)

@app.route('/cadastro_membros')
@login_required
def cadastro_membros():
    """Rota para a página de cadastro de membros (apenas para admins)."""
    if not current_user.is_admin:
        flash('Acesso negado. Somente administradores podem acessar esta página.', 'error')
        return redirect(url_for('index'))
    return render_template('cadastro_membros.html')

# Rotas para gerenciar cultos (apenas para admins)
@app.route('/add_culto', methods=['POST'])
@login_required
def add_culto():
    """Adiciona um novo culto (apenas para admins)."""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Acesso negado.'}), 403
    date_str = request.json.get('date')
    time = request.json.get('time')
    description = request.json.get('description')
    try:
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
        if Culto.query.filter_by(date=date, time=time, description=description).first():
            return jsonify({'success': False, 'message': 'Este culto já existe.'}), 400
        novo_culto = Culto(date=date, time=time, description=description)
        db.session.add(novo_culto)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Culto adicionado com sucesso!'}), 200
    except ValueError:
        return jsonify({'success': False, 'message': 'Data ou formato inválido.'}), 400

@app.route('/edit_culto/<int:culto_id>', methods=['POST'])
@login_required
def edit_culto(culto_id):
    """Edita um culto existente (apenas para admins)."""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Acesso negado.'}), 403
    culto = Culto.query.get_or_404(culto_id)
    date_str = request.json.get('date')
    time = request.json.get('time')
    description = request.json.get('description')
    try:
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
        if Culto.query.filter(Culto.id != culto_id, Culto.date == date, Culto.time == time, Culto.description == description).first():
            return jsonify({'success': False, 'message': 'Outro culto com esses dados já existe.'}), 400
        culto.date = date
        culto.time = time
        culto.description = description
        db.session.commit()
        return jsonify({'success': True, 'message': 'Culto atualizado com sucesso!'}), 200
    except ValueError:
        return jsonify({'success': False, 'message': 'Data ou formato inválido.'}), 400

@app.route('/delete_culto/<int:culto_id>', methods=['POST'])
@login_required
def delete_culto(culto_id):
    """Remove um culto (apenas para admins)."""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Acesso negado.'}), 403
    culto = Culto.query.get_or_404(culto_id)
    db.session.delete(culto)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Culto removido com sucesso!'}), 200

# Rotas para gerenciar membros (apenas para admins)
@app.route('/add_member', methods=['POST'])
@login_required
def add_member():
    """Adiciona um novo membro (apenas para admins)."""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Acesso negado.'}), 403
    name = request.json.get('name')
    instrument = request.json.get('instrument')
    email = request.json.get('email')
    phone = request.json.get('phone')
    password = request.json.get('password', '123456')  # Senha padrão, caso não fornecida
    if not all([name, email]):  # Nome e email são obrigatórios
        return jsonify({'success': False, 'message': 'Nome e email são obrigatórios.'}), 400
    if Member.query.filter_by(email=email).first():
        return jsonify({'success': False, 'message': 'Este email já está cadastrado.'}), 400
    novo_membro = Member(name=name, instrument=instrument, email=email, phone=phone)
    novo_membro.set_password(password)  # Define a senha hashada
    db.session.add(novo_membro)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Membro cadastrado com sucesso! A senha padrão é 123456, e o membro pode alterá-la no perfil.'}), 200

@app.route('/edit_member/<int:member_id>', methods=['POST'])
@login_required
def edit_member(member_id):
    """Edita um membro existente (apenas para admins)."""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Acesso negado.'}), 403
    member = Member.query.get_or_404(member_id)
    name = request.json.get('name')
    instrument = request.json.get('instrument')
    email = request.json.get('email')
    phone = request.json.get('phone')
    password = request.json.get('password')  # Permite alterar a senha, se fornecida
    if not name or not email:
        return jsonify({'success': False, 'message': 'Nome e email são obrigatórios.'}), 400
    if email != member.email and Member.query.filter_by(email=email).first():
        return jsonify({'success': False, 'message': 'Este email já está cadastrado por outro membro.'}), 400
    member.name = name
    member.instrument = instrument
    member.email = email
    member.phone = phone
    if password:
        member.set_password(password)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Membro atualizado com sucesso!'}), 200

@app.route('/delete_member/<int:member_id>', methods=['POST'])
@login_required
def delete_member(member_id):
    """Remove um membro (apenas para admins)."""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Acesso negado.'}), 403
    member = Member.query.get_or_404(member_id)
    db.session.delete(member)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Membro removido com sucesso!'}), 200

# Rotas para gerenciar escalas (apenas para admins)
@app.route('/add_escala', methods=['POST'])
@login_required
def add_escala():
    """Adiciona uma nova escala (apenas para admins)."""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Acesso negado.'}), 403
    member_id = request.json.get('member_id')
    culto_id = request.json.get('culto_id')
    role = request.json.get('role')
    if member_id and culto_id and role:
        if Escala.query.filter_by(member_id=member_id, culto_id=culto_id).first():
            return jsonify({'success': False, 'message': 'Este membro já está escalado para este culto.'}), 400
        nova_escala = Escala(member_id=member_id, culto_id=culto_id, role=role)
        db.session.add(nova_escala)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Escala adicionada com sucesso!'}), 200
    return jsonify({'success': False, 'message': 'Dados inválidos.'}), 400

@app.route('/edit_escala/<int:escala_id>', methods=['POST'])
@login_required
def edit_escala(escala_id):
    """Edita uma escala existente (apenas para admins)."""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Acesso negado.'}), 403
    escala = Escala.query.get_or_404(escala_id)
    role = request.json.get('role')
    if role:
        escala.role = role
        db.session.commit()
        return jsonify({'success': True, 'message': 'Escala atualizada com sucesso!'}), 200
    return jsonify({'success': False, 'message': 'Dados inválidos.'}), 400

@app.route('/delete_escala/<int:escala_id>', methods=['POST'])
@login_required
def delete_escala(escala_id):
    """Remove uma escala (apenas para admins)."""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Acesso negado.'}), 403
    escala = Escala.query.get_or_404(escala_id)
    db.session.delete(escala)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Escala removida com sucesso!'}), 200

# Rotas para carregar dados dinâmicos
@app.route('/get_user_data', methods=['GET'])
@login_required
def get_user_data():
    """Carrega dados do usuário logado (User ou Member), priorizando o nome do membro."""
    user = User.query.get(session['user_id']) or Member.query.get(session['user_id'])
    if isinstance(user, User):
        # Para um User (admin), tenta encontrar o Member associado pelo email
        member = Member.query.filter_by(email=user.email).first()
        name = member.name if member else user.email.split('@')[0]  # Usa o nome do member ou o username antes do '@'
    else:  # Membro comum
        name = user.name  # Usa o nome diretamente do Member
    
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
    """Carrega avisos simulados."""
    announcements = [
        {"text": "Ensaio geral marcado para sexta-feira às 19h."},
        {"text": "Novo repertório disponível no app!"}
    ]
    return jsonify(announcements)

@app.route('/get_user_scales', methods=['GET'])
@login_required
def get_user_scales():
    """Carrega as escalas do usuário logado (User ou Member)."""
    user = User.query.get(session['user_id']) or Member.query.get(session['user_id'])
    member = Member.query.filter_by(email=user.email).first() if isinstance(user, User) else user
    if member:
        escalas = Escala.query.join(Culto).filter(Escala.member_id == member.id).all()
        return jsonify([{
            'culto': {
                'date': escala.culto.date.strftime('%Y-%m-%d'),
                'time': escala.culto.time,
                'description': escala.culto.description
            },
            'role': escala.role
        } for escala in escalas])
    return jsonify([]), 200

@app.route('/get_cult_calendar', methods=['GET'])
@login_required
def get_cult_calendar():
    """Carrega o calendário de cultos."""
    cultos = Culto.query.all()
    return jsonify([{
        'id': culto.id,
        'date': culto.date.strftime('%Y-%m-%d'),
        'time': culto.time,
        'description': culto.description
    } for culto in cultos])

@app.route('/get_membros', methods=['GET'])
@login_required
def get_membros():
    """Carrega a lista de membros."""
    membros = Member.query.all()
    return jsonify([{
        'id': member.id,
        'name': member.name,
        'instrument': member.instrument,
        'email': member.email,
        'phone': member.phone
    } for member in membros])

@app.route('/submit_feedback', methods=['POST'])
@login_required
def submit_feedback():
    """Processa feedback enviado pelo usuário (simulado)."""
    data = request.json
    feedback_text = data.get('feedback')
    user = User.query.get(session['user_id']) or Member.query.get(session['user_id'])
    user_email = user.email

    if feedback_text and user_email:
        # Simulação de salvamento (em produção, use um banco de dados)
        print(f"Feedback recebido de {user_email}: {feedback_text}")
        return jsonify({'success': True, 'message': 'Feedback enviado com sucesso!'}), 200
    return jsonify({'success': False, 'message': 'Erro ao enviar feedback. Tente novamente.'}), 400

if __name__ == '__main__':
    # Garante que o banco de dados seja criado antes de rodar o servidor
    ensure_database_exists()
    with app.app_context():
        create_admin()  # Adiciona o administrador padrão
    app.run(debug=True)  # Inicia o servidor em modo de depuração