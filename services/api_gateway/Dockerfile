FROM python:3.9-slim

WORKDIR /app

# Instalar librerías del sistema necesarias para PostgreSQL y Reportes
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# El puerto se expone, pero Docker Compose lo gestiona
EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]