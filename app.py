from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_socketio import SocketIO, emit
import sqlite3
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from datetime import datetime, timedelta
import re
from werkzeug.utils import secure_filename
import firebase_admin
from firebase_admin import credentials, messaging
import logging
import json

# Configurar logging para depuração
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Inicializar Firebase Admin com credenciais flexíveis
cred_path = os.getenv('FIREBASE_CRED_PATH')
if not cred_path:
    cred_json = os.getenv('FIREBASE_CREDENTIALS')
    if cred_json:
        cred = credentials.Certificate(json.loads(cred_json))
    else:
        cred = credentials.Certificate('static/firebase-adminsdk.json')
else:
    cred = credentials.Certificate(cred_path)
firebase_admin.initialize_app(cred)

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Chave secreta mais segura gerada randomicamente

# Configurar sessões persistentes
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=30)  # Sessão válida por 30 dias
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SECURE'] = True  # Ativar em produção com HTTPS
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

socketio = SocketIO(app, async_mode='gevent', ping_timeout=60, ping_interval=25)

# Configurações de e-mail
EMAIL_ADDRESS = "seu_email@gmail.com"  # Substitua pelo seu e-mail real
EMAIL_PASSWORD = "abcdefghijklmnop"    # Substitua pela senha ou chave de app do Gmail

# Configurações de upload de foto
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Configurações de upload de músicas
SONGS_UPLOAD_FOLDER = 'static/uploads/songs'
ALLOWED_SONG_EXTENSIONS = {'mp3', 'mp4', 'wav', 'ogg', 'm4a'}
app.config['SONGS_UPLOAD_FOLDER'] = SONGS_UPLOAD_FOLDER
os.makedirs(SONGS_UPLOAD_FOLDER, exist_ok=True)

DATABASE = 'database.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    tables = cursor.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()
    table_names = [table['name'] for table in tables]
    
    if 'users' not in table_names:
        cursor.execute('''CREATE TABLE users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE NOT NULL,
                        password TEXT NOT NULL,
                        is_admin INTEGER DEFAULT 1,
                        profile_pic TEXT,
                        fcm_token TEXT
                    )''')
        cursor.execute("INSERT INTO users (username, password, is_admin) VALUES ('admin', 'admin123', 1)")
    else:
        cursor.execute("PRAGMA table_info(users)")
        columns = [col['name'] for col in cursor.fetchall()]
        if 'profile_pic' not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN profile_pic TEXT")
        if 'fcm_token' not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN fcm_token TEXT")

    if 'members' not in table_names:
        cursor.execute('''CREATE TABLE members (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        role TEXT NOT NULL,
                        contact TEXT NOT NULL,
                        password TEXT NOT NULL,
                        profile_pic TEXT,
                        fcm_token TEXT
                    )''')
    else:
        cursor.execute("PRAGMA table_info(members)")
        columns = [col['name'] for col in cursor.fetchall()]
        if 'profile_pic' not in columns:
            cursor.execute("ALTER TABLE members ADD COLUMN profile_pic TEXT")
        if 'fcm_token' not in columns:
            cursor.execute("ALTER TABLE members ADD COLUMN fcm_token TEXT")

    if 'scales' not in table_names:
        cursor.execute('''CREATE TABLE scales (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        date TEXT NOT NULL,
                        event TEXT NOT NULL,
                        participants TEXT NOT NULL
                    )''')
    
    if 'repertoire' not in table_names:
        cursor.execute('''CREATE TABLE repertoire (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        scale_id INTEGER,
                        song TEXT NOT NULL,
                        FOREIGN KEY (scale_id) REFERENCES scales(id)
                    )''')
    
    if 'rehearsals' not in table_names:
        cursor.execute('''CREATE TABLE rehearsals (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        scale_id INTEGER,
                        date TEXT NOT NULL,
                        time TEXT NOT NULL,
                        location TEXT,
                        FOREIGN KEY (scale_id) REFERENCES scales(id)
                    )''')
    
    if 'notices' not in table_names:
        cursor.execute('''CREATE TABLE notices (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        title TEXT NOT NULL,
                        message TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        is_active INTEGER DEFAULT 1
                    )''')
        logger.info("Tabela 'notices' criada com sucesso.")
    
    if 'songs' not in table_names:
        cursor.execute('''CREATE TABLE songs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        title TEXT NOT NULL,
                        tone TEXT,
                        minister TEXT,
                        youtube_link TEXT,
                        spotify_link TEXT,
                        file_path TEXT
                    )''')
        logger.info("Tabela 'songs' criada com sucesso.")
    
    conn.commit()
    conn.close()
    logger.info("Banco de dados inicializado/verificado com sucesso.")

def is_valid_email(email):
    email_pattern = re.compile(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$')
    return bool(email_pattern.match(email))

def check_email_duplicate(email, exclude_id=None):
    conn = get_db_connection()
    if exclude_id:
        query = "SELECT id FROM members WHERE contact = ? AND id != ?"
        params = (email, exclude_id)
    else:
        query = "SELECT id FROM members WHERE contact = ?"
        params = (email,)
    existing = conn.execute(query, params).fetchone()
    conn.close()
    return existing is not None

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def allowed_song_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_SONG_EXTENSIONS

def send_email(to_emails, subject, body):
    msg = MIMEMultipart()
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = ", ".join(to_emails)
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))
    
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        logger.info(f"E-mail enviado com sucesso para: {to_emails}")
        return True
    except Exception as e:
        logger.error(f"Erro ao enviar e-mail: {e}")
        return False

