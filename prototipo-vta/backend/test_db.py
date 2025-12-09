import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")

print(f"Connecting to {DB_NAME} as {DB_USER}...")

try:
    conn = psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASS)
    print("Connected!")
    cur = conn.cursor()
    
    print("Checking if table 'agendamentos' exists...")
    cur.execute("SELECT to_regclass('public.agendamentos');")
    result = cur.fetchone()
    print(f"Table exists: {result[0] if result else 'No'}")
    
    if not result[0]:
        print("Attempting to create table...")
        try:
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
            print("Table created successfully!")
        except Exception as e:
            print(f"Error creating table: {e}")
            conn.rollback()
            
    cur.close()
    conn.close()

except Exception as e:
    print(f"Connection error: {e}")
