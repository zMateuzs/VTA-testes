from flask import render_template, request, redirect, url_for, flash, jsonify
from datetime import datetime
from flask import request, jsonify, session, render_template, redirect, url_for, send_file
import sqlite3
from werkzeug.security import check_password_hash, generate_password_hash
import os
from datetime import datetime, date
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors

# Importa a instância 'app' do arquivo app.py
from app import app

# --- Configuração da Conexão com o Banco de Dados ---
DB_FILE = 'agenda.db'

def get_db_connection():
    """Cria e retorna uma nova conexão com o banco de dados SQLite."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def update_appointment_statuses(conn):
    """Atualiza automaticamente o status dos agendamentos baseados na data e hora atuais."""
    try:
        cur = conn.cursor()
        today = date.today()
        today_str = today.isoformat()
        now = datetime.now()
        current_time_str = now.strftime('%H:%M')

        # 1. Passou do dia -> Realizado (se não cancelado/realizado)
        cur.execute("""
            UPDATE agendamentos 
            SET status = 'realizado' 
            WHERE data_agendamento < ? AND status NOT IN ('cancelado', 'realizado')
        """, (today_str,))

        # 2. Mesmo dia, passou do horário -> Confirmado (se agendado)
        cur.execute("""
            UPDATE agendamentos 
            SET status = 'confirmado' 
            WHERE data_agendamento = ? AND horario < ? AND status = 'agendado'
        """, (today_str, current_time_str))
        
        conn.commit()
        cur.close()
    except Exception as e:
        print(f"Erro na atualização automática de status: {e}")

# --- ROTAS DE PÁGINAS E AUTENTICAÇÃO ---

# Rota para a página de Landing (GET)
@app.route('/')
def landing_page():
    return render_template('0.Landing_page.html')

# Rota para a página de Login (GET)
@app.route('/login', methods=['GET'])
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
        cur = conn.cursor()
        
        cur.execute("SELECT id, email, senha_hash, perfil FROM usuarios WHERE email = ?", (email,))
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
    
    conn = None
    try:
        conn = get_db_connection()
        update_appointment_statuses(conn)
        cur = conn.cursor()
        
        # Data de hoje
        today = date.today()
        today_str = today.isoformat()
        
        # 1. Consultas Hoje (Total)
        cur.execute("SELECT COUNT(*) FROM agendamentos WHERE data_agendamento = ? AND status != 'cancelado'", (today_str,))
        consultas_hoje_count = cur.fetchone()[0]
        
        # 2. Clientes Ativos (Total de clientes únicos)
        cur.execute("SELECT COUNT(DISTINCT cliente) FROM agendamentos")
        clientes_ativos_count = cur.fetchone()[0]
        
        # 3. Salas Disponíveis e Ocupadas
        # Buscando agendamentos de hoje para calcular ocupação e listar na agenda
        cur.execute("SELECT * FROM agendamentos WHERE data_agendamento = ? ORDER BY horario", (today_str,))
        agendamentos_hoje = cur.fetchall()
        
        TOTAL_SALAS = 5 # Definindo um total fixo de salas para o sistema
        occupied_rooms = set()
        
        now = datetime.now()
        current_minutes = now.hour * 60 + now.minute
        
        agenda_items = []
        
        sala_nomes = {
            '1': 'Consultório 1',
            '2': 'Consultório 2',
            '3': 'Cirurgia',
            '4': 'Raio-X',
            'sala1': 'Consultório 1',
            'sala2': 'Consultório 2',
            'sala3': 'Cirurgia',
            'sala4': 'Raio-X'
        }
        
        for ag in agendamentos_hoje:
            sala_val = str(ag['sala'])
            sala_display = sala_nomes.get(sala_val, sala_val)
            
            # Processamento para Agenda de Hoje
            item = {
                'horario': str(ag['horario'])[:5],
                'pet': ag['pet'],
                'servico': ag['observacoes'] if ag['observacoes'] else 'Consulta',
                'sala': sala_display,
                'cliente': ag['cliente'],
                'veterinario': 'Dr. VTA' # Placeholder
            }
            agenda_items.append(item)
            
            # Cálculo de Salas Ocupadas (Assumindo duração de 1h)
            try:
                h_str = str(ag['horario'])
                parts = h_str.split(':')
                h = int(parts[0])
                m = int(parts[1])
                start_minutes = h * 60 + m
                
                # Se o horário atual está dentro da janela de 1h do agendamento
                if start_minutes <= current_minutes < start_minutes + 60:
                    occupied_rooms.add(ag['sala'])
            except Exception as e:
                print(f"Erro ao processar horário: {e}")
                pass
                
        salas_ocupadas_count = len(occupied_rooms)
        salas_disponiveis_count = max(0, TOTAL_SALAS - salas_ocupadas_count)
        
        # 4. Notificações
        cur.execute("SELECT * FROM notificacoes ORDER BY created_at DESC LIMIT 5")
        notificacoes = cur.fetchall()
        
        cur.close()

        return render_template('2. dashboard_vta.html', 
                            consultas_hoje=consultas_hoje_count,
                            clientes_ativos=clientes_ativos_count,
                            salas_disponiveis=salas_disponiveis_count,
                            salas_ocupadas=salas_ocupadas_count,
                            agenda_hoje=agenda_items,
                            notificacoes=notificacoes)
    except Exception as e:
        print(f"Erro no dashboard: {e}")
        # Em caso de erro, renderiza com valores zerados ou padrão
        return render_template('2. dashboard_vta.html', 
                            consultas_hoje=0,
                            clientes_ativos=0,
                            salas_disponiveis=5,
                            salas_ocupadas=0,
                            agenda_hoje=[],
                            notificacoes=[])
    finally:
        if conn:
            conn.close()

@app.route('/api/dashboard/stats')
def dashboard_stats():
    if 'user_id' not in session:
        return jsonify({"message": "Não autorizado"}), 401
    
    conn = None
    try:
        conn = get_db_connection()
        update_appointment_statuses(conn)
        cur = conn.cursor()
        
        today = date.today()
        today_str = today.isoformat()
        
        # 1. Consultas Hoje (Total) - Excluindo cancelados
        cur.execute("SELECT COUNT(*) FROM agendamentos WHERE data_agendamento = ? AND status != 'cancelado'", (today_str,))
        consultas_hoje_count = cur.fetchone()[0]
        
        # 2. Clientes Ativos
        cur.execute("SELECT COUNT(DISTINCT cliente) FROM agendamentos")
        clientes_ativos_count = cur.fetchone()[0]
        
        # 3. Salas
        cur.execute("SELECT * FROM agendamentos WHERE data_agendamento = ? AND status != 'cancelado' ORDER BY horario", (today_str,))
        agendamentos_hoje = cur.fetchall()
        
        TOTAL_SALAS = 5
        occupied_rooms = set()
        now = datetime.now()
        current_minutes = now.hour * 60 + now.minute
        
        for ag in agendamentos_hoje:
            try:
                h_str = str(ag['horario'])
                parts = h_str.split(':')
                h = int(parts[0])
                m = int(parts[1])
                start_minutes = h * 60 + m
                if start_minutes <= current_minutes < start_minutes + 60:
                    occupied_rooms.add(ag['sala'])
            except:
                pass
                
        salas_ocupadas_count = len(occupied_rooms)
        salas_disponiveis_count = max(0, TOTAL_SALAS - salas_ocupadas_count)
        
        cur.close()
        
        return jsonify({
            "consultas_hoje": consultas_hoje_count,
            "clientes_ativos": clientes_ativos_count,
            "salas_disponiveis": salas_disponiveis_count,
            "salas_ocupadas": salas_ocupadas_count
        })
    except Exception as e:
        print(f"Erro API stats: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            conn.close()

# Rota da Agenda
@app.route('/agenda')
def agenda_page():
    if 'user_id' not in session:
        return redirect(url_for('login_page'))
    # Renderiza o arquivo HTML da agenda
    return render_template('3. agenda_vta.html')

# Nova rota para Agendamento (Novo / Editar)
@app.route('/agendamento')
def agendamento_page():
    if 'user_id' not in session:
        return redirect(url_for('login_page'))
    return render_template('4. agendamento_vta.html')

# Rota dos Pets
@app.route('/pets')
def pets_page():
    if 'user_id' not in session:
        return redirect(url_for('login_page'))
    return render_template('6. pets_vta.html')

# Nova rota para Clientes
@app.route('/clientes')
def clientes_page():
    if 'user_id' not in session:
        return redirect(url_for('login_page'))
    
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status')
    per_page = 10
    offset = (page - 1) * per_page
    
    conn = get_db_connection()
    
    # Base query for clients
    query = 'SELECT * FROM clientes'
    count_query = 'SELECT COUNT(*) FROM clientes'
    params = []
    
    if status_filter and status_filter in ['active', 'inactive']:
        query += ' WHERE status = ?'
        count_query += ' WHERE status = ?'
        params.append(status_filter)
        
    query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
    query_params = params + [per_page, offset]
    
    # Fetch paginated clients
    clients = conn.execute(query, query_params).fetchall()
    
    # Filtered count for pagination
    filtered_count = conn.execute(count_query, params).fetchone()[0]
    
    # 1. Total Clients (Global)
    all_clients_count = conn.execute('SELECT COUNT(*) FROM clientes').fetchone()[0]
    
    # Calculate total pages
    total_pages = (filtered_count + per_page - 1) // per_page
    
    # 2. New Clients (Current Month)
    current_month = datetime.now().strftime('%Y-%m')
    # Note: created_at is TIMESTAMP, strftime works on it in SQLite
    new_clients = conn.execute("SELECT COUNT(*) FROM clientes WHERE strftime('%Y-%m', created_at) = ?", (current_month,)).fetchone()[0]
    
    # 3. Active Clients
    active_clients = conn.execute("SELECT COUNT(*) FROM clientes WHERE status = 'active'").fetchone()[0]
    
    # 4. Recurring Clients (> 1 appointment in current year)
    current_year = datetime.now().strftime('%Y')
    # We count distinct clients in agendamentos who have > 1 appointment this year
    recurring_clients = conn.execute("""
        SELECT COUNT(*) FROM (
            SELECT cliente 
            FROM agendamentos 
            WHERE strftime('%Y', data_agendamento) = ?
            GROUP BY cliente
            HAVING COUNT(*) > 1
        )
    """, (current_year,)).fetchone()[0]
    
    conn.close()
    
    return render_template('5. clientes_vta.html', 
                           clients=clients,
                           total_clients=filtered_count,
                           all_clients_count=all_clients_count,
                           new_clients=new_clients,
                           active_clients=active_clients,
                           recurring_clients=recurring_clients,
                           page=page,
                           total_pages=total_pages,
                           per_page=per_page,
                           current_status=status_filter)

@app.route('/api/clientes/search')
def search_clientes():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    query = request.args.get('q', '').lower()
    if not query:
        return jsonify([])
        
    conn = get_db_connection()
    # Search by name, email or cpf
    # Using LIKE for partial match
    sql = """
        SELECT id, nome, email, telefone, cpf, observacoes 
        FROM clientes 
        WHERE lower(nome) LIKE ? OR lower(email) LIKE ? OR cpf LIKE ?
        LIMIT 10
    """
    search_term = f"%{query}%"
    clients = conn.execute(sql, (search_term, search_term, search_term)).fetchall()
    conn.close()
    
    result = []
    for client in clients:
        result.append({
            'id': client['id'],
            'nome': client['nome'],
            'email': client['email'],
            'telefone': client['telefone'],
            'cpf': client['cpf'],
            'observacoes': client['observacoes']
        })
        
    return jsonify(result)

@app.route('/api/clientes', methods=['POST'])
def create_cliente():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.json
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO clientes (nome, email, telefone, cpf, data_nascimento, endereco, observacoes, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get('name'),
            data.get('email'),
            data.get('phone'),
            data.get('cpf'),
            data.get('birthDate'),
            data.get('address'),
            data.get('notes'),
            data.get('status', 'active')
        ))
        conn.commit()
        new_id = cur.lastrowid
        return jsonify({'success': True, 'id': new_id})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/clientes/<int:client_id>', methods=['PUT'])
def update_cliente(client_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.json
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            UPDATE clientes 
            SET nome=?, email=?, telefone=?, cpf=?, data_nascimento=?, endereco=?, observacoes=?, status=?
            WHERE id=?
        """, (
            data.get('name'),
            data.get('email'),
            data.get('phone'),
            data.get('cpf'),
            data.get('birthDate'),
            data.get('address'),
            data.get('notes'),
            data.get('status'),
            client_id
        ))
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/clientes/<int:client_id>', methods=['DELETE'])
def delete_cliente(client_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    conn = get_db_connection()
    try:
        conn.execute('DELETE FROM clientes WHERE id = ?', (client_id,))
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/clientes/exportar')
def export_clientes():
    if 'user_id' not in session:
        return redirect(url_for('login_page'))

    status_filter = request.args.get('status')
    conn = get_db_connection()
    
    query = 'SELECT * FROM clientes'
    params = []
    
    if status_filter and status_filter in ['active', 'inactive']:
        query += ' WHERE status = ?'
        params.append(status_filter)
        
    query += ' ORDER BY nome'
    
    clients = conn.execute(query, params).fetchall()
    conn.close()

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # Logo
    logo_path = os.path.join(os.path.dirname(__file__), 'static', 'img', 'logo.png')
    if os.path.exists(logo_path):
        try:
            c.drawImage(logo_path, 30, height - 80, width=50, height=50, preserveAspectRatio=True, mask='auto')
        except Exception as e:
            print(f"Erro ao carregar logo: {e}")

    # Title
    c.setFont("Helvetica-Bold", 20)
    c.drawString(100, height - 50, "Relatório de Clientes - Agenda VTA")
    c.setFont("Helvetica", 10)
    c.drawString(100, height - 70, f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}")

    # Table Header
    y = height - 120
    c.setFont("Helvetica-Bold", 10)
    c.drawString(30, y, "Nome")
    c.drawString(200, y, "Email")
    c.drawString(380, y, "Telefone")
    c.drawString(500, y, "Status")
    
    y -= 10
    c.line(30, y + 5, 580, y + 5)
    y -= 15

    # Table Content
    c.setFont("Helvetica", 9)
    for client in clients:
        if y < 50:
            c.showPage()
            y = height - 50
        
        c.drawString(30, y, str(client['nome'])[:35])
        c.drawString(200, y, str(client['email'])[:35])
        c.drawString(380, y, str(client['telefone']))
        
        status = "Ativo" if client['status'] == 'active' else "Inativo"
        c.drawString(500, y, status)
        
        y -= 15

    c.save()
    buffer.seek(0)
    
    return send_file(buffer, as_attachment=True, download_name=f'clientes_vta_{datetime.now().strftime("%Y%m%d")}.pdf', mimetype='application/pdf')

# Nova rota para Salas
@app.route('/salas')
def salas_page():
    if 'user_id' not in session:
        return redirect(url_for('login_page'))
    return render_template('8. salas_vta.html')

# Rota para Relatórios ADM
@app.route('/relatorios')
def relatorios_dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login_page'))
    return render_template('9. relatorios_dashboard.html')

# Nova rota para Relatórios Pets
@app.route('/relatorios/pets')
def relatorios_pets():
    if 'user_id' not in session:
        return redirect(url_for('login_page'))
        
    conn = get_db_connection()
    
    # Buscar todos os pets com dados dos tutores
    query_pets = '''
        SELECT p.*, c.nome as tutor_nome, c.telefone, c.email, c.endereco 
        FROM pets p 
        LEFT JOIN clientes c ON p.tutor_id = c.id
    '''
    pets_db = conn.execute(query_pets).fetchall()
    
    pets_data = []
    for pet in pets_db:
        # Calcular idade aproximada
        idade = "Desconhecida"
        if pet['data_nascimento']:
            try:
                nasc = datetime.strptime(pet['data_nascimento'], '%Y-%m-%d').date()
                hoje = datetime.now().date()
                anos = hoje.year - nasc.year - ((hoje.month, hoje.day) < (nasc.month, nasc.day))
                idade = f"{anos} anos"
            except:
                pass

        # Buscar histórico de agendamentos deste pet
        query_hist = '''
            SELECT * FROM agendamentos 
            WHERE pet = ? 
            ORDER BY data_agendamento DESC, horario DESC
        '''
        historico_db = conn.execute(query_hist, (pet['nome'],)).fetchall()
        
        historico = []
        ultima_consulta = None
        
        for h in historico_db:
            if not ultima_consulta:
                ultima_consulta = h['data_agendamento']
                
            historico.append({
                'data': h['data_agendamento'],
                'tipo': 'consulta', 
                'titulo': f"Agendamento em {h['sala']}",
                'descricao': h['observacoes'] or "Sem observações"
            })

        pets_data.append({
            'id': pet['id'],
            'petNome': pet['nome'],
            'clienteNome': pet['tutor_nome'] or "Sem Tutor",
            'especie': pet['especie'],
            'raca': pet['raca'],
            'idade': idade,
            'ultimaConsulta': ultima_consulta or "Nenhuma",
            'totalConsultas': len(historico),
            'status': 'ativo', 
            'telefone': pet['telefone'] or "",
            'email': pet['email'] or "",
            'endereco': pet['endereco'] or "",
            'peso': f"{pet['peso']} kg" if pet['peso'] else "-",
            'nascimento': pet['data_nascimento'],
            'historico': historico
        })
    
    conn.close()
    return render_template('10. relatorios_pets.html', pets=pets_data)

# Nova rota para Usuários
@app.route('/usuarios')
def usuarios_page():
    if 'user_id' not in session:
        return redirect(url_for('login_page'))
    return render_template('7. usuarios_vta.html')

# --- API DE USUÁRIOS ---

@app.route('/api/usuarios', methods=['GET'])
def get_usuarios():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    conn = get_db_connection()
    
    # Filtros
    query = request.args.get('q', '').lower()
    role = request.args.get('role')
    status = request.args.get('status')
    
    sql = "SELECT id, nome, email, cpf, telefone, perfil, status, ultimo_acesso FROM usuarios WHERE 1=1"
    params = []
    
    if query:
        sql += " AND (lower(nome) LIKE ? OR lower(email) LIKE ?)"
        params.extend([f"%{query}%", f"%{query}%"])
        
    if role:
        sql += " AND perfil = ?"
        params.append(role)
        
    if status:
        sql += " AND status = ?"
        params.append(status)
        
    sql += " ORDER BY nome"
    
    users = conn.execute(sql, params).fetchall()
    conn.close()
    
    result = []
    for user in users:
        result.append({
            'id': user['id'],
            'name': user['nome'] or 'Sem Nome',
            'email': user['email'],
            'cpf': user['cpf'],
            'phone': user['telefone'],
            'role': user['perfil'],
            'status': user['status'],
            'lastAccess': user['ultimo_acesso'] or 'Nunca'
        })
        
    return jsonify(result)

@app.route('/api/usuarios', methods=['POST'])
def create_usuario():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.json
    
    # Validações básicas
    if not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Email e senha são obrigatórios'}), 400
        
    conn = get_db_connection()
    try:
        # Verificar se email já existe
        existing = conn.execute("SELECT id FROM usuarios WHERE email = ?", (data.get('email'),)).fetchone()
        if existing:
            return jsonify({'error': 'Email já cadastrado'}), 400
            
        senha_hash = generate_password_hash(data.get('password'))
        
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO usuarios (nome, email, senha_hash, cpf, telefone, perfil, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get('name'),
            data.get('email'),
            senha_hash,
            data.get('cpf'),
            data.get('phone'),
            data.get('role', 'usuario'),
            data.get('status', 'ativo')
        ))
        conn.commit()
        new_id = cur.lastrowid
        return jsonify({'success': True, 'id': new_id})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/usuarios/<int:user_id>', methods=['PUT'])
