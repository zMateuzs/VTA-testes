import os
import psycopg2
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash

load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "vta_agenda")
DB_USER = os.getenv("DB_USER", "vta_user")
DB_PASS = os.getenv("DB_PASS", "")

missing_env = [key for key in ("DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASS") if os.getenv(key) is None]
if missing_env:
    print(
        "Atenção: usando valores padrão para " + ", ".join(missing_env) +
        ". Exporte as variáveis DB_* de produção antes de executar python backend/setup_db.py."
    )
else:
    print(
        f"Banco alvo: host={DB_HOST} port={DB_PORT} db={DB_NAME} user={DB_USER} senha={'(vazia)' if DB_PASS == '' else '***'}"
    )


def get_db_connection():
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASS,
    )


def create_tables():
    conn = get_db_connection()
    cur = conn.cursor()

    print("Criando tabela usuarios...")
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS usuarios (
            id SERIAL PRIMARY KEY,
            nome VARCHAR(255),
            email VARCHAR(255) UNIQUE NOT NULL,
            senha_hash VARCHAR(255) NOT NULL,
            cpf VARCHAR(20),
            telefone VARCHAR(30),
            perfil VARCHAR(50) DEFAULT 'usuario',
            status VARCHAR(20) DEFAULT 'ativo',
            ultimo_acesso TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
    )

    print("Criando tabela clientes...")
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS clientes (
            id SERIAL PRIMARY KEY,
            nome VARCHAR(255) NOT NULL,
            email VARCHAR(255),
            telefone VARCHAR(50),
            cpf VARCHAR(20),
            data_nascimento DATE,
            endereco TEXT,
            observacoes TEXT,
            status VARCHAR(20) DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
    )

    print("Criando tabela pets...")
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS pets (
            id SERIAL PRIMARY KEY,
            nome VARCHAR(255) NOT NULL,
            especie VARCHAR(100) NOT NULL,
            raca VARCHAR(100),
            sexo VARCHAR(20) NOT NULL,
            data_nascimento DATE,
            peso NUMERIC,
            cor VARCHAR(50),
            tutor_id INTEGER REFERENCES clientes(id) ON DELETE SET NULL,
            observacoes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
    )

    print("Criando tabela salas...")
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS salas (
            id SERIAL PRIMARY KEY,
            nome VARCHAR(100) NOT NULL,
            tipo VARCHAR(100),
            capacidade INTEGER,
            status VARCHAR(20) DEFAULT 'ativo',
            observacoes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
    )

    print("Criando tabela notificacoes...")
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS notificacoes (
            id SERIAL PRIMARY KEY,
            titulo VARCHAR(255) NOT NULL,
            mensagem TEXT NOT NULL,
            tipo VARCHAR(50) DEFAULT 'info',
            lida BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
    )

    print("Criando tabela agendamentos...")
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS agendamentos (
            id SERIAL PRIMARY KEY,
            cliente VARCHAR(255) NOT NULL,
            cliente_id INTEGER REFERENCES clientes(id) ON DELETE SET NULL,
            pet VARCHAR(255) NOT NULL,
            sala VARCHAR(50) NOT NULL,
            data_agendamento DATE NOT NULL,
            horario TIME NOT NULL,
            status VARCHAR(50) DEFAULT 'agendado',
            observacoes TEXT,
            checkin_realizado BOOLEAN DEFAULT FALSE,
            checkin_horario TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
    )

    print("Garantindo admin padrão...")
    cur.execute("SELECT id FROM usuarios WHERE email = %s", ("admin@vta.com",))
    if not cur.fetchone():
        senha_hash = generate_password_hash('admin123')
        cur.execute(
            """
            INSERT INTO usuarios (nome, email, senha_hash, perfil, status)
            VALUES (%s, %s, %s, %s, %s)
            """,
            ("Administrador", "admin@vta.com", senha_hash, 'admin', 'ativo'),
        )

    print("Inserindo salas padrão se necessário...")
    cur.execute("SELECT COUNT(*) FROM salas")
    if cur.fetchone()[0] == 0:
        salas_iniciais = [
            ('Consultório 1', 'Consulta', 1, 'ativo', 'Sala principal de atendimento'),
            ('Consultório 2', 'Consulta', 1, 'ativo', 'Sala secundária'),
            ('Centro Cirúrgico', 'Cirurgia', 1, 'ativo', 'Equipado para procedimentos complexos'),
            ('Sala de Banho', 'Banho e Tosa', 2, 'ativo', 'Área úmida'),
        ]
        cur.executemany(
            "INSERT INTO salas (nome, tipo, capacidade, status, observacoes) VALUES (%s, %s, %s, %s, %s)",
            salas_iniciais,
        )

    conn.commit()
    cur.close()
    conn.close()
    print("Tabelas criadas/atualizadas com sucesso no PostgreSQL!")


if __name__ == "__main__":
    create_tables()
