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
            status VARCHAR(20) DEFAULT 'disponivel',
            descricao TEXT,
            observacoes TEXT,
            cor VARCHAR(20) DEFAULT '#52B788',
            veterinario VARCHAR(120),
            motivo_bloqueio VARCHAR(120),
            observacoes_bloqueio TEXT,
            previsao_liberacao TIMESTAMP,
            data_bloqueio TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
    )

    # Garantir colunas adicionadas em instalações existentes
    cur.execute("ALTER TABLE salas ALTER COLUMN status SET DEFAULT 'disponivel';")
    cur.execute("UPDATE salas SET status = 'disponivel' WHERE status = 'ativo';")
    cur.execute("ALTER TABLE salas ADD COLUMN IF NOT EXISTS descricao TEXT;")
    cur.execute("ALTER TABLE salas ADD COLUMN IF NOT EXISTS cor VARCHAR(20) DEFAULT '#52B788';")
    cur.execute("ALTER TABLE salas ADD COLUMN IF NOT EXISTS veterinario VARCHAR(120);")
    cur.execute("ALTER TABLE salas ADD COLUMN IF NOT EXISTS motivo_bloqueio VARCHAR(120);")
    cur.execute("ALTER TABLE salas ADD COLUMN IF NOT EXISTS observacoes_bloqueio TEXT;")
    cur.execute("ALTER TABLE salas ADD COLUMN IF NOT EXISTS previsao_liberacao TIMESTAMP;")
    cur.execute("ALTER TABLE salas ADD COLUMN IF NOT EXISTS data_bloqueio TIMESTAMP;")
    cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS salas_nome_idx ON salas (lower(nome));")

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
            ('Consultório 1', 'consulta', 1, 'disponivel', 'Sala principal de atendimento', '#52B788', 'Dr(a). Equipe'),
            ('Consultório 2', 'consulta', 1, 'disponivel', 'Sala secundária', '#2E86AB', 'Dr(a). Equipe'),
            ('Centro Cirúrgico', 'cirurgia', 1, 'disponivel', 'Equipado para procedimentos complexos', '#F77F00', 'Dr(a). Cirurgia'),
            ('Sala de Exames', 'exame', 1, 'disponivel', 'Sala para exames de imagem', '#9D4EDD', 'Dr(a). Diagnóstico'),
        ]
        cur.executemany(
            """
            INSERT INTO salas (nome, tipo, capacidade, status, descricao, cor, veterinario)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            salas_iniciais,
        )

    conn.commit()
    cur.close()
    conn.close()
    print("Tabelas criadas/atualizadas com sucesso no PostgreSQL!")


if __name__ == "__main__":
    create_tables()
