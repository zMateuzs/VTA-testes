from flask import Flask
import os
from dotenv import load_dotenv

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

# Cria a instância principal da aplicação
app = Flask(__name__)

# Configuração obrigatória de segurança
secret_key = os.getenv("SECRET_KEY")
if not secret_key:
    raise RuntimeError("SECRET_KEY não definido no ambiente")
app.secret_key = secret_key

# Endurece cookies de sessão para ambiente produtivo
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE=os.getenv("SESSION_COOKIE_SAMESITE", "Lax"),
    SESSION_COOKIE_SECURE=os.getenv("SESSION_COOKIE_SECURE", "true").lower() == "true",
)

debug_flag = os.getenv("FLASK_DEBUG", "false").lower() == "true"
host = os.getenv("HOST", "0.0.0.0")
port = int(os.getenv("PORT", "5000"))

# --- Importa as rotas DEPOIS de criar o 'app' ---
# Isso evita problemas de importação circular.
from routes import *

# --- Ponto de entrada para rodar o servidor ---
if __name__ == '__main__':
    app.run(debug=debug_flag, host=host, port=port, use_reloader=debug_flag)