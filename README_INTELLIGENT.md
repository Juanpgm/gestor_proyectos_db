# 🎯 Gestor de Proyectos DB - Sistema Inteligente de Despliegue y Monitoreo

Un sistema completo y robusto para gestión de bases de datos PostgreSQL con capacidades de auto-diagnóstico, auto-configuración, autoreparación y monitoreo continuo. Diseñado para funcionar tanto en entornos locales como en Railway (cloud).

## ✨ Características Principales

### 🧠 Inteligencia Artificial

- **Auto-diagnóstico**: Detección automática de problemas de conectividad, rendimiento y estructura
- **Auto-configuración**: Configuración automática según el entorno detectado
- **Autoreparación**: Reparación automática de problemas comunes sin intervención manual
- **Detección de entorno**: Selección inteligente entre Railway y PostgreSQL local

### 🔄 Despliegue Robusto

- **Despliegue híbrido**: Soporte para Railway (cloud) y PostgreSQL local
- **Fallback automático**: Si Railway falla, automáticamente usa configuración local
- **Validación completa**: Verificación de conectividad, estructura y datos tras despliegue
- **Recuperación ante fallos**: Reconstrucción automática en caso de corrupción

### 📊 Monitoreo Continuo

- **Chequeos periódicos**: Verificación automática de salud cada 5-15 minutos
- **Alertas inteligentes**: Sistema de alertas por niveles (Info, Warning, Critical)
- **Métricas de rendimiento**: Tiempo de respuesta, uso de memoria, conexiones
- **Histórico completo**: Almacenamiento de todas las métricas y eventos

### 🔧 Autoreparación Avanzada

- **Detección de problemas**: Identificación automática de fallos comunes
- **Reparación automática**: Solución sin intervención para problemas conocidos
- **Reconstrucción de emergencia**: Recreación completa de estructura si es necesario
- **Recuperación de datos**: Restauración automática desde backups

### 📈 Reportes Ejecutivos

- **Análisis de tendencias**: Identificación de patrones y degradación
- **Reportes multiformat**: JSON, HTML, Markdown, CSV
- **Métricas clave**: Uptime, rendimiento, alertas, estabilidad
- **Recomendaciones**: Sugerencias automáticas de optimización

## 🏗️ Arquitectura del Sistema

```
intelligent_master_deploy.py     # Script maestro - Punto de entrada único
├── intelligent_local_deploy.py  # Despliegue local con detección de PostgreSQL
├── intelligent_railway_deploy.py # Despliegue Railway con manejo de suspensión
├── database_monitor.py          # Monitoreo continuo y autoreparación
├── database_reporter.py         # Sistema de reportes avanzado
├── railway_config.py           # Configuración Railway con fallback
└── src/                        # Módulos core del sistema
    ├── utils/
    │   ├── database_health.py   # Sistema de diagnóstico de salud
    │   └── database_repair.py   # Sistema de autoreparación
    ├── config/settings.py       # Configuraciones
    ├── database/connection.py   # Gestión de conexiones
    └── utils/data_loader.py     # Carga de datos
```

## 🚀 Instalación y Configuración

### Prerrequisitos

```bash
# Python 3.8+
python --version

# PostgreSQL (para desarrollo local)
# Windows: https://www.postgresql.org/download/windows/
# macOS: brew install postgresql
# Linux: sudo apt-get install postgresql postgresql-contrib
```

### Instalación de dependencias

```bash
# Clonar o descargar el proyecto
cd gestor_proyectos_db

# Crear entorno virtual (recomendado)
python -m venv env
source env/bin/activate  # Linux/macOS
# o
env\Scripts\activate     # Windows

# Instalar dependencias
pip install psycopg2-binary python-dotenv schedule
```

### Configuración de Variables de Entorno

#### Para Railway (Cloud)

```bash
# Crear archivo .env
echo "DATABASE_URL=postgresql://postgres:contraseña@localhost:5432/gestor_proyectos" > .env

# Agregar URL de Railway (obtenida del dashboard)
echo "DATABASE_URL=postgresql://postgres:PASSWORD@railway.domain:PORT/railway" > .env
```

#### Para PostgreSQL Local

```bash
# El sistema detecta automáticamente PostgreSQL local
# Configuración por defecto:
# Host: localhost
# Puerto: 5432
# Usuario: postgres
# Base de datos: gestor_proyectos
```

## 🎮 Uso del Sistema

### 🚀 Comando Principal - Despliegue Completo

```bash
# Despliegue automático completo (RECOMENDADO)
python intelligent_master_deploy.py full-deploy

# Esto ejecutará:
# 1. Detección automática del mejor entorno
# 2. Despliegue inteligente con validación
# 3. Chequeo de salud post-despliegue
# 4. Inicio de monitoreo continuo
# 5. Generación de reporte inicial
```

### 🎯 Comandos Específicos

#### Despliegue

