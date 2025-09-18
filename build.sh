#!/bin/bash
# Railway Build Script
# Este script ayuda a Railway a detectar y construir correctamente el proyecto

echo "🚂 Iniciando build script para Railway..."

# Verificar que Python esté disponible
python3 --version || python --version

# Actualizar pip
python3 -m pip install --upgrade pip || python -m pip install --upgrade pip

# Instalar dependencias
echo "📦 Instalando dependencias..."
python3 -m pip install -r requirements.txt || python -m pip install -r requirements.txt

# Compilar archivos Python para verificar sintaxis
echo "✅ Verificando sintaxis de archivos Python..."
python3 -m py_compile railway_deploy.py || python -m py_compile railway_deploy.py
python3 -m py_compile intelligent_master_deploy.py || python -m py_compile intelligent_master_deploy.py

echo "🎉 Build completado exitosamente!"