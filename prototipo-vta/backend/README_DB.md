# Configuração do Banco de Dados

O sistema utiliza PostgreSQL. Para que o agendamento funcione, é necessário criar a tabela `agendamentos` no banco de dados.

## 1. Criar a Tabela

Você pode rodar o script `backend/setup_db.py` para criar a tabela automaticamente:

```bash
cd backend
source venv/bin/activate  # Se estiver usando ambiente virtual
python setup_db.py
```

Caso encontre erros de permissão, você pode criar a tabela manualmente executando o seguinte SQL no seu banco de dados:

```sql
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
```

## 2. Variáveis de Ambiente

Certifique-se de que o arquivo `.env` na pasta `backend` contém as credenciais corretas do banco de dados:

```
DB_HOST=seu_host
DB_NAME=seu_banco
DB_USER=seu_usuario
DB_PASS=sua_senha
```
