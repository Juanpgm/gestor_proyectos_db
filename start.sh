#!/bin/bash
# Railway Start Script
# Script de inicio para Railway deployment

echo "🚀 Iniciando aplicación Railway..."

# Configurar variables de entorno
export PYTHONUNBUFFERED=1
export PYTHONDONTWRITEBYTECODE=1
export DEPLOYMENT_ENV=railway

# Verificar que Python esté disponible
if command -v python3 &> /dev/null; then
    PYTHON_CMD=python3
elif command -v python &> /dev/null; then
    PYTHON_CMD=python
else
    echo "❌ Error: Python no encontrado"
    exit 1
fi

echo "✅ Usando Python: $PYTHON_CMD"

# Ejecutar la aplicación
echo "🎯 Ejecutando railway_deploy.py..."
exec $PYTHON_CMD railway_deploy.py