from flask import request, jsonify, session, render_template, redirect, url_for
import sqlite3
from werkzeug.security import check_password_hash
import os
from datetime import datetime, date

# Importa a instância 'app' do arquivo app.py
from app import app

# --- Configuração da Conexão com o Banco de Dados ---
DB_FILE = 'agenda.db'

def get_db_connection():
    """Cria e retorna uma nova conexão com o banco de dados SQLite."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

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
        cur = conn.cursor()
        
        # Data de hoje
        today = date.today()
        today_str = today.isoformat()
        
        # 1. Consultas Hoje (Total)
        cur.execute("SELECT COUNT(*) FROM agendamentos WHERE data_agendamento = ?", (today_str,))
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
        
        for ag in agendamentos_hoje:
            # Processamento para Agenda de Hoje
            item = {
                'horario': str(ag['horario'])[:5],
                'pet': ag['pet'],
                'servico': ag['observacoes'] if ag['observacoes'] else 'Consulta',
                'sala': ag['sala'],
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
    return render_template('5. clientes_vta.html')

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
    return render_template('10. relatorios_pets.html')

# Nova rota para Usuários
@app.route('/usuarios')
def usuarios_page():
    if 'user_id' not in session:
        return redirect(url_for('login_page'))
    return render_template('7. usuarios_vta.html')

# --- API AGENDAMENTOS ---

@app.route('/api/agendamentos', methods=['GET'])
def get_agendamentos():
    if 'user_id' not in session:
        return jsonify({"message": "Não autorizado"}), 401
    
    conn = None
    try:
        conn = get_db_connection()
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
            INSERT INTO agendamentos (cliente, pet, sala, data_agendamento, horario, status, observacoes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get('cliente'),
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
