import sqlite3
import os

DB_FILE = 'agenda.db'

def create_clientes_table():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    
    print("Creating table clientes...")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT,
            telefone TEXT,
            cpf TEXT,
            data_nascimento DATE,
            endereco TEXT,
            observacoes TEXT,
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    
    conn.commit()
    cur.close()
    conn.close()
    print("Table clientes created successfully!")

if __name__ == "__main__":
    create_clientes_table()
