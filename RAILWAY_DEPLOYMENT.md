# 🚂 Guía de Despliegue en Railway

## 📋 Resumen

Tu aplicación está completamente configurada para desplegarse en Railway con **deployment automático de base de datos**. Se enfoca únicamente en la inicialización y carga de datos, **sin APIs**.

## ✅ Estado Actual

- ✅ Script de deployment de base de datos creado (`railway_db_deploy.py`)
- ✅ Configuración de base de datos actualizada
- ✅ Tabla `emp_seguimiento_procesos_dacp` creada y configurada
- ✅ Carga directa de datos usando loaders existentes
- ✅ Archivos de despliegue creados
- ✅ Seguridad de credenciales implementada
- ❌ **APIs eliminadas** - Solo deployment y monitoreo básico

## 🔧 Archivos de Configuración Creados

### 1. **railway_db_deploy.py** (NUEVO)

- Script principal de deployment de base de datos
- Inicialización automática de todas las tablas
- Carga directa de datos usando los loaders existentes
- Verificación completa de datos cargados
- **Sin funcionalidades de API**

### 2. **railway_app.py** (ACTUALIZADO)

- Aplicación web simplificada para Railway
- Ejecuta `railway_db_deploy.py` al inicio
- Solo endpoints de monitoreo (`/status`, `/health`)
- **Eliminadas todas las referencias a APIs de datos**

### 3. **manual_deploy.py** (NUEVO)

- Script manual para deployment si es necesario
- Útil para re-ejecutar deployment
- Verificaciones de entorno

### 4. **Procfile** (ACTUALIZADO)

```
web: python railway_app.py
release: python railway_db_deploy.py
```

### 5. **Otros archivos**

- Todas las dependencias necesarias
- Compatible con Railway

### 4. **railway.json**

```json
{
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

### 5. **runtime.txt**

```
python-3.12
```

## 🛡️ Seguridad Implementada

### Variables de Entorno Protegidas

- ❌ **NO** hay credenciales hardcodeadas en el código
- ✅ Configuración por `DATABASE_URL` (Railway estándar)
- ✅ `.gitignore` actualizado para proteger archivos sensibles

### Archivos Protegidos en .gitignore

```
.env
.env.local
.env.railway
*.db
__pycache__/
```

## 🚀 Pasos para Desplegar

### 1. **Preparar el Repositorio**

```bash
git add .
git commit -m "Configuración para Railway deployment"
git push origin main
```

### 2. **Configurar Railway**

1. Ve a [railway.app](https://railway.app)
2. Conecta tu repositorio GitHub
3. Railway detectará automáticamente tu aplicación Python

### 3. **Configurar Variables de Entorno en Railway**

En el dashboard de Railway, agrega estas variables:

**Variables Requeridas:**

- `DATABASE_URL`: Railway la proporcionará automáticamente al agregar PostgreSQL
- `APP_ENV`: `production`
- `LOG_LEVEL`: `INFO`

**Opcional:**

- `PYTHONPATH`: `/app/src` (si necesitas rutas específicas)

### 4. **Agregar Base de Datos PostgreSQL**

1. En Railway dashboard, haz clic en "Add Service"
2. Selecciona "PostgreSQL"
3. Railway configurará automáticamente `DATABASE_URL`

### 5. **Verificar Despliegue**

- Railway desplegará automáticamente
- Accede a: `https://tu-app.railway.app/status`
- Verifica que muestre: `{"status": "healthy", "database": "connected"}`

## 🔍 Endpoints Disponibles (Solo Monitoreo)

### Status de la Aplicación

```
GET /status
Response: {
  "status": "healthy",
  "database": "connected",
  "deployment": "completed",
  "tables": {"contratos_secop": 1250, "emp_seguimiento_procesos_dacp": 17, ...},
  "total_records": 15420
}
```

### Health Check

```
GET /health
Response: {"status": "ok", "service": "railway-db-app"}
```

### Página Principal

```
GET /
Response: Página HTML con información del sistema
```

**⚠️ IMPORTANTE: No hay APIs de datos - Solo monitoreo**

### Health Check

```
GET /health
Response: {"status": "ok"}
```

## 🛠️ Comandos de Desarrollo Local

### Probar Configuración

```bash
python test_railway.py
```

### Ejecutar Localmente (Simulando Railway)

```bash
# Cargar configuración Railway
cp .env.railway .env

# Ejecutar aplicación
python railway_app.py
```

## 📊 Monitoreo

### Logs en Railway

- Los logs se muestran automáticamente en el dashboard
- Configuración de logging optimizada para producción

### Métricas Disponibles

- Estado de conexión a base de datos
- Número de tablas disponibles
- Health checks automáticos

## ⚠️ Consideraciones Importantes

### Seguridad

- **NUNCA** commitees archivos `.env` con credenciales
- Usa solo variables de entorno en Railway
- Verifica `.gitignore` antes de hacer push

### Base de Datos

- Railway PostgreSQL incluye PostGIS automáticamente
- Las migraciones se ejecutan al inicio de la aplicación
- Backup automático incluido en Railway

### Escalabilidad

- Railway escala automáticamente según demanda
- Configuración optimizada para aplicaciones Python
- Reinicio automático en caso de fallo

## 📞 Soporte

### Si algo no funciona:

1. Verifica logs en Railway dashboard
2. Confirma variables de entorno configuradas
3. Usa `python test_railway.py` para diagnosticar localmente

### Archivos de Debug:

- `railway_app.py`: Aplicación principal
- `src/config/settings.py`: Configuración de base de datos
- `test_railway.py`: Script de diagnóstico

---

## 🎉 ¡Listo para Desplegar!

Tu aplicación está completamente preparada para Railway. Todos los archivos están configurados, la seguridad está implementada y el sistema está optimizado para producción.

**Próximo paso:** Conecta tu repositorio en railway.app y disfruta de tu aplicación en la nube! 🚀