def update_usuario(user_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.json
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        
        # Se senha foi fornecida, atualiza também a senha
        if data.get('password'):
            senha_hash = generate_password_hash(data.get('password'))
            cur.execute("""
                UPDATE usuarios 
                SET nome=?, email=?, senha_hash=?, cpf=?, telefone=?, perfil=?, status=?
                WHERE id=?
            """, (
                data.get('name'),
                data.get('email'),
                senha_hash,
                data.get('cpf'),
                data.get('phone'),
                data.get('role'),
                data.get('status'),
                user_id
            ))
        else:
            cur.execute("""
                UPDATE usuarios 
                SET nome=?, email=?, cpf=?, telefone=?, perfil=?, status=?
                WHERE id=?
            """, (
                data.get('name'),
                data.get('email'),
                data.get('cpf'),
                data.get('phone'),
                data.get('role'),
                data.get('status'),
                user_id
            ))
            
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/usuarios/<int:user_id>', methods=['DELETE'])
def delete_usuario(user_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
        
    # Não permitir excluir o próprio usuário logado
    if user_id == session.get('user_id'):
        return jsonify({'error': 'Não é possível excluir o próprio usuário'}), 400
    
    conn = get_db_connection()
    try:
        conn.execute('DELETE FROM usuarios WHERE id = ?', (user_id,))
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


# Rota para Gerar Relatório PDF de Agendamentos
@app.route('/relatorios/agendamentos-pdf')
def gerar_relatorio_agendamentos_pdf():
    if 'user_id' not in session:
        return redirect(url_for('login_page'))
    
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Buscar todos os agendamentos ordenados por data e horário
        cur.execute("SELECT * FROM agendamentos ORDER BY data_agendamento DESC, horario ASC")
        agendamentos = cur.fetchall()
        
        cur.close()
        
        # --- Geração do PDF ---
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter
        
        # Logo (Simulado com texto/círculo se não tiver imagem, ou tentar carregar imagem)
        # Tenta carregar a imagem da logo se existir
        logo_path = os.path.join(app.static_folder, 'img', 'logo.png') # Ajuste o caminho conforme necessário
        if os.path.exists(logo_path):
            try:
                c.drawImage(logo_path, 50, height - 80, width=50, height=50, mask='auto')
            except:
                pass
        else:
            # Desenha um placeholder se não tiver imagem
            c.setStrokeColor(colors.green)
            c.setFillColor(colors.white)
            c.circle(75, height - 55, 25, fill=1)
            c.setFillColor(colors.green)
            c.setFont("Helvetica-Bold", 14)
            c.drawCentredString(75, height - 60, "VTA")

        # Cabeçalho
        c.setFillColor(colors.black)
        c.setFont("Helvetica-Bold", 20)
        c.drawString(120, height - 50, "Relatório de Agendamentos")
        c.setFont("Helvetica", 12)
        c.drawString(120, height - 70, "VTA - Vet Assistance")
        
        c.setFont("Helvetica", 10)
        today_fmt = date.today().strftime('%d/%m/%Y')
        c.drawRightString(width - 50, height - 50, f"Data de Emissão: {today_fmt}")
        
        # Linha separadora
        c.setStrokeColor(colors.gray)
        c.line(50, height - 90, width - 50, height - 90)
        
        y = height - 120
        
        # Cabeçalho da Tabela
        c.setFillColor(colors.black)
        c.setFont("Helvetica-Bold", 8)
        # Colunas: Data, Horário, Sala, Cliente, Pet, Serviço, Veterinário, Status
        c.drawString(30, y, "Data")
        c.drawString(85, y, "Horário")
        c.drawString(125, y, "Sala")
        c.drawString(165, y, "Cliente")
        c.drawString(265, y, "Pet")
        c.drawString(335, y, "Serviço")
        c.drawString(415, y, "Veterinário")
        c.drawString(500, y, "Status")
        
        y -= 10
        c.line(30, y, width - 30, y)
        y -= 20
        
        c.setFont("Helvetica", 8)
        
        sala_nomes = {
            '1': 'Sala 1', '2': 'Sala 2', '3': 'Cirurgia', '4': 'Raio-X',
            'sala1': 'Sala 1', 'sala2': 'Sala 2', 'sala3': 'Cirurgia', 'sala4': 'Raio-X'
        }

        for ag in agendamentos:
            if y < 50: # Nova página
                c.showPage()
                y = height - 50
                # Repetir cabeçalho na nova página
                c.setFont("Helvetica-Bold", 8)
                c.drawString(30, y, "Data")
                c.drawString(85, y, "Horário")
                c.drawString(125, y, "Sala")
                c.drawString(165, y, "Cliente")
                c.drawString(265, y, "Pet")
                c.drawString(335, y, "Serviço")
                c.drawString(415, y, "Veterinário")
                c.drawString(500, y, "Status")
                y -= 10
                c.line(30, y, width - 30, y)
                y -= 20
                c.setFont("Helvetica", 8)
            
            # Formatar Data
            try:
                data_obj = datetime.strptime(str(ag['data_agendamento']), '%Y-%m-%d')
                data_fmt = data_obj.strftime('%d/%m/%Y')
            except:
                data_fmt = str(ag['data_agendamento'])

            # Extrair serviço e veterinário de observações
            obs = ag['observacoes'] or ''
            servico = '-'
            veterinario = '-'
            
            if 'Serviço:' in obs:
                try:
                    servico = obs.split('Serviço:')[1].split(',')[0].strip()
                except:
                    pass
            
            if 'Vet:' in obs:
                try:
                    # Tenta pegar o texto após 'Vet:' até o próximo ponto ou fim da string
                    vet_part = obs.split('Vet:')[1]
                    if '.' in vet_part:
                        veterinario = vet_part.split('.')[0].strip()
                    else:
                        veterinario = vet_part.strip()
                except:
                    pass
            
            # Formatar Sala
            sala_raw = str(ag['sala']).lower()
            sala_fmt = sala_nomes.get(sala_raw, ag['sala'])

            c.drawString(30, y, data_fmt)
            c.drawString(85, y, str(ag['horario'])[:5])
            c.drawString(125, y, str(sala_fmt)[:10])
            c.drawString(165, y, str(ag['cliente'])[:20])
            c.drawString(265, y, str(ag['pet'])[:15])
            c.drawString(335, y, servico[:15])
            c.drawString(415, y, veterinario[:15])
            c.drawString(500, y, str(ag['status']).capitalize())
            
            y -= 15
            
        c.save()
        buffer.seek(0)
        
        today_str = date.today().strftime('%Y-%m-%d')
        return send_file(buffer, as_attachment=True, download_name=f'relatorio_agendamentos_{today_str}.pdf', mimetype='application/pdf')

    except Exception as e:
        print(f"Erro ao gerar PDF de agendamentos: {e}")
        return jsonify({"message": "Erro ao gerar relatório PDF"}), 500
    finally:
        if conn:
            conn.close()

# Rota para Gerar Relatório PDF do Dashboard
@app.route('/relatorios/dashboard-pdf')
def gerar_relatorio_dashboard_pdf():
    if 'user_id' not in session:
        return redirect(url_for('login_page'))
    
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Data de hoje
        today = date.today()
        today_str = today.isoformat()
        today_fmt = today.strftime('%d/%m/%Y')
        
        # 1. Consultas Hoje (Total)
        cur.execute("SELECT COUNT(*) FROM agendamentos WHERE data_agendamento = ?", (today_str,))
        consultas_hoje_count = cur.fetchone()[0]
        
        # 2. Clientes Ativos (Total de clientes únicos)
        cur.execute("SELECT COUNT(DISTINCT cliente) FROM agendamentos")
        clientes_ativos_count = cur.fetchone()[0]
        
        # 3. Salas Disponíveis e Ocupadas
        cur.execute("SELECT * FROM agendamentos WHERE data_agendamento = ? ORDER BY horario", (today_str,))
        agendamentos_hoje = cur.fetchall()
        
        TOTAL_SALAS = 5
        occupied_rooms = set()
        now = datetime.now()
        current_minutes = now.hour * 60 + now.minute
        
        agenda_items = []
        sala_nomes = {
            '1': 'Consultório 1', '2': 'Consultório 2', '3': 'Cirurgia', '4': 'Raio-X',
            'sala1': 'Consultório 1', 'sala2': 'Consultório 2', 'sala3': 'Cirurgia', 'sala4': 'Raio-X'
        }
        
        for ag in agendamentos_hoje:
            sala_val = str(ag['sala'])
            sala_display = sala_nomes.get(sala_val, sala_val)
            
            item = {
                'horario': str(ag['horario'])[:5],
                'pet': ag['pet'],
                'servico': ag['observacoes'] if ag['observacoes'] else 'Consulta',
                'sala': sala_display,
                'cliente': ag['cliente']
            }
            agenda_items.append(item)
            
            try:
                h_str = str(ag['horario'])
                parts = h_str.split(':')
                h = int(parts[0])
                m = int(parts[1])
                start_minutes = h * 60 + m
                if start_minutes <= current_minutes < start_minutes + 60:
                    occupied_rooms.add(ag['sala'])
            except:
                pass
                
        salas_ocupadas_count = len(occupied_rooms)
        salas_disponiveis_count = max(0, TOTAL_SALAS - salas_ocupadas_count)
        
        cur.close()
        
        # --- Geração do PDF ---
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter
        
        # Cabeçalho
        c.setFont("Helvetica-Bold", 24)
        c.drawString(50, height - 50, "Relatório do Dashboard - Agenda VTA")
        
        c.setFont("Helvetica", 12)
        c.drawString(50, height - 80, f"Data: {today_fmt}")
        c.drawString(50, height - 100, f"Gerado por: Administrador") # Poderia pegar da sessão
        
        # Linha separadora
        c.line(50, height - 110, width - 50, height - 110)
        
        # Resumo (Stats)
        y = height - 150
        c.setFont("Helvetica-Bold", 16)
        c.drawString(50, y, "Resumo do Dia")
        
        y -= 30
        c.setFont("Helvetica", 12)
        c.drawString(50, y, f"Consultas Hoje: {consultas_hoje_count}")
        c.drawString(250, y, f"Salas Disponíveis: {salas_disponiveis_count}")
        
        y -= 20
        c.drawString(50, y, f"Clientes Ativos: {clientes_ativos_count}")
        c.drawString(250, y, f"Salas Ocupadas: {salas_ocupadas_count}")
        
        # Agenda de Hoje
        y -= 50
        c.setFont("Helvetica-Bold", 16)
        c.drawString(50, y, "Agenda de Hoje")
        
        y -= 30
        # Cabeçalho da Tabela
        c.setFont("Helvetica-Bold", 10)
        c.drawString(50, y, "Horário")
        c.drawString(120, y, "Pet")
        c.drawString(220, y, "Serviço")
        c.drawString(350, y, "Sala")
        c.drawString(450, y, "Cliente")
        
        y -= 10
        c.line(50, y, width - 50, y)
        y -= 20
        
        c.setFont("Helvetica", 10)
        if not agenda_items:
            c.drawString(50, y, "Nenhuma consulta agendada para hoje.")
        else:
            for item in agenda_items:
                if y < 50: # Nova página se acabar o espaço
                    c.showPage()
                    y = height - 50
                
                c.drawString(50, y, item['horario'])
                c.drawString(120, y, str(item['pet'])[:15])
                c.drawString(220, y, str(item['servico'])[:20])
                c.drawString(350, y, str(item['sala'])[:15])
                c.drawString(450, y, str(item['cliente'])[:20])
                y -= 20
                
        c.save()
        buffer.seek(0)
        
        return send_file(buffer, as_attachment=True, download_name=f'relatorio_dashboard_{today_str}.pdf', mimetype='application/pdf')

    except Exception as e:
        print(f"Erro ao gerar PDF: {e}")
        return jsonify({"message": "Erro ao gerar relatório PDF"}), 500
    finally:
        if conn:
            conn.close()

# --- API AGENDAMENTOS ---

@app.route('/api/agendamentos', methods=['GET'])
def get_agendamentos():
    if 'user_id' not in session:
        return jsonify({"message": "Não autorizado"}), 401
    
    conn = None
    try:
        conn = get_db_connection()
        update_appointment_statuses(conn)
        cur = conn.cursor()
        cur.execute("SELECT * FROM agendamentos ORDER BY data_agendamento, horario")
        agendamentos = cur.fetchall()
        
        # Converter objetos datetime/date/time para string e formatar para o frontend
        result = []
        for agendamento in agendamentos:
            item = {
                'id': agendamento['id'],
                'cliente': agendamento['cliente'],
                'pet': agendamento['pet'],
                'sala': agendamento['sala'],
                'data': str(agendamento['data_agendamento']),
                'horario': str(agendamento['horario'])[:5], # Pega HH:MM
                'status': agendamento['status'],
                'obs': agendamento['observacoes']
            }
            
            if agendamento['checkin_realizado']:
                item['checkin'] = {
                    'realizado': True,
                    'horario': str(agendamento['checkin_horario'])
                }
            else:
                item['checkin'] = None
                
            result.append(item)
                
        cur.close()
        return jsonify(result), 200
    except Exception as e:
        print(f"Erro ao buscar agendamentos: {e}")
        return jsonify({"message": "Erro ao buscar agendamentos"}), 500
    finally:
        if conn:
            conn.close()

@app.route('/api/agendamentos', methods=['POST'])
def create_agendamento():
    if 'user_id' not in session:
        return jsonify({"message": "Não autorizado"}), 401
        
    data = request.json
    
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            INSERT INTO agendamentos (cliente, cliente_id, pet, sala, data_agendamento, horario, status, observacoes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get('cliente'),
            data.get('cliente_id'), # Pode ser None
            data.get('pet'),
            data.get('sala'),
            data.get('data'),
            data.get('horario'),
            data.get('status', 'agendado'),
            data.get('obs')
        ))
        
        new_id = cur.lastrowid
        
        # Criar notificação
        titulo = "Novo Agendamento"
        # Formatar data para DD/MM/AAAA se possível, mas usando string direta por enquanto
        try:
            data_obj = datetime.strptime(data.get('data'), '%Y-%m-%d')
            data_fmt = data_obj.strftime('%d/%m/%Y')
        except:
            data_fmt = data.get('data')
            
        msg = f"{data.get('pet')} - {data_fmt} às {data.get('horario')}"
        cur.execute("INSERT INTO notificacoes (titulo, mensagem, tipo) VALUES (?, ?, ?)", (titulo, msg, 'info'))
        
        conn.commit()
        cur.close()
        
        return jsonify({"message": "Agendamento criado com sucesso", "id": new_id}), 201
    except Exception as e:
        print(f"Erro ao criar agendamento: {e}")
        return jsonify({"message": "Erro ao criar agendamento"}), 500
    finally:
        if conn:
            conn.close()

@app.route('/api/agendamentos/<int:id>', methods=['PUT'])
def update_agendamento(id):
    if 'user_id' not in session:
        return jsonify({"message": "Não autorizado"}), 401
        
    data = request.json
    
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Verifica se é uma atualização de check-in ou edição completa
        if 'checkin' in data:
            checkin = data['checkin']
            if checkin:
                cur.execute("""
                    UPDATE agendamentos 
                    SET checkin_realizado = ?, checkin_horario = ?, status = ?
                    WHERE id = ?
                """, (True, checkin.get('horario'), 'confirmado', id))
                
                # Notificação Check-in
                cur.execute("SELECT pet FROM agendamentos WHERE id = ?", (id,))
                row = cur.fetchone()
                if row:
                    cur.execute("INSERT INTO notificacoes (titulo, mensagem, tipo) VALUES (?, ?, ?)", 
                               ("Check-in Realizado", f"{row['pet']}", 'success'))
            else:
                cur.execute("""
                    UPDATE agendamentos 
                    SET checkin_realizado = ?, checkin_horario = NULL, status = ?
                    WHERE id = ?
                """, (False, 'agendado', id))
        else:
            cur.execute("""
                UPDATE agendamentos 
                SET cliente = ?, pet = ?, sala = ?, data_agendamento = ?, horario = ?, status = ?, observacoes = ?
                WHERE id = ?
            """, (
                data.get('cliente'),
                data.get('pet'),
                data.get('sala'),
                data.get('data'),
                data.get('horario'),
                data.get('status'),
                data.get('obs'),
                id
            ))
            
            # Notificação Edição
            status = data.get('status')
            titulo = "Agendamento Atualizado"
            msg = f"{data.get('pet')}"
            tipo = 'info'
            
            if status == 'confirmado':
                titulo = "Consulta Confirmada"
                tipo = 'success'
            elif status == 'cancelado':
                titulo = "Consulta Cancelada"
                tipo = 'warning'
            elif status == 'realizado':
                titulo = "Consulta Realizada"
                tipo = 'success'
                
            cur.execute("INSERT INTO notificacoes (titulo, mensagem, tipo) VALUES (?, ?, ?)", (titulo, msg, tipo))
            
        conn.commit()
        cur.close()
        
        return jsonify({"message": "Agendamento atualizado com sucesso"}), 200
    except Exception as e:
        print(f"Erro ao atualizar agendamento: {e}")
        return jsonify({"message": "Erro ao atualizar agendamento"}), 500
    finally:
        if conn:
            conn.close()

@app.route('/api/agendamentos/<int:id>', methods=['DELETE'])
def delete_agendamento(id):
    if 'user_id' not in session:
        return jsonify({"message": "Não autorizado"}), 401
        
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Buscar nome do pet antes de excluir para a notificação
        cur.execute("SELECT pet FROM agendamentos WHERE id = ?", (id,))
        row = cur.fetchone()
        pet_name = row['pet'] if row else "Desconhecido"
        
        cur.execute("DELETE FROM agendamentos WHERE id = ?", (id,))
        
        # Notificação
        cur.execute("INSERT INTO notificacoes (titulo, mensagem, tipo) VALUES (?, ?, ?)", 
                   ("Agendamento Excluído", f"{pet_name}", 'warning'))
        
        conn.commit()
        cur.close()
        
        return jsonify({"message": "Agendamento excluído com sucesso"}), 200
    except Exception as e:
        print(f"Erro ao excluir agendamento: {e}")
        return jsonify({"message": "Erro ao excluir agendamento"}), 500
    finally:
        if conn:
            conn.close()

# --- ROTAS DE PETS ---

@app.route('/api/pets', methods=['GET'])
def list_pets():
    if 'user_id' not in session:
        return jsonify({"message": "Não autorizado"}), 401
    
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Join with clientes to get tutor name
        cur.execute("""
            SELECT p.*, c.nome as tutor_nome 
            FROM pets p
            LEFT JOIN clientes c ON p.tutor_id = c.id
            ORDER BY p.nome
        """)
        pets = cur.fetchall()
        
        pets_list = []
        for pet in pets:
            # Calculate age (simplified)
            idade = "Desconhecida"
            if pet['data_nascimento']:
                try:
                    dob = datetime.strptime(pet['data_nascimento'], '%Y-%m-%d').date()
                    today = date.today()
                    years = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
                    idade = f"{years} anos"
                except:
                    pass

            pets_list.append({
                'id': pet['id'],
                'nome': pet['nome'],
                'especie': pet['especie'],
                'raca': pet['raca'],
                'sexo': pet['sexo'],
                'data_nascimento': pet['data_nascimento'],
                'peso': pet['peso'],
                'cor': pet['cor'],
                'tutor_id': pet['tutor_id'],
                'tutor_nome': pet['tutor_nome'] or 'Sem Tutor',
                'observacoes': pet['observacoes'],
                'idade': idade
            })
            
        cur.close()
        return jsonify(pets_list), 200
    except Exception as e:
        print(f"Erro ao listar pets: {e}")
        return jsonify({"message": "Erro ao listar pets"}), 500
    finally:
        if conn:
            conn.close()

@app.route('/api/pets', methods=['POST'])
def create_pet():
    if 'user_id' not in session:
        return jsonify({"message": "Não autorizado"}), 401
    
    data = request.json
    conn = None
    try:
        # Helper to convert empty strings to None
        def clean(val):
            return val if val and str(val).strip() != "" else None

        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            INSERT INTO pets (nome, especie, raca, sexo, data_nascimento, peso, cor, tutor_id, observacoes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get('nome'),
            data.get('especie'),
            clean(data.get('raca')),
            data.get('sexo'),
            clean(data.get('dataNascimento')),
            clean(data.get('peso')),
            clean(data.get('cor')),
            data.get('tutor'),
            clean(data.get('observacoes'))
        ))
        
        conn.commit()
        pet_id = cur.lastrowid
        cur.close()
        
        return jsonify({"message": "Pet criado com sucesso", "id": pet_id}), 201
    except Exception as e:
        print(f"Erro ao criar pet: {e}")
        return jsonify({"message": f"Erro ao criar pet: {str(e)}"}), 500
    finally:
        if conn:
            conn.close()

