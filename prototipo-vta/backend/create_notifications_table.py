import sqlite3

DB_FILE = 'agenda.db'

def create_notifications_table():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    
    print("Dropping table notificacoes if exists...")
    cur.execute("DROP TABLE IF EXISTS notificacoes")

    print("Creating table notificacoes...")
    cur.execute("""
        CREATE TABLE notificacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT NOT NULL,
            mensagem TEXT NOT NULL,
            tipo TEXT DEFAULT 'info',
            lida BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    
    conn.commit()
    cur.close()
    conn.close()
    print("Table notificacoes created successfully!")

if __name__ == "__main__":
    create_notifications_table()