def send_push_notification(registration_ids, title, body):
    if not registration_ids:
        logger.warning("Nenhum token disponível para envio")
        return False
    valid_tokens = [token for token in registration_ids if token and isinstance(token, str)]
    if not valid_tokens:
        logger.warning("Nenhum token válido encontrado após filtragem")
        return False
    
    message = messaging.MulticastMessage(
        notification=messaging.Notification(
            title=title,
            body=body
        ),
        tokens=valid_tokens
    )
    try:
        response = messaging.send_multicast(message)
        logger.info(f"Notificações enviadas com sucesso: {response.success_count}, falhas: {response.failure_count}")
        if response.failure_count > 0:
            for idx, resp in enumerate(response.responses):
                if not resp.success:
                    logger.error(f"Falha no envio para o token {valid_tokens[idx]}: {resp.exception}")
        return response.success_count > 0
    except Exception as e:
        logger.error(f"Erro ao enviar notificação push: {e}")
        return False

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        
        user = conn.execute('SELECT * FROM users WHERE username = ? AND password = ?',
                           (username, password)).fetchone()
        if user:
            session['logged_in'] = True
            session['user_id'] = user['id']
            session['username'] = username
            session['is_admin'] = bool(user['is_admin'])
            session['name'] = user['username']
            session.permanent = True  # Torna a sessão persistente
            conn.close()
            flash("Login realizado com sucesso!", "success")
            logger.info(f"Usuário {username} logado com sucesso como admin")
            return redirect(url_for('index'))
        
        member = conn.execute('SELECT * FROM members WHERE contact = ? AND password = ?',
                             (username, password)).fetchone()
        conn.close()
        if member:
            session['logged_in'] = True
            session['user_id'] = member['id']
            session['username'] = username
            session['is_admin'] = False
            session['name'] = member['name']
            session.permanent = True  # Torna a sessão persistente
            flash("Login realizado com sucesso!", "success")
            logger.info(f"Membro {username} logado com sucesso")
            return redirect(url_for('index'))
        
        flash("Usuário ou senha inválidos", "error")
        logger.warning(f"Tentativa de login falhou para {username}")
        return render_template('login.html')
    return render_template('login.html')

