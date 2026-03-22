FROM python:3.12-slim

WORKDIR /app

# Instala dependências de sistema para o MySQL
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Copia o requirements e instala TUDO, incluindo o pymysql explicitamente
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install pymysql cryptography gunicorn

# Copia o código
COPY . .

# Expõe a porta 80 (padrão do Easypanel)
EXPOSE 80

# Comando de inicialização apontando para a pasta src
CMD ["gunicorn", "--chdir", "src", "main:app", "--bind", "0.0.0.0:80"]
