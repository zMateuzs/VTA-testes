import sqlite3

DB_FILE = 'agenda.db'

def create_salas_table():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Criar tabela
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS salas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        tipo TEXT,
        capacidade INTEGER,
        status TEXT DEFAULT 'ativo',
        observacoes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Inserir dados iniciais se estiver vazia
    cursor.execute('SELECT count(*) FROM salas')
    if cursor.fetchone()[0] == 0:
        salas_iniciais = [
            ('Consultório 1', 'Consulta', 1, 'ativo', 'Sala principal de atendimento'),
            ('Consultório 2', 'Consulta', 1, 'ativo', 'Sala secundária'),
            ('Centro Cirúrgico', 'Cirurgia', 1, 'ativo', 'Equipado para procedimentos complexos'),
            ('Sala de Banho', 'Banho e Tosa', 2, 'ativo', 'Área úmida')
        ]
        cursor.executemany('INSERT INTO salas (nome, tipo, capacidade, status, observacoes) VALUES (?, ?, ?, ?, ?)', salas_iniciais)
        print("Dados iniciais de salas inseridos.")
        
    conn.commit()
    conn.close()
    print("Tabela salas criada com sucesso!")

if __name__ == '__main__':
    create_salas_table()