@app.route('/api/pets/<int:id>', methods=['PUT'])
def update_pet(id):
    if 'user_id' not in session:
        return jsonify({"message": "Não autorizado"}), 401
    
    data = request.json
    conn = None
    try:
        # Helper to convert empty strings to None
        def clean(val):
            return val if val and str(val).strip() != "" else None

        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            UPDATE pets 
            SET nome=?, especie=?, raca=?, sexo=?, data_nascimento=?, peso=?, cor=?, tutor_id=?, observacoes=?
            WHERE id=?
        """, (
            data.get('nome'),
            data.get('especie'),
            clean(data.get('raca')),
            data.get('sexo'),
            clean(data.get('dataNascimento')),
            clean(data.get('peso')),
            clean(data.get('cor')),
            data.get('tutor'),
            clean(data.get('observacoes')),
            id
        ))
        
        conn.commit()
        cur.close()
        
        return jsonify({"message": "Pet atualizado com sucesso"}), 200
    except Exception as e:
        print(f"Erro ao atualizar pet: {e}")
        return jsonify({"message": f"Erro ao atualizar pet: {str(e)}"}), 500
    finally:
        if conn:
            conn.close()

@app.route('/api/pets/<int:id>', methods=['DELETE'])
def delete_pet(id):
    if 'user_id' not in session:
        return jsonify({"message": "Não autorizado"}), 401
    
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("DELETE FROM pets WHERE id = ?", (id,))
        
        conn.commit()
        cur.close()
        
        return jsonify({"message": "Pet excluído com sucesso"}), 200
    except Exception as e:
        print(f"Erro ao excluir pet: {e}")
        return jsonify({"message": "Erro ao excluir pet"}), 500
    finally:
        if conn:
            conn.close()

@app.route('/api/clientes/all', methods=['GET'])
def list_all_clientes():
    if 'user_id' not in session:
        return jsonify({"message": "Não autorizado"}), 401
        
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, nome FROM clientes ORDER BY nome")
        clientes = cur.fetchall()
        
        result = [{'id': c['id'], 'nome': c['nome']} for c in clientes]
        
        cur.close()
        return jsonify(result), 200
    except Exception as e:
        print(f"Erro ao listar clientes: {e}")
        return jsonify({"message": "Erro ao listar clientes"}), 500
    finally:
        if conn:
            conn.close()
