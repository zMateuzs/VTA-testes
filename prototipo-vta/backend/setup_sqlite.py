import sqlite3
import os
from werkzeug.security import generate_password_hash

DB_FILE = 'agenda.db'

def create_tables():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    
    print("Creating table agendamentos...")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS agendamentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente TEXT NOT NULL,
            pet TEXT NOT NULL,
            sala TEXT NOT NULL,
            data_agendamento DATE NOT NULL,
            horario TIME NOT NULL,
            status TEXT DEFAULT 'agendado',
            observacoes TEXT,
            checkin_realizado BOOLEAN DEFAULT 0,
            checkin_horario TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    print("Creating table usuarios...")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            senha_hash TEXT NOT NULL,
            perfil TEXT DEFAULT 'usuario'
        );
    """)
    
    # Check if admin user exists
    cur.execute("SELECT * FROM usuarios WHERE email = 'admin@vta.com'")
    if not cur.fetchone():
        print("Creating default admin user...")
        senha_hash = generate_password_hash('admin123')
        cur.execute("INSERT INTO usuarios (email, senha_hash, perfil) VALUES (?, ?, ?)", 
                    ('admin@vta.com', senha_hash, 'admin'))
    
    conn.commit()
    cur.close()
    conn.close()
    print("Tables created successfully in SQLite!")

if __name__ == "__main__":
    create_tables()
