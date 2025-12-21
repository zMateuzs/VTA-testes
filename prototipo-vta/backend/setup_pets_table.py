import sqlite3
import os

DB_FILE = 'agenda.db'

def create_pets_table():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    
    print("Creating table pets...")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS pets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            especie TEXT NOT NULL,
            raca TEXT,
            sexo TEXT NOT NULL,
            data_nascimento DATE,
            peso REAL,
            cor TEXT,
            tutor_id INTEGER,
            observacoes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (tutor_id) REFERENCES clientes (id)
        );
    """)
    
    conn.commit()
    cur.close()
    conn.close()
    print("Table pets created successfully!")

if __name__ == "__main__":
    create_pets_table()
