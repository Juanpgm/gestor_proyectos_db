# Dockerfile personalizado para Railway - Solución definitiva
FROM python:3.12-slim

# Configurar variables de entorno
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PORT=8080

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    postgresql-client \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Configurar directorio de trabajo
WORKDIR /app

# Copiar requirements primero para cache de Docker
COPY requirements.txt .

# Instalar dependencias Python
RUN pip install --upgrade pip setuptools wheel
RUN pip install -r requirements.txt --no-cache-dir

# Copiar código de la aplicación
COPY . .

# Exponer puerto
EXPOSE $PORT

# Comando de inicio
CMD ["python", "app.py"]