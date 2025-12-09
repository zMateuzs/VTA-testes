import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")

def get_db_connection():
    conn = psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASS)
    return conn

def create_tables():
    conn = get_db_connection()
    cur = conn.cursor()
    
    print("Criando tabela agendamentos...")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS agendamentos (
            id SERIAL PRIMARY KEY,
            cliente VARCHAR(255) NOT NULL,
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
    """)
    
    conn.commit()
    cur.close()
    conn.close()
    print("Tabela agendamentos criada com sucesso!")

if __name__ == "__main__":
    create_tables()