```bash
# Despliegue automático (detecta Railway vs Local)
python intelligent_master_deploy.py deploy

# Forzar Railway
python intelligent_master_deploy.py deploy --environment railway

# Forzar Local
python intelligent_master_deploy.py deploy --environment local
```

#### Monitoreo

```bash
# Iniciar monitoreo continuo
python intelligent_master_deploy.py monitor

# El monitoreo incluye:
# - Chequeos cada 15 minutos (Railway: 5 minutos)
# - Autoreparación automática
# - Alertas en tiempo real
# - Generación de logs detallados
```

#### Reportes

```bash
# Reporte ejecutivo (últimos 7 días)
python intelligent_master_deploy.py report

# Reporte de salud específico
python intelligent_master_deploy.py report --type health --days 30

# Reporte de rendimiento
python intelligent_master_deploy.py report --type performance --days 7

# Análisis de alertas
python intelligent_master_deploy.py report --type alerts --days 14
```

#### Mantenimiento

```bash
# Chequeo de salud manual
python intelligent_master_deploy.py health-check

# Reparación manual
python intelligent_master_deploy.py repair

# Estado completo del sistema
python intelligent_master_deploy.py status
```

### 🔧 Scripts Individuales (Uso Avanzado)

```bash
# Despliegue local únicamente
python intelligent_local_deploy.py

# Despliegue Railway únicamente
python intelligent_railway_deploy.py

# Solo monitoreo (requiere DB ya configurada)
python database_monitor.py

# Solo generación de reportes
python database_reporter.py
```

## 📊 Sistema de Monitoreo

### Chequeos Automáticos

- **Conectividad**: Verificación de conexión a base de datos
- **Estructura**: Validación de tablas, índices y restricciones
- **Datos**: Verificación de integridad y consistencia
- **Rendimiento**: Tiempo de respuesta y uso de recursos
- **Seguridad**: Verificación de permisos y configuración

### Autoreparación

- **Reconexión automática**: En caso de pérdida de conexión
- **Recreación de índices**: Si se detectan índices faltantes
- **Limpieza de datos**: Eliminación de datos corruptos
- **Optimización**: Ajustes automáticos de rendimiento
- **Reconstrucción**: Recreación completa si es necesario

### Alertas Inteligentes

- **INFO**: Eventos informativos (reconexiones exitosas, etc.)
- **WARNING**: Problemas que requieren atención (rendimiento lento)
- **CRITICAL**: Problemas críticos que requieren acción inmediata

## 📈 Sistema de Reportes

### Tipos de Reportes

#### 🎯 Resumen Ejecutivo

- Puntuación de salud general (0-100)
- Estado de estabilidad del sistema
- Top 5 recomendaciones
- Métricas clave de uptime y rendimiento

#### 🔍 Análisis de Salud

- Distribución de chequeos por estado
- Análisis por categorías (conectividad, estructura, datos)
- Tendencias de tiempo de respuesta
- Recomendaciones específicas

#### ⚡ Análisis de Rendimiento

- Métricas de tiempo de conexión
- Análisis de tiempo de consultas
- Uso de memoria y recursos
- Gráficos de tendencias

#### 🚨 Análisis de Alertas

- Distribución por tipo y severidad
- Alertas más frecuentes
- Tiempo promedio de resolución
- Tendencias de frecuencia

### Formatos de Exportación

- **JSON**: Para procesamiento automático
- **HTML**: Para visualización web
- **Markdown**: Para documentación
- **CSV**: Para análisis en Excel

## 🗂️ Estructura de Logs

```
logs/
├── monitor_YYYYMMDD.log           # Logs diarios del monitor
├── monitoring_stats.json          # Estadísticas de monitoreo
├── monitoring_config.json         # Configuración del monitor
├── final_status.json             # Estado final del sistema
├── health_reports/               # Reportes de salud individuales
│   └── health_YYYYMMDD_HHMMSS.json
├── alerts/                       # Alertas por día
│   └── alerts_YYYYMMDD.json
├── daily_reports/               # Reportes diarios
│   └── daily_YYYYMMDD.json
└── reports/                     # Reportes exportados
    ├── executive_summary_YYYYMMDD_HHMMSS.json
    ├── executive_summary_YYYYMMDD_HHMMSS.html
    └── executive_summary_YYYYMMDD_HHMMSS.md
```

## ⚙️ Configuración Avanzada

### Archivo master_config.json

```json
{
  "auto_monitor": true,
  "auto_reports": true,
  "fallback_enabled": true,
  "health_check_on_deploy": true,
  "monitoring_config": {
    "check_interval_minutes": 15,
    "railway_check_interval_minutes": 5,
    "auto_repair": true,
    "max_repair_attempts": 3,
    "alert_thresholds": {
      "response_time_ms": 2000,
      "connection_failures": 3,
      "data_staleness_hours": 24
    }
  },
  "report_config": {
    "daily_reports": true,
    "weekly_reports": true,
    "executive_summary": true
  }
}
```

### Variables de Entorno Opcionales

