#!/bin/bash
# Railway Build Script - Production Ready
# Script robusto de build para Railway deployment

set -e  # Exit on any error

echo "Railway Build Script Starting..."
echo "=============================="

# Funcion para logging con timestamp
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Funcion para manejo de errores
handle_error() {
    log "ERROR en linea $1"
    log "Build failed - revisar logs arriba"
    exit 1
}

# Configurar trap para errores
trap 'handle_error $LINENO' ERR

# Verificar entorno
log "Verificando entorno de build..."
log "Python version: $(python3 --version 2>/dev/null || python --version)"
log "Pip version: $(python3 -m pip --version 2>/dev/null || python -m pip --version)"
log "Working directory: $(pwd)"
log "User: $(whoami)"

# Determinar comando Python
if command -v python3 &> /dev/null; then
    PYTHON_CMD=python3
    PIP_CMD="python3 -m pip"
elif command -v python &> /dev/null; then
    PYTHON_CMD=python
    PIP_CMD="python -m pip"
else
    log "ERROR: Python no encontrado"
    exit 1
fi

log "Usando Python: $PYTHON_CMD"

# Verificar archivos criticos
log "Verificando archivos criticos..."
critical_files=("requirements.txt" "app.py" "railway_deploy.py" "intelligent_master_deploy.py")
for file in "${critical_files[@]}"; do
    if [[ -f "$file" ]]; then
        log "OK $file"
    else
        log "FALTANTE $file"
        exit 1
    fi
done

# Actualizar herramientas de Python
log "Actualizando herramientas de Python..."
$PIP_CMD install --upgrade pip setuptools wheel --no-cache-dir

# Verificar requirements.txt
log "Analizando requirements.txt..."
if [[ -s requirements.txt ]]; then
    line_count=$(wc -l < requirements.txt)
    log "requirements.txt tiene $line_count lineas"
    log "Primeras dependencias:"
    head -5 requirements.txt | while read line; do
        if [[ ! "$line" =~ ^# ]] && [[ -n "$line" ]]; then
            log "   - $line"
        fi
    done
else
    log "requirements.txt vacio o inexistente"
    exit 1
fi

# Instalar dependencias
log "Instalando dependencias..."
$PIP_CMD install -r requirements.txt --no-cache-dir --timeout 300

# Verificar instalacion de dependencias criticas
log "Verificando dependencias criticas..."
critical_packages=("psycopg2" "sqlalchemy" "dotenv")
for package in "${critical_packages[@]}"; do
    if $PYTHON_CMD -c "import $package" 2>/dev/null; then
        log "OK $package instalado"
    else
        log "ERROR $package no instalado correctamente"
        exit 1
    fi
done

# Compilar archivos Python para verificar sintaxis
log "Verificando sintaxis de archivos Python..."
python_files=("app.py" "railway_deploy.py" "intelligent_master_deploy.py")
for file in "${python_files[@]}"; do
    if [[ -f "$file" ]]; then
        if $PYTHON_CMD -m py_compile "$file"; then
            log "OK $file - sintaxis OK"
        else
            log "ERROR $file - error de sintaxis"
            exit 1
        fi
    fi
done

# Test basico de importacion
log "Ejecutando tests basicos de importacion..."
if $PYTHON_CMD -c "
import sys
import os
sys.path.insert(0, '.')

try:
    import app
    print('OK app.py importa correctamente')
except Exception as e:
    print(f'ERROR importando app.py: {e}')
    sys.exit(1)

try:
    import railway_deploy
    print('OK railway_deploy.py importa correctamente')
except Exception as e:
    print(f'ERROR importando railway_deploy.py: {e}')
    sys.exit(1)

try:
    import intelligent_master_deploy
    print('OK intelligent_master_deploy.py importa correctamente')
except Exception as e:
    print(f'WARNING importando intelligent_master_deploy.py: {e}')
    # No exit aqui porque puede fallar por dependencias de DB

print('Tests de importacion completados')
"; then
    log "Tests de importacion OK"
else
    log "Fallo test de importacion"
    exit 1
fi

# Verificar espacio en disco
log "Verificando espacio en disco..."
df_output=$(df -h . | tail -1)
log "Espacio disponible: $df_output"

# Build completado exitosamente
log "Build completado exitosamente!"
log "Archivos compilados y dependencias instaladas"
log "Listo para deployment Railway"

# Informacion final
log "Resumen del build:"
log "   Python: $($PYTHON_CMD --version)"
log "   Pip packages instalados: $($PIP_CMD list | wc -l)"
log "   Archivos Python verificados: ${#python_files[@]}"
log "   Build completado en: $(date)"

echo "=============================="
echo "BUILD SCRIPT COMPLETADO EXITOSAMENTE"