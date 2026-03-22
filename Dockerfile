FROM python:3.12-slim

# Instala bibliotecas necessárias para o MySQL
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copia e instala as dependências
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# Garante que o gunicorn e mysqlclient estejam instalados
RUN pip install gunicorn mysqlclient Flask-SQLAlchemy

# Copia o restante do código
COPY . .

# Define a porta (Easypanel usa 80 por padrão para HTTP)
EXPOSE 80

# O "Start Command" agora é escrito aqui:
CMD ["gunicorn", "--chdir", "src", "main:app", "--bind", "0.0.0.0:80"]
