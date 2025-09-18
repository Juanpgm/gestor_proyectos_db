# Gestor de Proyectos DB

Sistema de gestión de base de datos PostgreSQL con PostGIS para el manejo de contratos y procesos de empréstitos del Distrito de Santiago de Cali.

## Características

- **Base de datos**: PostgreSQL con extensión PostGIS
- **ORM**: SQLAlchemy con soporte para funciones geoespaciales
- **Programación funcional**: Estructura modular y funciones puras
- **Validación de datos**: Pydantic para configuraciones
- **Logging avanzado**: Rich para logging colorido y estructurado
- **Migraciones**: Sistema de migraciones SQL versionadas

## Estructura del Proyecto

```
gestor_proyectos_db/
├── src/                          # Código fuente principal
│   ├── config/                   # Configuraciones del sistema
│   ├── models/                   # Modelos SQLAlchemy
│   ├── database/                 # Gestión de conexiones y PostGIS
│   └── utils/                    # Utilidades y helpers
├── sql/                          # Scripts SQL
│   ├── migrations/               # Migraciones versionadas
│   └── schemas/                  # Esquemas y estructuras
├── tests/                        # Pruebas unitarias
├── docs/                         # Documentación
├── app_outputs/                  # Archivos de datos JSON
├── main.py                       # Punto de entrada principal
├── requirements.txt              # Dependencias Python
└── README.md                     # Este archivo
```

## Instalación

### Prerrequisitos

- Python 3.8+
- PostgreSQL 12+ con PostGIS 3.0+
- pip (gestor de paquetes de Python)

### Pasos de instalación

1. **Clonar o descargar el proyecto**

2. **Activar el entorno virtual** (ya existente):

   ```bash
   .\env\Scripts\Activate.ps1
   ```

3. **Instalar dependencias**:

   ```bash
   pip install -r requirements.txt
   ```

4. **Configurar variables de entorno**:

   ```bash
   cp .env.example .env
   # Editar .env con tus configuraciones de base de datos
   ```

5. **Configurar PostgreSQL**:
   - Crear usuario y base de datos
   - Habilitar PostGIS (se hace automáticamente)

## Configuración

### Variables de entorno (.env)

```env
# Base de datos
DB_HOST=localhost
DB_PORT=5432
DB_NAME=gestor_proyectos_db
DB_USER=postgres
DB_PASSWORD=tu_password_aqui

# Aplicación
LOG_LEVEL=INFO
DATA_DIR=app_outputs
```

### Archivos de datos

El sistema espera encontrar los siguientes archivos JSON:

- `app_outputs/emprestito_outputs/emp_contratos.json`
- `app_outputs/emprestito_outputs/emp_procesos.json`

## Uso

### Comandos principales

```bash
# Inicializar base de datos y esquemas
python main.py init

# Cargar datos desde archivos JSON
python main.py load

# Ejecutar migraciones
python main.py migrate

# Verificar estado de la base de datos
python main.py status
```

### Ejemplo de uso programático

```python
from src.config.settings import load_config
from src.database.connection import create_database_manager
from src.database.postgis import setup_postgis
from src.utils.data_loader import load_all_data

# Cargar configuración
config = load_config()

# Crear gestor de DB
db_manager = create_database_manager(config)

# Conectar y configurar
db_manager.connect()
setup_postgis(db_manager)

# Cargar datos
stats = load_all_data(
    db_manager,
    config.application.contratos_file,
    config.application.procesos_file
)

print(f"Datos cargados: {stats}")
```

## Modelos de Datos

### Proceso (emp_procesos)

- Información básica del proceso de contratación
- Valores monetarios y modalidades
- Estado y seguimiento en SECOP
- URLs y metadatos

### Contrato (emp_contratos)

- Información detallada del contrato
- Datos de entidad y proveedor
- Valores financieros y recursos
- Fechas y responsables
- Relación con proceso padre

### Vistas de análisis

- `v_procesos_resumen`: Estadísticas de procesos
- `v_contratos_resumen`: Información clave de contratos
- `v_analisis_entidades`: Análisis por entidad
- `v_analisis_temporal`: Análisis temporal
- `v_analisis_proveedores`: Estadísticas de proveedores

## Arquitectura

### Principios de diseño

1. **Programación Funcional**: Funciones puras, inmutabilidad cuando es posible
2. **Separación de responsabilidades**: Módulos especializados
3. **Configuración externa**: Variables de entorno y archivos de configuración
4. **Validación robusta**: Pydantic para configuraciones, validaciones en modelos
5. **Logging estructurado**: Información detallada para debugging y monitoreo

### Flujo de datos

```
JSON Files → DataLoader → SQLAlchemy Models → PostgreSQL + PostGIS
```

### Capas de la aplicación

1. **Configuración**: Manejo de settings y variables de entorno
2. **Modelos**: Definición de esquemas de datos
3. **Base de datos**: Conexiones, migraciones y PostGIS
4. **Utilidades**: Helpers, logging y carga de datos

## Desarrollo

### Agregar nuevas tablas

1. Crear modelo en `src/models/`
2. Crear migración en `sql/migrations/`
3. Actualizar `src/models/__init__.py`
4. Crear funciones de carga de datos si es necesario

### Ejemplo de nueva migración

```sql
-- sql/migrations/003_nueva_tabla.sql
CREATE TABLE IF NOT EXISTS nueva_tabla (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Pruebas

```bash
# Ejecutar pruebas (cuando estén implementadas)
pytest tests/

# Verificar calidad de código
flake8 src/
black src/
mypy src/
```

## Estructura de Base de Datos

### Tablas principales

- **emp_procesos**: Procesos de contratación
- **emp_contratos**: Contratos adjudicados

### Índices optimizados

- Índices B-tree para consultas frecuentes
- Índices GIN para campos JSON
- Índices espaciales GIST (preparado para PostGIS)

### Triggers

- Actualización automática de timestamps
- Validaciones de integridad

## Consultas útiles

```sql
-- Resumen de procesos por banco
SELECT banco, COUNT(*), SUM(valor_total)
FROM emp_procesos
GROUP BY banco;

-- Contratos por estado
SELECT estado_contrato, COUNT(*), SUM(valor_del_contrato)
FROM emp_contratos
GROUP BY estado_contrato;

-- Top 10 proveedores por valor
SELECT proveedor_adjudicado, SUM(valor_del_contrato) as total
FROM emp_contratos
GROUP BY proveedor_adjudicado
ORDER BY total DESC
LIMIT 10;
```

## Troubleshooting

### Problemas comunes

1. **Error de conexión a PostgreSQL**:

   - Verificar que PostgreSQL esté ejecutándose
   - Revisar credenciales en `.env`
   - Verificar firewall y puertos

2. **PostGIS no disponible**:

   - Instalar PostGIS: `CREATE EXTENSION postgis;`
   - Verificar permisos de usuario

3. **Errores de carga de datos**:
   - Verificar formato de archivos JSON
   - Revisar logs para errores específicos
   - Validar integridad de datos

### Logs

Los logs se guardan según la configuración en `.env`:

- Consola: Siempre activa con Rich formatting
- Archivo: Si se especifica `LOG_FILE`

## Contribución

1. Seguir principios de programación funcional
2. Documentar todas las funciones públicas
3. Agregar pruebas para nuevas funcionalidades
4. Usar type hints en Python
5. Seguir convenciones de nomenclatura SQL

## Licencia

[Especificar licencia del proyecto]

## Contacto

[Información de contacto del equipo]