```bash
# Configuración de base de datos local
DB_HOST=localhost
DB_PORT=5432
DB_NAME=gestor_proyectos
DB_USER=postgres
DB_PASSWORD=tu_password

# Configuración Railway (automática desde dashboard)
DATABASE_URL=postgresql://user:pass@host:port/db

# Configuración de logs
LOG_LEVEL=INFO
LOG_RETENTION_DAYS=30
```

## 🔧 Solución de Problemas

### Problemas Comunes

#### 1. "No se puede conectar a PostgreSQL"

```bash
# Verificar que PostgreSQL esté ejecutándose
# Windows:
net start postgresql-x64-14

# macOS:
brew services start postgresql

# Linux:
sudo systemctl start postgresql

# Verificar puerto
netstat -an | findstr 5432  # Windows
netstat -an | grep 5432     # Linux/macOS
```

#### 2. "Railway no disponible"

```bash
# Verificar variables de entorno
python -c "import os; print(os.getenv('DATABASE_URL'))"

# Verificar conectividad
ping railway.app

# El sistema automáticamente usa fallback local
```

#### 3. "Error de permisos"

```bash
# PostgreSQL local: verificar usuario
psql -U postgres -c "SELECT current_user;"

# Crear base de datos manualmente si es necesario
createdb -U postgres gestor_proyectos
```

### Modo Debug

```bash
# Ejecutar con información detallada
python intelligent_master_deploy.py deploy --environment local

# Revisar logs
tail -f logs/monitor_$(date +%Y%m%d).log

# Verificar estado
python intelligent_master_deploy.py status
```

### Recuperación de Emergencia

```bash
# Forzar reparación completa
python intelligent_master_deploy.py repair

# Si todo falla, recrear desde cero
rm -rf logs/  # Eliminar logs
python intelligent_master_deploy.py deploy --environment local
```

## 🔄 Flujo de Trabajo Típico

### Para Desarrollo Local

```bash
# 1. Configuración inicial
python intelligent_master_deploy.py full-deploy

# 2. Desarrollo y testing
# ... tu código aquí ...

# 3. Chequeos periódicos
python intelligent_master_deploy.py health-check

# 4. Reportes semanales
python intelligent_master_deploy.py report --days 7
```

### Para Producción (Railway)

```bash
# 1. Configurar variables de entorno con Railway URL
echo "DATABASE_URL=tu_railway_url" > .env

# 2. Despliegue completo
python intelligent_master_deploy.py full-deploy

# 3. Monitoreo continuo automático
# (se ejecuta en background)

# 4. Reportes ejecutivos automáticos
# (se generan diariamente)
```

## 📋 Lista de Verificación Post-Instalación

- [ ] ✅ PostgreSQL instalado y ejecutándose
- [ ] ✅ Python 3.8+ con dependencias instaladas
- [ ] ✅ Variables de entorno configuradas (.env)
- [ ] ✅ Primer despliegue ejecutado exitosamente
- [ ] ✅ Monitoreo continuo activo
- [ ] ✅ Reporte inicial generado
- [ ] ✅ Chequeo de salud manual exitoso
- [ ] ✅ Logs generándose correctamente

## 🎯 Beneficios del Sistema

### Para Desarrolladores

- **Configuración automática**: Sin configuración manual compleja
- **Detección de errores**: Problemas identificados antes de que afecten
- **Reportes automáticos**: Visibilidad completa del estado del sistema
- **Fallback inteligente**: Funciona incluso si Railway no está disponible

### Para Operaciones

- **Monitoreo 24/7**: Vigilancia continua sin intervención
- **Autoreparación**: Resolución automática de problemas comunes
- **Alertas proactivas**: Notificación antes de fallas críticas
- **Reportes ejecutivos**: Métricas para toma de decisiones

### Para el Negocio

- **Alta disponibilidad**: Uptime maximizado con autoreparación
- **Costos reducidos**: Menos intervención manual requerida
- **Escalabilidad**: Funciona igual en desarrollo y producción
- **Transparencia**: Reportes claros del estado del sistema

## 🤝 Soporte y Contribuciones

Este sistema está diseñado para ser robusto y auto-explicativo. Los logs detallados y reportes proporcionan toda la información necesaria para diagnosticar y resolver problemas.

### Estructura Modular

Cada componente es independiente y puede ser usado por separado:

- `intelligent_master_deploy.py`: Orquestador principal
- `database_monitor.py`: Sistema de monitoreo standalone
- `database_reporter.py`: Generador de reportes independiente
- `intelligent_local_deploy.py`: Despliegue local especializado
- `intelligent_railway_deploy.py`: Despliegue Railway especializado

Este diseño permite extensiones y modificaciones fáciles según necesidades específicas.

---

## 🎉 ¡Listo para Usar!

El sistema está diseñado para funcionar "out of the box" con configuración mínima. Para la mayoría de casos de uso, simplemente ejecuta:

```bash
python intelligent_master_deploy.py full-deploy
```

¡Y tendrás un sistema completo de gestión de base de datos con monitoreo inteligente funcionando en minutos!
