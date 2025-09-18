#!/usr/bin/env python3
"""
🚂 Script de Deployment de Base de Datos para Railway
==================================================

Este script inicializa la base de datos PostgreSQL en Railway y carga todos los datos
directamente usando los scripts de carga existentes.

NO incluye funcionalidades de API - solo base de datos y carga de datos.
"""

import os
import sys
import logging
from pathlib import Path

# Agregar el directorio src al path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.config.settings import DatabaseConfig
from src.database.connection import DatabaseManager
from src.database.postgis import PostGISManager
from src.utils.data_loader import DataLoader
from railway_config import create_railway_connection

# Configurar logging para Railway
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class RailwayDatabaseDeployment:
    """
    Manejador del deployment de base de datos en Railway
    """
    
    def __init__(self):
        """Inicializar el deployment con Railway"""
        self.start_time = time.time()
        
        try:
            # Intentar crear conexión Railway
            self.db_manager = create_railway_connection()
            
            if self.db_manager:
                print("✅ Conectado a Railway PostgreSQL")
                self.is_railway = True
                # No necesitamos config separado, lo maneja railway_config
                self.config = None
            else:
                # Fallback a configuración local
                print("⚠️  Railway no disponible, usando configuración local")
                self.config = DatabaseConfig()
                self.db_manager = DatabaseManager(self.config.to_dict())
                self.is_railway = False
                
            # Inicializar componentes
            self.data_loader = DataLoader(self.db_manager)
            self.data_files_path = Path(__file__).parent / "app_outputs"
            
            logger.info(f"🚂 Deployment inicializado {'en Railway' if self.is_railway else 'localmente'}")
            
        except Exception as e:
            logger.error(f"❌ Error inicializando deployment: {e}")
            raise
    
    def verify_environment(self):
        """Verificar que el entorno esté configurado correctamente"""
        logger.info("🔍 Verificando entorno...")
        
        # Verificar variables de entorno críticas
        required_vars = []
        if self.is_railway:
            if not os.environ.get("DATABASE_URL"):
                required_vars.append("DATABASE_URL")
        else:
            if not all([
                os.environ.get("DB_HOST"),
                os.environ.get("DB_NAME"),
                os.environ.get("DB_USER"),
                os.environ.get("DB_PASSWORD")
            ]):
                logger.warning("⚠️ Variables de DB locales no completamente configuradas")
        
        if required_vars:
            logger.error(f"❌ Variables faltantes: {', '.join(required_vars)}")
            return False
        
        # Verificar archivos de datos
        if not self.data_files_path.exists():
            logger.error(f"❌ Directorio de datos no encontrado: {self.data_files_path}")
            return False
        
        logger.info("✅ Entorno verificado correctamente")
        return True
    
    def initialize_database(self):
        """Inicializar la base de datos y crear todas las tablas"""
        logger.info("🗃️ Inicializando base de datos...")
        
        try:
            # Ya tenemos db_manager desde __init__
            if not self.db_manager:
                logger.error("❌ DatabaseManager no inicializado")
                return False
            
            # Verificar conexión
            if not self.db_manager.test_connection():
                logger.error("❌ No se pudo conectar a la base de datos")
                return False
            
            logger.info("✅ Conexión a base de datos establecida")
            
            # Configurar PostGIS si está disponible
            logger.info("🗺️ Configurando PostGIS...")
            postgis_manager = PostGISManager(self.db_manager)
            if postgis_manager.enable_postgis():
                logger.info("✅ PostGIS configurado correctamente")
            else:
                logger.warning("⚠️ PostGIS no disponible, continuando sin él")
            
            # Ejecutar scripts SQL con manejo de errores mejorado
            logger.info("📋 Ejecutando scripts de inicialización...")
            sql_files = [
                "sql/01_init_database.sql",
                "sql/02_create_procesos_table.sql", 
                "sql/03_create_contratos_table.sql",
                "sql/04_create_views.sql"
            ]
            
            for sql_file in sql_files:
                sql_path = Path(sql_file)
                if sql_path.exists():
                    logger.info(f"📄 Ejecutando {sql_file}...")
                    try:
                        success = self.db_manager.execute_sql_file(str(sql_path))
                        if success:
                            logger.info(f"✅ {sql_file} ejecutado correctamente")
                        else:
                            logger.warning(f"⚠️ Algunos errores en {sql_file} (puede ser normal si ya existe)")
                    except Exception as e:
                        error_msg = str(e).lower()
                        # Errores que son normales cuando las tablas ya existen
                        if any(keyword in error_msg for keyword in [
                            'ya existe', 'already exists', 'duplicate', 
                            'duplicateobject', 'relation already exists'
                        ]):
                            logger.info(f"ℹ️ {sql_file}: Elementos ya existen (saltando)")
                        else:
                            logger.error(f"❌ Error en {sql_file}: {str(e)}")
                            return False
                else:
                    logger.warning(f"⚠️ Archivo {sql_file} no encontrado")
            
            logger.info("✅ Inicialización de base de datos completada")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error inicializando base de datos: {str(e)}")
            return False
    
    def load_all_data(self):
        """Cargar todos los datos usando el DataLoader existente"""
        logger.info("📊 Iniciando carga de datos...")
        
        try:
            # Crear data loader
            self.data_loader = DataLoader(self.db_manager)
            
            success_count = 0
            total_count = 0
            
            # Cargar contratos si el archivo existe
            contratos_file = self.data_files_path / "emprestito_outputs" / "emp_contratos.json"
            if contratos_file.exists():
                logger.info(f"📋 Cargando contratos desde {contratos_file}...")
                total_count += 1
                try:
                    contratos_loaded, _ = self.data_loader.load_contratos_from_json(contratos_file)
                    logger.info(f"✅ {contratos_loaded} contratos cargados")
                    success_count += 1
                except Exception as e:
                    logger.error(f"❌ Error cargando contratos: {str(e)}")
            else:
                logger.warning(f"⚠️ Archivo de contratos no encontrado: {contratos_file}")
            
            # Cargar procesos si el archivo existe
            procesos_file = self.data_files_path / "emprestito_outputs" / "emp_procesos.json"
            if procesos_file.exists():
                logger.info(f"📋 Cargando procesos desde {procesos_file}...")
                total_count += 1
                try:
                    procesos_loaded, _ = self.data_loader.load_procesos_from_json(procesos_file)
                    logger.info(f"✅ {procesos_loaded} procesos cargados")
                    success_count += 1
                except Exception as e:
                    logger.error(f"❌ Error cargando procesos: {str(e)}")
            else:
                logger.warning(f"⚠️ Archivo de procesos no encontrado: {procesos_file}")
            
            # Buscar otros archivos JSON y intentar cargarlos
            for output_dir in self.data_files_path.iterdir():
                if output_dir.is_dir() and output_dir.name.endswith("_outputs"):
                    for json_file in output_dir.glob("*.json"):
                        if json_file.name not in ["emp_contratos.json", "emp_procesos.json"]:
                            logger.info(f"📄 Archivo adicional encontrado: {json_file}")
                            # Aquí se podrían agregar más loaders específicos según sea necesario
            
            logger.info(f"📊 Carga completada: {success_count}/{total_count} módulos exitosos")
            return success_count > 0  # Éxito si al menos un archivo se cargó
            
        except Exception as e:
            logger.error(f"❌ Error durante la carga de datos: {str(e)}")
            return False
    
    def verify_data_load(self):
        """Verificar que los datos se cargaron correctamente"""
        logger.info("🔍 Verificando carga de datos...")
        
        try:
            # Usar el método get_status del data loader o consultar directamente
            with self.db_manager.get_session() as session:
                # Obtener lista de tablas y sus conteos
                tables_info = {}
                
                # Consultar tablas principales que conocemos
                known_tables = [
                    "emp_seguimiento_procesos_dacp",
                    "emp_contratos", 
                    "contratos_secop",
                    "procesos_secop",
                    "ejecucion_presupuestal"
                ]
                
                for table_name in known_tables:
                    try:
                        result = session.execute(f"SELECT COUNT(*) FROM {table_name};").fetchone()
                        count = result[0] if result else 0
                        tables_info[table_name] = count
                    except Exception as e:
                        logger.debug(f"Tabla {table_name} no existe o error: {str(e)}")
                        # No es crítico si una tabla no existe
            
            if not tables_info:
                logger.error("❌ No se encontraron tablas en la base de datos")
                return False
            
            logger.info("📋 Resumen de tablas:")
            total_records = 0
            
            for table_name, count in tables_info.items():
                if count > 0:  # Solo mostrar tablas con datos
                    logger.info(f"   • {table_name}: {count:,} registros")
                    total_records += count
            
            logger.info(f"✅ Total: {total_records:,} registros en {len([t for t in tables_info.values() if t > 0])} tablas")
            
            # Verificar que al menos algunas tablas tienen datos
            tables_with_data = [table for table, count in tables_info.items() if count > 0]
            
            if not tables_with_data:
                logger.warning("⚠️ Ninguna tabla tiene datos")
                return False
            
            logger.info(f"✅ {len(tables_with_data)} tablas con datos encontradas")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error verificando datos: {str(e)}")
            return False
    
    def cleanup(self):
        """Limpiar recursos"""
        logger.info("🧹 Limpiando recursos...")
        
        if self.db_manager:
            try:
                # Cerrar la sesión si existe
                if hasattr(self.db_manager, 'session') and self.db_manager.session:
                    self.db_manager.session.close()
                
                # Cerrar el engine si existe
                if hasattr(self.db_manager, 'engine') and self.db_manager.engine:
                    self.db_manager.engine.dispose()
                
                logger.info("✅ Conexión cerrada correctamente")
            except Exception as e:
                logger.warning(f"⚠️ Error cerrando conexión: {str(e)}")
    
    def run_deployment(self):
        """Ejecutar el deployment completo"""
        logger.info("🚀 INICIANDO DEPLOYMENT DE BASE DE DATOS RAILWAY")
        logger.info("=" * 60)
        
        success = False
        
        try:
            # 1. Verificar entorno
            if not self.verify_environment():
                logger.error("❌ Verificación de entorno falló")
                return False
            
            # 2. Inicializar base de datos
            if not self.initialize_database():
                logger.error("❌ Inicialización de base de datos falló")
                return False
            
            # 3. Cargar datos
            if not self.load_all_data():
                logger.error("❌ Carga de datos falló")
                return False
            
            # 4. Verificar carga
            if not self.verify_data_load():
                logger.error("❌ Verificación de datos falló")
                return False
            
            logger.info("=" * 60)
            logger.info("🎉 DEPLOYMENT COMPLETADO EXITOSAMENTE")
            logger.info("✅ Base de datos inicializada y datos cargados")
            
            if self.is_railway:
                logger.info("🌐 Aplicación lista en Railway")
            else:
                logger.info("🏠 Base de datos local lista")
            
            success = True
            
        except Exception as e:
            logger.error(f"❌ Error crítico durante deployment: {str(e)}")
            success = False
        
        finally:
            self.cleanup()
        
        return success

def main():
    """Función principal"""
    deployment = RailwayDatabaseDeployment()
    
    success = deployment.run_deployment()
    
    # Exit code para Railway
    exit_code = 0 if success else 1
    logger.info(f"🔚 Finalizando con código: {exit_code}")
    
    sys.exit(exit_code)

if __name__ == "__main__":
    main()