@app.route('/index')
def index():
    if not session.get('logged_in'):
        logger.warning("Tentativa de acesso ao index sem login")
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    conn = get_db_connection()
    
    name = session.get('name')
    is_admin = session.get('is_admin', False)
    
    if is_admin:
        user_data = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    else:
        user_data = conn.execute('SELECT * FROM members WHERE id = ?', (user_id,)).fetchone()
    user_data = dict(user_data) if user_data else {'id': user_id, 'profile_pic': None}
    
    notices = conn.execute('SELECT * FROM notices WHERE is_active = 1 ORDER BY created_at DESC').fetchall()
    
    current_date = datetime.now().strftime('%Y-%m-%d')
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, date, event, participants 
        FROM scales 
        WHERE date >= ? 
        ORDER BY date ASC
    """, (current_date,))
    all_scales = cursor.fetchall()
    
    my_scales = []
    members = {}
    songs = {}
    rehearsals = {}
    for scale in all_scales:
        scale_id, date, event, participants = scale
        participant_ids = participants.split(',')
        participant_ids = [int(pid) for pid in participant_ids if pid.isdigit()]
        if user_id in participant_ids:
            song_rows = conn.execute('SELECT song FROM repertoire WHERE scale_id = ?', (scale_id,)).fetchall()
            scale_songs = [conn.execute('SELECT title FROM songs WHERE id = ?', (song_id['song'],)).fetchone()['title'] for song_id in song_rows] if song_rows else []
            
            rehearsal = conn.execute('SELECT date, time, location FROM rehearsals WHERE scale_id = ? LIMIT 1', (scale_id,)).fetchone()
            rehearsal_info = dict(rehearsal) if rehearsal else None
            
            my_scales.append({
                'id': scale_id,
                'date': date,
                'event': event,
                'participants': participants,
                'songs': scale_songs,
                'rehearsal': rehearsal_info
            })
        
        for pid in participant_ids:
            if pid not in members:
                cursor.execute("SELECT name FROM members WHERE id = ?", (pid,))
                member = cursor.fetchone()
                members[pid] = member['name'] if member else "Desconhecido"
    
    conn.close()
    
    logger.info(f"Renderizando index para {name}, admin: {is_admin}")
    return render_template('index.html', 
                         name=name, 
                         is_admin=is_admin, 
                         my_scales=my_scales, 
                         members=members,
                         notices=notices,
                         user_data=user_data)

@app.route('/visualizar_escalas')
def visualizar_escalas():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    conn = get_db_connection()
    scales = conn.execute('SELECT * FROM scales ORDER BY date ASC').fetchall()
    members = {row['id']: row['name'] for row in conn.execute('SELECT id, name FROM members').fetchall()}
    
    scales_with_details = []
    for scale in scales:
        scale_id = scale['id']
        song_rows = conn.execute('SELECT song FROM repertoire WHERE scale_id = ?', (scale_id,)).fetchall()
        scale_songs = [conn.execute('SELECT title FROM songs WHERE id = ?', (song_id['song'],)).fetchone()['title'] for song_id in song_rows] if song_rows else []
        
        rehearsal = conn.execute('SELECT date, time, location FROM rehearsals WHERE scale_id = ? LIMIT 1', (scale_id,)).fetchone()
        rehearsal_info = dict(rehearsal) if rehearsal else None
        
        scales_with_details.append({
            'id': scale['id'],
            'date': scale['date'],
            'event': scale['event'],
            'participants': scale['participants'],
            'songs': scale_songs,
            'rehearsal': rehearsal_info
        })
    
    conn.close()
    return render_template('visualizar_escalas.html', 
                         scales=scales_with_details, 
                         members=members, 
                         is_admin=session.get('is_admin', False),
                         name=session.get('name'))

@app.route('/visualizar_escala/<int:scale_id>')
def visualizar_escala(scale_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    scale = conn.execute('SELECT * FROM scales WHERE id = ?', (scale_id,)).fetchone()
    if not scale:
        conn.close()
        flash("Escala não encontrada!", "error")
        return redirect(url_for('index'))
    
    participant_ids = scale['participants'].split(',')
    participant_ids = [int(pid) for pid in participant_ids if pid.isdigit()]
    
    query = 'SELECT id, name FROM members WHERE id IN ({})'.format(','.join('?' for _ in participant_ids))
    members = {row['id']: row['name'] for row in conn.execute(query, participant_ids)}
    
    song_rows = conn.execute('SELECT song FROM repertoire WHERE scale_id = ?', (scale_id,)).fetchall()
    songs = []
    for song_row in song_rows:
        song_id = song_row['song']
        song_data = conn.execute('SELECT title, tone, youtube_link, spotify_link, file_path FROM songs WHERE id = ?', (song_id,)).fetchone()
        if song_data:
            songs.append(dict(song_data))
    
    rehearsal = conn.execute('SELECT date, time, location FROM rehearsals WHERE scale_id = ? LIMIT 1', (scale_id,)).fetchone()
    rehearsal_info = dict(rehearsal) if rehearsal else None
    
    conn.close()
    
    return render_template('visualizar_escala.html', 
                          scale=scale, 
                          members=members, 
                          songs=songs, 
                          rehearsal=rehearsal_info,
                          is_admin=session.get('is_admin', False),
                          name=session.get('name'))

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('user_id', None)
    session.pop('username', None)
    session.pop('is_admin', None)
    session.pop('name', None)
    logger.info("Usuário deslogado")
    return redirect(url_for('login'))

@app.route('/cadastrar_aviso', methods=['GET', 'POST'])
def cadastrar_aviso():
    if not session.get('logged_in') or not session.get('is_admin'):
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        title = request.form['title']
        message = request.form['message']
        created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        if not title.strip() or not message.strip():
            flash("Título e mensagem são obrigatórios!", "error")
            return render_template('cadastrar_aviso.html')
        
        conn = get_db_connection()
        conn.execute('INSERT INTO notices (title, message, created_at) VALUES (?, ?, ?)',
                    (title, message, created_at))
        conn.commit()
        
        members = conn.execute('SELECT fcm_token FROM members WHERE fcm_token IS NOT NULL').fetchall()
        users = conn.execute('SELECT fcm_token FROM users WHERE fcm_token IS NOT NULL').fetchall()
        tokens = [m['fcm_token'] for m in members] + [u['fcm_token'] for u in users]
        conn.close()
        
        if tokens:
            success = send_push_notification(tokens, title, message)
            flash("Aviso cadastrado e notificação enviada com sucesso!" if success else "Aviso cadastrado, mas falha ao enviar notificação!", "success" if success else "error")
        else:
            flash("Aviso cadastrado, mas nenhum dispositivo para notificar!", "success")
        return redirect(url_for('gerenciar_avisos'))
    
    return render_template('cadastrar_aviso.html')

@app.route('/gerenciar_avisos')
def gerenciar_avisos():
    if not session.get('logged_in') or not session.get('is_admin'):
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    notices = conn.execute('SELECT * FROM notices ORDER BY created_at DESC').fetchall()
    conn.close()
    
    return render_template('gerenciar_avisos.html', notices=notices)

@app.route('/editar_aviso/<int:notice_id>', methods=['GET', 'POST'])
def editar_aviso(notice_id):
    if not session.get('logged_in') or not session.get('is_admin'):
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    notice = conn.execute('SELECT * FROM notices WHERE id = ?', (notice_id,)).fetchone()
    if not notice:
        conn.close()
        flash("Aviso não encontrado!", "error")
        return redirect(url_for('gerenciar_avisos'))
    
    if request.method == 'POST':
        title = request.form['title']
        message = request.form['message']
        is_active = 1 if request.form.get('is_active') else 0
        
        if not title.strip() or not message.strip():
            conn.close()
            flash("Título e mensagem são obrigatórios!", "error")
            return render_template('editar_aviso.html', notice=notice)
        
        conn.execute('UPDATE notices SET title = ?, message = ?, is_active = ? WHERE id = ?',
                    (title, message, is_active, notice_id))
        conn.commit()
        conn.close()
        flash("Aviso atualizado com sucesso!", "success")
        return redirect(url_for('gerenciar_avisos'))
    
    conn.close()
    return render_template('editar_aviso.html', notice=notice)

@app.route('/excluir_aviso/<int:notice_id>', methods=['POST'])
def excluir_aviso(notice_id):
    if not session.get('logged_in') or not session.get('is_admin'):
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    notice = conn.execute('SELECT * FROM notices WHERE id = ?', (notice_id,)).fetchone()
    if not notice:
        conn.close()
        flash("Aviso não encontrado!", "error")
        return redirect(url_for('gerenciar_avisos'))
    
    conn.execute('DELETE FROM notices WHERE id = ?', (notice_id,))
    conn.commit()
    conn.close()
    flash("Aviso excluído com sucesso!", "success")
    return redirect(url_for('gerenciar_avisos'))

@app.route('/cadastrar_membro', methods=['GET', 'POST'])
def cadastrar_membro():
    if not session.get('logged_in') or not session.get('is_admin'):
        return redirect(url_for('login'))
    if request.method == 'POST':
        name = request.form['name']
        role = request.form['role']
        email = request.form['email']
        password = request.form['password']
        
        if not is_valid_email(email):
            flash("Formato de e-mail inválido!", "error")
            return render_template('cadastrar_membro.html')
        if check_email_duplicate(email):
            flash("Este e-mail já está cadastrado!", "error")
            return render_template('cadastrar_membro.html')
        
        conn = get_db_connection()
        conn.execute('INSERT INTO members (name, role, contact, password) VALUES (?, ?, ?, ?)',
                    (name, role, email, password))
        conn.commit()
        conn.close()
        flash("Membro cadastrado com sucesso!", "success")
        return redirect(url_for('index'))
    return render_template('cadastrar_membro.html')

@app.route('/criar_escala', methods=['GET', 'POST'])
def criar_escala():
    if not session.get('logged_in') or not session.get('is_admin'):
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    members = conn.execute('SELECT * FROM members ORDER BY role, name').fetchall()
    conn.close()
    
    members_by_role = {}
    for member in members:
        role = member['role']
        if role not in members_by_role:
            members_by_role[role] = []
        members_by_role[role].append(dict(member))
    
    if request.method == 'POST':
        date = request.form['date']
        event = request.form['event']
        participants = ','.join(request.form.getlist('participants'))
        if not participants:
            flash("Selecione pelo menos um participante!", "error")
            return render_template('criar_escala.html', members_by_role=members_by_role)
        conn = get_db_connection()
        conn.execute('INSERT INTO scales (date, event, participants) VALUES (?, ?, ?)',
                    (date, event, participants))
        conn.commit()
        conn.close()
        flash("Escala criada com sucesso!", "success")
        return redirect(url_for('index'))
    
    return render_template('criar_escala.html', members_by_role=members_by_role)

@app.route('/editar_escala/<int:scale_id>', methods=['GET', 'POST'])
def editar_escala(scale_id):
    if not session.get('logged_in') or not session.get('is_admin'):
        return redirect(url_for('login'))
    conn = get_db_connection()
    scale = conn.execute('SELECT * FROM scales WHERE id = ?', (scale_id,)).fetchone()
    members = conn.execute('SELECT * FROM members ORDER BY role, name').fetchall()
    conn.close()
    
    if not scale:
        flash("Escala não encontrada!", "error")
        return redirect(url_for('visualizar_escalas'))
    
    members_by_role = {}
    for member in members:
        role = member['role']
        if role not in members_by_role:
            members_by_role[role] = []
        members_by_role[role].append(dict(member))
    
    if request.method == 'POST':
        date = request.form['date']
        event = request.form['event']
        participants = ','.join(request.form.getlist('participants'))
        if not participants:
            flash("Selecione pelo menos um participante!", "error")
            return render_template('editar_escala.html', scale=scale, members_by_role=members_by_role)
        conn = get_db_connection()
        conn.execute('UPDATE scales SET date = ?, event = ?, participants = ? WHERE id = ?',
                    (date, event, participants, scale_id))
        conn.commit()
        conn.close()
        flash("Escala editada com sucesso!", "success")
        return redirect(url_for('visualizar_escalas'))
    
    return render_template('editar_escala.html', scale=scale, members_by_role=members_by_role)

@app.route('/excluir_escala/<int:scale_id>', methods=['POST'])
def excluir_escala(scale_id):
    if not session.get('logged_in') or not session.get('is_admin'):
        return redirect(url_for('login'))
    conn = get_db_connection()
    scale = conn.execute('SELECT * FROM scales WHERE id = ?', (scale_id,)).fetchone()
    if not scale:
        conn.close()
        flash("Escala não encontrada!", "error")
        return redirect(url_for('visualizar_escalas'))
    conn.execute('DELETE FROM repertoire WHERE scale_id = ?', (scale_id,))
    conn.execute('DELETE FROM rehearsals WHERE scale_id = ?', (scale_id,))
    conn.execute('DELETE FROM scales WHERE id = ?', (scale_id,))
    conn.commit()
    conn.close()
    flash("Escala excluída com sucesso!", "success")
    return redirect(url_for('visualizar_escalas'))

@app.route('/gerenciar_repertorio/<int:scale_id>', methods=['GET', 'POST'])
def gerenciar_repertorio(scale_id):
    if not session.get('logged_in') or not session.get('is_admin'):
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    scale = conn.execute('SELECT * FROM scales WHERE id = ?', (scale_id,)).fetchone()
    songs = conn.execute('SELECT * FROM repertoire WHERE scale_id = ?', (scale_id,)).fetchall()
    available_songs = conn.execute('SELECT id, title FROM songs ORDER BY title ASC').fetchall()
    
    user_id = session['user_id']
    name = session.get('name')
    is_admin = session.get('is_admin', False)
    
    if is_admin:
        user_data = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    else:
        user_data = conn.execute('SELECT * FROM members WHERE id = ?', (user_id,)).fetchone()
    user_data = dict(user_data) if user_data else {'id': user_id, 'profile_pic': None}
    
    if not scale:
        conn.close()
        flash("Escala não encontrada!", "error")
        return redirect(url_for('visualizar_escalas'))
    
    if request.method == 'POST':
        song_id = request.form.get('song_id')
        if not song_id:
            flash("Selecione uma música!", "error")
            conn.close()
            return render_template('gerenciar_repertorio.html', scale=scale, songs=songs, available_songs=available_songs, user_data=user_data, name=name, is_admin=is_admin)
        
        existing_song = conn.execute('SELECT id FROM repertoire WHERE scale_id = ? AND song = ?', (scale_id, song_id)).fetchone()
        if existing_song:
            flash("Esta música já está no repertório desta escala!", "error")
            conn.close()
            return render_template('gerenciar_repertorio.html', scale=scale, songs=songs, available_songs=available_songs, user_data=user_data, name=name, is_admin=is_admin)
        
        conn.execute('INSERT INTO repertoire (scale_id, song) VALUES (?, ?)', (scale_id, song_id))
        conn.commit()
        flash("Música adicionada ao repertório!", "success")
        conn.close()
        return redirect(url_for('gerenciar_repertorio', scale_id=scale_id))
    
    conn.close()
    return render_template('gerenciar_repertorio.html', scale=scale, songs=songs, available_songs=available_songs, user_data=user_data, name=name, is_admin=is_admin)

@app.route('/gerenciar_repertorio_global', methods=['GET', 'POST'])
def gerenciar_repertorio_global():
    if not session.get('logged_in') or not session.get('is_admin'):
        flash("Acesso restrito a administradores!", "error")
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    user_id = session['user_id']
    name = session.get('name')
    is_admin = session.get('is_admin', False)
    
    if is_admin:
        user_data = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    else:
        user_data = conn.execute('SELECT * FROM members WHERE id = ?', (user_id,)).fetchone()
    user_data = dict(user_data) if user_data else {'id': user_id, 'profile_pic': None}
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'create':
            title = request.form['title']
            tone = request.form.get('tone', '')
            minister = request.form.get('minister', '')
            youtube_link = request.form.get('youtube_link', '')
            spotify_link = request.form.get('spotify_link', '')
            
            if not title.strip():
                flash("O título da música é obrigatório!", "error")
                conn.close()
                return redirect(url_for('gerenciar_repertorio_global'))
            
            file_path = None
            if 'file' in request.files:
                file = request.files['file']
                if file and allowed_song_file(file.filename):
                    filename = secure_filename(f"{title}_{datetime.now().strftime('%Y%m%d%H%M%S')}.{file.filename.rsplit('.', 1)[1].lower()}")
                    file_path = os.path.join(app.config['SONGS_UPLOAD_FOLDER'], filename)
                    file.save(file_path)
            
            conn.execute('INSERT INTO songs (title, tone, minister, youtube_link, spotify_link, file_path) VALUES (?, ?, ?, ?, ?, ?)',
                        (title, tone, minister, youtube_link, spotify_link, file_path))
            conn.commit()
            flash("Música cadastrada com sucesso!", "success")
        
        elif action == 'edit':
            song_id = request.form['song_id']
            title = request.form['title']
            tone = request.form.get('tone', '')
            minister = request.form.get('minister', '')
            youtube_link = request.form.get('youtube_link', '')
            spotify_link = request.form.get('spotify_link', '')
            
            if not title.strip():
                flash("O título da música é obrigatório!", "error")
                conn.close()
                return redirect(url_for('gerenciar_repertorio_global'))
            
            file_path = conn.execute('SELECT file_path FROM songs WHERE id = ?', (song_id,)).fetchone()['file_path']
            if 'file' in request.files:
                file = request.files['file']
                if file and allowed_song_file(file.filename):
                    if file_path and os.path.exists(file_path):
                        os.remove(file_path)
                    filename = secure_filename(f"{title}_{datetime.now().strftime('%Y%m%d%H%M%S')}.{file.filename.rsplit('.', 1)[1].lower()}")
                    file_path = os.path.join(app.config['SONGS_UPLOAD_FOLDER'], filename)
                    file.save(file_path)
            
            conn.execute('UPDATE songs SET title = ?, tone = ?, minister = ?, youtube_link = ?, spotify_link = ?, file_path = ? WHERE id = ?',
                        (title, tone, minister, youtube_link, spotify_link, file_path, song_id))
            conn.commit()
            flash("Música atualizada com sucesso!", "success")
        
        elif action == 'delete':
            song_id = request.form['song_id']
            file_path = conn.execute('SELECT file_path FROM songs WHERE id = ?', (song_id,)).fetchone()['file_path']
            if file_path and os.path.exists(file_path):
                os.remove(file_path)
            conn.execute('DELETE FROM songs WHERE id = ?', (song_id,))
            conn.commit()
            flash("Música excluída com sucesso!", "success")
    
    songs = conn.execute('SELECT * FROM songs ORDER BY title ASC').fetchall()
    conn.close()
    return render_template('gerenciar_repertorio_global.html', songs=songs, user_data=user_data, name=name, is_admin=is_admin)

@app.route('/repertorio')
def repertorio():
    if not session.get('logged_in'):
        flash("Você precisa estar logado para visualizar o repertório!", "error")
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    songs = conn.execute('SELECT * FROM songs ORDER BY title ASC').fetchall()
    conn.close()
    return render_template('repertorio.html', songs=songs, is_admin=session.get('is_admin', False), name=session.get('name'), user_data=session.get('user_data', {}))

@app.route('/lista_membros')
def lista_membros():
    if not session.get('logged_in') or not session.get('is_admin'):
        return redirect(url_for('login'))
    conn = get_db_connection()
    members = conn.execute('SELECT * FROM members ORDER BY role ASC, name ASC').fetchall()
    conn.close()
    return render_template('lista_membros.html', members=members)

@app.route('/editar_membro/<int:member_id>', methods=['GET', 'POST'])
def editar_membro(member_id):
    if not session.get('logged_in') or not session.get('is_admin'):
        return redirect(url_for('login'))
    conn = get_db_connection()
    member = conn.execute('SELECT * FROM members WHERE id = ?', (member_id,)).fetchone()
    conn.close()
    if not member:
        flash("Membro não encontrado!", "error")
        return redirect(url_for('lista_membros'))
    
    if request.method == 'POST':
        name = request.form['name']
        role = request.form['role']
        email = request.form['email']
        password = request.form['password']
        
        if 'delete' in request.form:
            conn = get_db_connection()
            conn.execute('DELETE FROM members WHERE id = ?', (member_id,))
            conn.commit()
            conn.close()
            flash("Membro excluído com sucesso!", "success")
            return redirect(url_for('lista_membros'))
        
        if not is_valid_email(email):
            flash("Formato de e-mail inválido!", "error")
            return render_template('editar_membro.html', member=member)
        if check_email_duplicate(email, exclude_id=member_id):
            flash("Este e-mail já está cadastrado por outro membro!", "error")
            return render_template('editar_membro.html', member=member)
        
        conn = get_db_connection()
        conn.execute('UPDATE members SET name = ?, role = ?, contact = ?, password = ? WHERE id = ?',
                    (name, role, email, password, member_id))
        conn.commit()
        conn.close()
        flash("Membro atualizado com sucesso!", "success")
        return redirect(url_for('lista_membros'))
    
    return render_template('editar_membro.html', member=member)

@app.route('/compartilhar_escala/<int:scale_id>')
def compartilhar_escala(scale_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    conn = get_db_connection()
    scale = conn.execute('SELECT * FROM scales WHERE id = ?', (scale_id,)).fetchone()
    members = {row['id']: row['name'] for row in conn.execute('SELECT id, name FROM members').fetchall()}
    songs = conn.execute('SELECT song FROM repertoire WHERE scale_id = ?', (scale_id,)).fetchall()
    conn.close()
    if not scale:
        flash("Escala não encontrada!", "error")
        return redirect(url_for('visualizar_escalas'))
    return render_template('compartilhar_escala.html', scale=scale, members=members, songs=songs)

@app.route('/agendar_ensaio/<int:scale_id>', methods=['GET', 'POST'])
def agendar_ensaio(scale_id):
    if not session.get('logged_in') or not session.get('is_admin'):
        return redirect(url_for('login'))
    conn = get_db_connection()
    scale = conn.execute('SELECT * FROM scales WHERE id = ?', (scale_id,)).fetchone()
    rehearsals = conn.execute('SELECT * FROM rehearsals WHERE scale_id = ?', (scale_id,)).fetchall()
    conn.close()
    if not scale:
        flash("Escala não encontrada!", "error")
        return redirect(url_for('visualizar_escalas'))
    if request.method == 'POST':
        date = request.form['date']
        time = request.form['time']
        location = request.form['location']
        conn = get_db_connection()
        conn.execute('INSERT INTO rehearsals (scale_id, date, time, location) VALUES (?, ?, ?, ?)',
                    (scale_id, date, time, location))
        conn.commit()
        conn.close()
        flash("Ensaio agendado com sucesso!", "success")
        return redirect(url_for('agendar_ensaio', scale_id=scale_id))
    return render_template('agendar_ensaio.html', scale=scale, rehearsals=rehearsals)

@app.route('/historico_escalas', methods=['GET', 'POST'])
def historico_escalas():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    conn = get_db_connection()
    query = 'SELECT * FROM scales'
    params = []
    if request.method == 'POST':
        search = request.form['search'].strip()
        if search:
            query += ' WHERE date LIKE ? OR event LIKE ?'
            params = [f'%{search}%', f'%{search}%']
    query += ' ORDER BY date DESC'
    scales = conn.execute(query, params).fetchall()
    members = {row['id']: row['name'] for row in conn.execute('SELECT id, name FROM members').fetchall()}
    conn.close()
    return render_template('historico_escalas.html', scales=scales, members=members)

@app.route('/relatorios', methods=['GET', 'POST'])
def relatorios():
    if not session.get('logged_in') or not session.get('is_admin'):
        return redirect(url_for('login'))
    conn = get_db_connection()
    members = conn.execute('SELECT * FROM members').fetchall()
    scales = conn.execute('SELECT * FROM scales').fetchall()
    conn.close()

    participation = {}
    for member in members:
        participation[member['id']] = {'name': member['name'], 'count': 0}
    for scale in scales:
        participant_ids = scale['participants'].split(',')
        for pid in participant_ids:
            if pid and pid.isdigit() and int(pid) in participation:
                participation[int(pid)]['count'] += 1

    min_participation = request.form.get('min_participation', 0, type=int) if request.method == 'POST' else 0
    filtered_participation = {k: v for k, v in participation.items() if v['count'] >= min_participation}

    chart_data = {
        'labels': [data['name'] for data in filtered_participation.values()],
        'data': [data['count'] for data in filtered_participation.values()]
    }
    return render_template('relatorios.html', participation=filtered_participation, chart_data=chart_data)

@app.route('/comunicar_equipe', methods=['GET', 'POST'])
def comunicar_equipe():
    if not session.get('logged_in') or not session.get('is_admin'):
        return redirect(url_for('login'))
    conn = get_db_connection()
    members = conn.execute('SELECT * FROM members').fetchall()
    conn.close()
    if request.method == 'POST':
        message = request.form['message']
        selected_members = request.form.getlist('members')
        if not message.strip():
            flash("Digite uma mensagem!", "error")
            return render_template('comunicar_equipe.html', members=members)
        if not selected_members:
            flash("Selecione pelo menos um membro!", "error")
            return render_template('comunicar_equipe.html', members=members)
        
        to_emails = [m['contact'] for m in members if str(m['id']) in selected_members and m['contact']]
        if to_emails:
            subject = "Mensagem do Ministério de Louvor"
            if send_email(to_emails, subject, message):
                flash(f"Mensagem enviada para {len(to_emails)} membros com e-mail!", "success")
            else:
                flash("Erro ao enviar e-mails. Verifique as credenciais!", "error")
        else:
            flash("Nenhum membro selecionado tem e-mail cadastrado!", "error")
        return redirect(url_for('index'))
    return render_template('comunicar_equipe.html', members=members)

@app.route('/enviar_notificacoes', methods=['GET', 'POST'])
def enviar_notificacoes():
    if not session.get('logged_in') or not session.get('is_admin'):
        return redirect(url_for('login'))
    conn = get_db_connection()
    scales = conn.execute('SELECT * FROM scales WHERE date >= date("now")').fetchall()
    members = conn.execute('SELECT * FROM members').fetchall()
    conn.close()
    if request.method == 'POST':
        scale_id = request.form['scale_id']
        message = request.form['message']
        if not message.strip():
            flash("Digite uma mensagem!", "error")
            return render_template('enviar_notificacoes.html', scales=scales, members={m['id']: m['name'] for m in members})
        
        conn = get_db_connection()
        scale = conn.execute('SELECT * FROM scales WHERE id = ?', (scale_id,)).fetchone()
        if not scale:
            conn.close()
            flash("Escala não encontrada!", "error")
            return render_template('enviar_notificacoes.html', scales=scales, members={m['id']: m['name'] for m in members})
        
        participant_ids = scale['participants'].split(',')
        to_emails = [m['contact'] for m in members if str(m['id']) in participant_ids and m['contact']]
        member_tokens = [m['fcm_token'] for m in members if str(m['id']) in participant_ids and m['fcm_token']]
        conn.close()
        
        if to_emails:
            subject = f"Lembrete: {scale['event']} em {scale['date']}"
            body = f"Olá,\n\n{message}\n\nEvento: {scale['event']}\nData: {scale['date']}"
            if send_email(to_emails, subject, body):
                flash(f"Notificação por e-mail enviada para {len(to_emails)} participantes!", "success")
            else:
                flash("Erro ao enviar notificações por e-mail. Verifique as credenciais!", "error")
        
        if member_tokens:
            success = send_push_notification(member_tokens, subject, message)
            if success:
                flash(f"Notificação push enviada para {len(member_tokens)} participantes!", "success")
            else:
                flash("Erro ao enviar notificações push!", "error")
        
        notification = {
            'title': subject,
            'message': message,
            'event': scale['event'],
            'date': scale['date']
        }
        for pid in participant_ids:
            if pid and pid.isdigit():
                socketio.emit('notification', notification, room=f'user_{pid}')
        
        if not to_emails and not member_tokens:
            flash("Nenhum participante com e-mail ou token cadastrado!", "error")
        return redirect(url_for('index'))
    return render_template('enviar_notificacoes.html', scales=scales, members={m['id']: m['name'] for m in members})

@app.route('/perfil', methods=['GET', 'POST'])
def perfil():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    is_admin = session.get('is_admin', False)
    username = session.get('username')
    
    if is_admin:
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        if not user:
            conn.close()
            flash("Usuário não encontrado!", "error")
            return redirect(url_for('index'))
        user_data = dict(user)
    else:
        user = conn.execute('SELECT * FROM members WHERE contact = ?', (username,)).fetchone()
        if not user:
            conn.close()
            flash("Membro não encontrado!", "error")
            return redirect(url_for('index'))
        user_data = dict(user)
    
    if request.method == 'POST':
        if is_admin:
            new_username = request.form['username']
            new_password = request.form['password']
            conn.execute('UPDATE users SET username = ?, password = ? WHERE id = ?',
                        (new_username, new_password, user_data['id']))
            session['username'] = new_username
            session['name'] = new_username
        else:
            new_contact = request.form['contact']
            new_password = request.form['password']
            if not is_valid_email(new_contact):
                conn.close()
                flash("Formato de e-mail inválido!", "error")
                return render_template('perfil.html', user_data=user_data, is_admin=is_admin)
            if check_email_duplicate(new_contact, exclude_id=user_data['id']):
                conn.close()
                flash("Este e-mail já está cadastrado por outro membro!", "error")
                return render_template('perfil.html', user_data=user_data, is_admin=is_admin)
            conn.execute('UPDATE members SET contact = ?, password = ? WHERE id = ?',
                        (new_contact, new_password, user_data['id']))
            session['username'] = new_contact
        
        if 'profile_pic' in request.files:
            file = request.files['profile_pic']
            if file and allowed_file(file.filename):
                filename = secure_filename(f"{user_data['id']}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}")
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                if is_admin:
                    conn.execute('UPDATE users SET profile_pic = ? WHERE id = ?', (filename, user_data['id']))
                else:
                    conn.execute('UPDATE members SET profile_pic = ? WHERE id = ?', (filename, user_data['id']))
                user_data['profile_pic'] = filename
                flash("Foto de perfil atualizada com sucesso!", "success")
            elif file.filename != '':
                flash("Formato de arquivo inválido. Use PNG, JPG, JPEG ou GIF.", "error")
        
        conn.commit()
        conn.close()
        flash("Perfil atualizado com sucesso!", "success")
        return redirect(url_for('perfil'))
    
    conn.close()
    return render_template('perfil.html', user_data=user_data, is_admin=is_admin)

@app.route('/save_token', methods=['POST'])
def save_token():
    if not session.get('logged_in'):
        return jsonify({'error': 'Não autenticado'}), 401
    
    token = request.form.get('fcm_token')
    user_id = session['user_id']
    is_admin = session.get('is_admin', False)
    
    if not token:
        logger.warning(f"Token FCM não fornecido para User ID: {user_id}, Is Admin: {is_admin}")
        return jsonify({'error': 'Token não fornecido'}), 400
    
    logger.info(f"Token recebido: {token}, User ID: {user_id}, Is Admin: {is_admin}")
    
    conn = get_db_connection()
    if is_admin:
        conn.execute('UPDATE users SET fcm_token = ? WHERE id = ?', (token, user_id))
    else:
        conn.execute('UPDATE members SET fcm_token = ? WHERE id = ?', (token, user_id))
    conn.commit()
    conn.close()
    
    return jsonify({'message': 'Token salvo com sucesso!'}), 200

@app.route('/firebase-messaging-sw.js')
def serve_service_worker():
    return app.send_static_file('firebase-messaging-sw.js')

# Rota para o manifest.json (necessário para PWA)
@app.route('/manifest.json')
def serve_manifest():
    manifest = {
        "name": "Ministério de Louvor",
        "short_name": "Ministério",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#D32F2F",
        "theme_color": "#D32F2F",
        "icons": [
            {
                "src": "/static/icon.png",
                "sizes": "192x192",
                "type": "image/png"
            },
            {
                "src": "/static/icon.png",
                "sizes": "512x512",
                "type": "image/png"
            }
        ]
    }
    return jsonify(manifest)

@socketio.on('connect')
def handle_connect():
    if 'user_id' in session:
        user_id = session['user_id']
        emit('join', {'room': f'user_{user_id}'})
        logger.info(f"Usuário {user_id} conectado ao SocketIO")

@app.route('/test_push', methods=['GET'])
def test_push():
    conn = get_db_connection()
    members = conn.execute('SELECT fcm_token FROM members WHERE fcm_token IS NOT NULL').fetchall()
    users = conn.execute('SELECT fcm_token FROM users WHERE fcm_token IS NOT NULL').fetchall()
    tokens = [m['fcm_token'] for m in members] + [u['fcm_token'] for u in users]
    conn.close()
    logger.info(f"Tokens para teste: {tokens}")
    if not tokens:
        return "Nenhum token disponível para teste"
    success = send_push_notification(tokens, "Teste", "Esta é uma notificação de teste!")
    return "Notificação enviada!" if success else "Falha ao enviar notificação"

if __name__ == '__main__':
    try:
        init_db()
        socketio.run(app, host='0.0.0.0', port=5000)
    except Exception as e:
        logger.error(f"Erro ao iniciar o aplicativo: {e}")
