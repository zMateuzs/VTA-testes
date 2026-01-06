# routes.py CORRIGIDO

from flask import request, jsonify, session, render_template, redirect, url_for
import psycopg2
import psycopg2.extras # Importante para o cursor como dicionário
from werkzeug.security import check_password_hash
import os

# Importa a instância 'app' do arquivo app.py
from app import app

# --- Configuração da Conexão com o Banco de Dados ---
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")

def get_db_connection():
    """Cria e retorna uma nova conexão com o banco de dados."""
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASS,
    )
    return conn

# --- ROTAS DE PÁGINAS E AUTENTICAÇÃO ---

# Rota para a página de Login (GET)
@app.route('/')
def login_page():
    return render_template('1. login_vta.html')

# Rota para processar o formulário de login (POST)
@app.route('/login', methods=['POST'])
def login():
    data = request.form
    email = data.get('email')
    senha = data.get('password')

    if not email or not senha:
        return jsonify({"message": "Email e senha são obrigatórios!"}), 400

    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        cur.execute("SELECT id, email, senha_hash, perfil FROM usuarios WHERE email = %s", (email,))
        user = cur.fetchone()
        
        cur.close()

        if user and check_password_hash(user['senha_hash'], senha):
            session['user_id'] = user['id']
            session['user_perfil'] = user['perfil']
            
            # Responde ao front-end com a URL de redirecionamento
            return jsonify({
                "message": "Login bem-sucedido! Redirecionando...", 
                "redirect_url": url_for('dashboard')
            }), 200
        else:
            return jsonify({"message": "Email/usuário ou senha incorretos."}), 401

    except Exception as e:
        print(f"Erro no login: {e}")
        return jsonify({"message": "Erro interno no servidor."}), 500
    finally:
        if conn:
            conn.close()

# Rota de Logout
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login_page'))

# --- ROTAS PROTEGIDAS (EXIGEM LOGIN) ---

# Rota do Dashboard
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login_page'))
    # Renderiza o arquivo HTML do dashboard
    return render_template('2. dashboard_vta.html')

# Rota da Agenda
@app.route('/agenda')
def agenda_page():
    if 'user_id' not in session:
        return redirect(url_for('login_page'))
    # Renderiza o arquivo HTML da agenda
    return render_template('3. agenda_vta.html')


# --- APIs auxiliares ---

def _require_login_json():
    if 'user_id' not in session:
        return jsonify({"message": "Não autenticado."}), 401
    return None


@app.route('/api/clientes', methods=['GET'])
def listar_clientes():
    """Retorna clientes ativos para preencher selects no front."""
    not_authed = _require_login_json()
    if not_authed:
        return not_authed

    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        cur.execute(
            """
            SELECT id, nome, email, telefone
            FROM clientes
            WHERE status IS NULL OR status <> 'inativo'
            ORDER BY nome ASC
            """
        )

        clientes = [dict(row) for row in cur.fetchall()]
        cur.close()
        return jsonify(clientes), 200

    except Exception as e:
        print(f"Erro ao listar clientes: {e}")
        return jsonify({"message": "Erro ao buscar clientes."}), 500
    finally:
        if conn:
            conn.close()


@app.route('/api/pets', methods=['GET'])
def listar_pets():
    """Retorna pets cadastrados, incluindo o tutor para filtro no front."""
    not_authed = _require_login_json()
    if not_authed:
        return not_authed

    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        cur.execute(
            """
            SELECT
                p.id,
                p.nome,
                p.especie,
                p.raca,
                p.sexo,
                p.tutor_id,
                COALESCE(c.nome, '') AS tutor_nome
            FROM pets p
            LEFT JOIN clientes c ON c.id = p.tutor_id
            ORDER BY p.nome ASC
            """
        )

        pets = [dict(row) for row in cur.fetchall()]
        cur.close()
        return jsonify(pets), 200

    except Exception as e:
        print(f"Erro ao listar pets: {e}")
        return jsonify({"message": "Erro ao buscar pets."}), 500
    finally:
        if conn:
            conn.close()

# Adicione aqui outras rotas para as demais páginas (clientes, pets, etc.)
# seguindo o mesmo modelo.