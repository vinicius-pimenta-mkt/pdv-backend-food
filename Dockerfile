FROM python:3.12-slim

WORKDIR /app

# Instala dependências do sistema se necessário (ex: para banco de dados)
RUN apt-get update && apt-get install -y gcc libpq-dev && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia tudo para o container
COPY . .

# Expõe a porta que o Easypanel vai usar
EXPOSE 80

# Comando para rodar direto da pasta src
CMD ["gunicorn", "--chdir", "src", "main:app", "--bind", "0.0.0.0:80"]
