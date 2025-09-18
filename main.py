"""
Archivo principal para la ejecución del sistema de gestión de base de datos.

Este módulo orquesta las operaciones principales del sistema incluyendo:
- Inicialización de la base de datos
- Carga de datos
- Operaciones de mantenimiento

Uso:
    python main.py [comando] [opciones]
    
Comandos disponibles:
    - init: Inicializa la base de datos y esquemas
    - load: Carga datos desde archivos JSON
    - migrate: Ejecuta migraciones pendientes
    - status: Muestra el estado de la base de datos
"""

from typing import Optional
import sys
import argparse
from pathlib import Path

# Agregar el directorio src al path para importaciones
sys.path.append(str(Path(__file__).parent / "src"))

from src.config.settings import load_config
from src.database.connection import DatabaseManager
from src.database.postgis import PostGISManager
from src.utils.logger import setup_logger
from src.utils.data_loader import DataLoader

logger = setup_logger(__name__)


def main() -> None:
    """
    Función principal del sistema.
    
    Procesa argumentos de línea de comandos y ejecuta las operaciones correspondientes.
    """
    parser = argparse.ArgumentParser(
        description="Gestor de Proyectos DB - Sistema PostgreSQL con PostGIS"
    )
    
    parser.add_argument(
        "comando",
        choices=["init", "load", "migrate", "status", "railway-init", "railway-load"],
        help="Comando a ejecutar"
    )
    
    parser.add_argument(
        "--config",
        type=str,
        default=".env",
        help="Archivo de configuración (default: .env)"
    )
    
    parser.add_argument(
        "--railway",
        action="store_true",
        help="Usar configuración de Railway automáticamente"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Modo verbose para logging detallado"
    )
    
    args = parser.parse_args()
    
    try:
        # Determinar archivo de configuración
        config_file = args.config
        if args.railway or args.comando.startswith("railway-"):
            config_file = ".env.railway"
            logger.info("🚂 Usando configuración de Railway")
        
        # Cargar configuración
        config = load_config(config_file)
        logger.info(f"Configuración cargada desde: {config_file}")
        
        # Mostrar tipo de conexión
        if config["database"].is_railway:
            logger.info("🌐 Conectando a Railway PostgreSQL")
        else:
            logger.info("🏠 Conectando a PostgreSQL local")
        
        # Ejecutar comando
        if args.comando in ["init", "railway-init"]:
            init_database(config)
        elif args.comando in ["load", "railway-load"]:
            load_data(config)
        elif args.comando == "migrate":
            run_migrations(config)
        elif args.comando == "status":
            show_status(config)
            
    except Exception as e:
        logger.error(f"Error durante la ejecución: {e}")
        sys.exit(1)


def init_database(config) -> None:
    """Inicializa la base de datos y esquemas."""
    logger.info("🚀 Iniciando inicialización de base de datos...")
    
    try:
        # Crear manejador de base de datos
        db_manager = DatabaseManager(config["database"])
        
        # Verificar conexión
        logger.info("🔗 Verificando conexión a PostgreSQL...")
        if not db_manager.test_connection():
            logger.error("❌ No se pudo conectar a PostgreSQL")
            return
        
        logger.info("✅ Conexión a PostgreSQL exitosa")
        
        # Crear base de datos si no existe
        logger.info("📦 Creando base de datos si no existe...")
        db_manager.create_database()
        
        # Configurar PostGIS
        logger.info("🗺️ Configurando PostGIS...")
        postgis_manager = PostGISManager(db_manager)
        if postgis_manager.enable_postgis():
            logger.info("✅ PostGIS configurado correctamente")
        else:
            logger.warning("⚠️ No se pudo configurar PostGIS")
        
        # Ejecutar scripts SQL
        logger.info("📋 Ejecutando scripts de inicialización...")
        sql_files = [
            "sql/01_init_database.sql",
            "sql/02_create_procesos_table.sql", 
            "sql/03_create_contratos_table.sql",
            "sql/04_create_views.sql"
        ]
        
        for sql_file in sql_files:
            try:
                logger.info(f"📄 Ejecutando {sql_file}...")
                success = db_manager.execute_sql_file(sql_file)
                if success:
                    logger.info(f"✅ {sql_file} ejecutado correctamente")
                else:
                    logger.error(f"❌ Error ejecutando {sql_file}")
                    return False
            except Exception as e:
                logger.error(f"❌ Error ejecutando {sql_file}: {e}")
                return False
        
        logger.info("🎉 Inicialización de base de datos completada!")
        
    except Exception as e:
        logger.error(f"❌ Error durante la inicialización: {e}")
        raise


