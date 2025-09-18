#!/bin/bash
# Railway Start Script - Production Ready
# Script robusto de inicio para Railway deployment

set -e  # Exit on any error

echo "Iniciando aplicacion Railway..."
echo "=============================="

# Funcion para logging con timestamp
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Funcion para manejo de errores
handle_error() {
    log "Error en start script linea $1"
    log "Start failed - revisar configuracion"
    exit 1
}

# Configurar trap para errores
trap 'handle_error $LINENO' ERR

# Verificar entorno Railway
log "Configurando entorno Railway..."

# Variables de entorno esenciales
export PYTHONUNBUFFERED=1
export PYTHONDONTWRITEBYTECODE=1
export DEPLOYMENT_ENV=railway

# Configurar puerto
PORT=${PORT:-8080}
export PORT=$PORT
log "Puerto configurado: $PORT"

# Verificar variables de entorno criticas
log "Verificando variables de entorno..."
env_vars=("PYTHONUNBUFFERED" "PYTHONDONTWRITEBYTECODE" "PORT")
for var in "${env_vars[@]}"; do
    if [[ -n "${!var}" ]]; then
        log "OK $var=${!var}"
    else
        log "WARNING $var no configurada"
    fi
done

# Verificar DATABASE_URL
if [[ -n "$DATABASE_URL" ]]; then
    if [[ "$DATABASE_URL" == *"railway"* ]] || [[ "$DATABASE_URL" == *"rlwy.net"* ]]; then
        log "DATABASE_URL Railway detectada"
        export RAILWAY_DATABASE_DETECTED=true
    else
        log "DATABASE_URL personalizada detectada"
    fi
else
    log "WARNING DATABASE_URL no configurada - usando configuracion local"
fi

# Determinar comando Python
if command -v python3 &> /dev/null; then
    PYTHON_CMD=python3
elif command -v python &> /dev/null; then
    PYTHON_CMD=python
else
    log "ERROR: Python no encontrado"
    exit 1
fi

log "Usando Python: $PYTHON_CMD"
log "Version: $($PYTHON_CMD --version)"

# Verificar directorio de trabajo
log "Directorio de trabajo: $(pwd)"
log "Usuario: $(whoami)"

# Verificar archivos de aplicacion
log "Verificando archivos de aplicacion..."
app_files=("app.py" "railway_deploy.py" "intelligent_master_deploy.py")
primary_app=""

for file in "${app_files[@]}"; do
    if [[ -f "$file" ]]; then
        log "OK $file existe"
        if [[ "$file" == "app.py" ]]; then
            primary_app="app.py"
        elif [[ -z "$primary_app" && "$file" == "railway_deploy.py" ]]; then
            primary_app="railway_deploy.py"
        fi
    else
        log "WARNING $file no encontrado"
    fi
done

# Determinar aplicación a ejecutar
if [[ -n "$primary_app" ]]; then
    log "Aplicacion principal: $primary_app"
else
    log "ERROR: No se encontro aplicacion principal"
    exit 1
fi

# Test rapido de importacion
log "Test rapido de importacion..."
if $PYTHON_CMD -c "
import sys
sys.path.insert(0, '.')
try:
    import ${primary_app%.py}
    print('OK Importacion exitosa')
except Exception as e:
    print(f'ERROR de importacion: {e}')
    sys.exit(1)
" 2>/dev/null; then
    log "Test de importacion OK"
else
    log "WARNING en test de importacion - continuando..."
fi

# Funcion para manejar senales
cleanup() {
    log "Recibida senal de terminacion - cerrando aplicacion..."
    exit 0
}

# Configurar traps para señales
trap cleanup SIGTERM SIGINT

# Mostrar informacion del sistema
log "Informacion del sistema:"
log "   Python: $($PYTHON_CMD --version)"
log "   PWD: $(pwd)"
log "   Hostname: $(hostname)"
log "   Fecha: $(date)"

# Ejecutar la aplicacion principal
log "Ejecutando aplicacion: $PYTHON_CMD $primary_app"
log "=================================="

# Ejecutar con manejo de errores
if ! exec $PYTHON_CMD $primary_app; then
    log "ERROR ejecutando $primary_app"
    
    # Intentar fallback si app.py falla
    if [[ "$primary_app" == "app.py" && -f "railway_deploy.py" ]]; then
        log "Intentando fallback a railway_deploy.py..."
        exec $PYTHON_CMD railway_deploy.py
    else
        log "No hay fallback disponible"
        exit 1
    fi
fi