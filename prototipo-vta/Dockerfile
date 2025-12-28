# Use imagem oficial do Python 3.11
FROM python:3.11-slim

# Define diretório de trabalho
WORKDIR /app

# Copia arquivo de dependências
COPY backend/requirements.txt ./

# Instala dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Copia TODO o projeto
COPY . . 

# Expõe a porta (Railway define $PORT)
EXPOSE 8000

# Entra na pasta backend e roda o app
WORKDIR /app/backend
CMD gunicorn -w 4 -b 0.0.0.0:$PORT app:app