def load_data(config) -> None:
    """Carga datos desde archivos JSON."""
    logger.info("📊 Iniciando carga de datos...")
    
    try:
        # Crear manejador de base de datos
        db_manager = DatabaseManager(config["database"])
        
        # Verificar conexión
        if not db_manager.test_connection():
            logger.error("❌ No se pudo conectar a PostgreSQL")
            return
            
        # Crear cargador de datos
        data_loader = DataLoader(db_manager)
        
        # Cargar contratos
        contratos_file = config.get("CONTRATOS_FILE", "app_outputs/emprestito_outputs/emp_contratos.json")
        logger.info(f"📋 Cargando contratos desde {contratos_file}...")
        from pathlib import Path
        contratos_loaded, _ = data_loader.load_contratos_from_json(Path(contratos_file))
        logger.info(f"✅ {contratos_loaded} contratos cargados")
        
        # Cargar procesos
        procesos_file = config.get("PROCESOS_FILE", "app_outputs/emprestito_outputs/emp_procesos.json")
        logger.info(f"📋 Cargando procesos desde {procesos_file}...")
        procesos_loaded, _ = data_loader.load_procesos_from_json(Path(procesos_file))
        logger.info(f"✅ {procesos_loaded} procesos cargados")
        
        logger.info("🎉 Carga de datos completada!")
        
    except Exception as e:
        logger.error(f"❌ Error durante la carga de datos: {e}")
        raise


def run_migrations(config) -> None:
    """Ejecuta migraciones pendientes."""
    logger.info("🔄 Ejecutando migraciones...")
    
    try:
        # Crear manejador de base de datos
        db_manager = DatabaseManager(config["database"])
        
        # Verificar conexión
        if not db_manager.test_connection():
            logger.error("❌ No se pudo conectar a PostgreSQL")
            return
            
        # Buscar archivos de migración
        migrations_dir = Path("sql/migrations")
        if migrations_dir.exists():
            migration_files = sorted(migrations_dir.glob("*.sql"))
            
            for migration_file in migration_files:
                logger.info(f"🔄 Ejecutando migración: {migration_file.name}")
                try:
                    db_manager.execute_sql_file(str(migration_file))
                    logger.info(f"✅ Migración {migration_file.name} completada")
                except Exception as e:
                    logger.error(f"❌ Error en migración {migration_file.name}: {e}")
        else:
            logger.info("📂 No se encontró directorio de migraciones")
        
        logger.info("🎉 Migraciones completadas!")
        
    except Exception as e:
        logger.error(f"❌ Error ejecutando migraciones: {e}")
        raise


def show_status(config) -> None:
    """Muestra el estado actual de la base de datos."""
    logger.info("📊 Verificando estado de la base de datos...")
    
    try:
        # Crear manejador de base de datos
        db_manager = DatabaseManager(config["database"])
        
        # Verificar conexión
        if not db_manager.test_connection():
            logger.error("❌ No se pudo conectar a PostgreSQL")
            return
            
        logger.info("✅ Conexión a PostgreSQL: OK")
        
        with db_manager.get_session() as session:
            # Verificar PostGIS
            result = session.execute("SELECT PostGIS_Version();").fetchone()
            if result:
                logger.info(f"🗺️ PostGIS versión: {result[0]}")
            
            # Contar registros en tablas
            tables = ['contratos', 'procesos']
            for table in tables:
                try:
                    count_result = session.execute(f"SELECT COUNT(*) FROM {table};").fetchone()
                    count = count_result[0] if count_result else 0
                    logger.info(f"📋 Tabla {table}: {count} registros")
                except Exception as e:
                    logger.warning(f"⚠️ Error consultando tabla {table}: {e}")
        
        logger.info("🎉 Verificación de estado completada!")
        
    except Exception as e:
        logger.error(f"❌ Error verificando estado: {e}")
        raise


if __name__ == "__main__":
    main()