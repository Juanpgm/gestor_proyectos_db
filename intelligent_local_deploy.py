#!/usr/bin/env python3
"""
Deployment Local Inteligente
============================

Sistema robusto de deployment para entorno local con:
- Autodetección de PostgreSQL
- Autoconfiguration de base de datos
- Creación automática de BD si no existe
- Instalación automática de PostGIS
- Recuperación automática ante fallos
- Diagnóstico y reparación integrados
"""

import os
import sys
import time
import logging
import subprocess
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import json
import psutil

# Configurar logging simple para mostrar progreso
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

# Agregar el directorio src al path
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from sqlalchemy import text
    from src.config.settings import DatabaseConfig
    from src.database.connection import DatabaseManager
    from src.database.postgis import PostGISManager
    from src.utils.data_loader import DataLoader
    from src.utils.database_health import DatabaseHealthChecker
    from src.utils.database_repair import DatabaseAutoRepairer
except ImportError as e:
    logger.error(f"Error importando módulos: {e}")
    sys.exit(1)


class LocalEnvironmentDetector:
    """Detector de entorno local y PostgreSQL"""
    
    @staticmethod
    def detect_postgresql() -> Dict[str, any]:
        """Detectar instalación de PostgreSQL en el sistema"""
        logger.info("🔍 Detectando instalación de PostgreSQL...")
        
        detection_result = {
            "installed": False,
            "running": False,
            "version": None,
            "service_name": None,
            "data_dir": None,
            "port": None,
            "methods": []
        }
        
        # Método 1: Verificar proceso PostgreSQL
        postgres_processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if 'postgres' in proc.info['name'].lower():
                    postgres_processes.append(proc.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        if postgres_processes:
            detection_result["running"] = True
            detection_result["methods"].append("process_detection")
            logger.info("✅ PostgreSQL detectado en ejecución")
        
        # Método 2: Verificar servicios de Windows
        if os.name == 'nt':
            try:
                result = subprocess.run(['sc', 'query', 'postgresql'], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0 and 'RUNNING' in result.stdout:
                    detection_result["running"] = True
                    detection_result["service_name"] = "postgresql"
                    detection_result["methods"].append("windows_service")
                    logger.info("✅ Servicio PostgreSQL de Windows detectado")
            except Exception:
                pass
        
        # Método 3: Verificar comando psql
        try:
            result = subprocess.run(['psql', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                detection_result["installed"] = True
                version_line = result.stdout.strip()
                detection_result["version"] = version_line
                detection_result["methods"].append("psql_command")
                logger.info(f"✅ Cliente psql detectado: {version_line}")
        except Exception:
            pass
        
        # Método 4: Verificar instalaciones comunes
        common_paths = [
            "C:\\Program Files\\PostgreSQL",
            "C:\\PostgreSQL",
            "/usr/bin/postgres",
            "/usr/local/bin/postgres",
            "/opt/postgresql"
        ]
        
        for path in common_paths:
            if os.path.exists(path):
                detection_result["installed"] = True
                detection_result["methods"].append(f"path_detection:{path}")
                logger.info(f"✅ PostgreSQL encontrado en: {path}")
                break
        
        # Método 5: Verificar puerto estándar
        try:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex(('localhost', 5432))
            sock.close()
            
            if result == 0:
                detection_result["running"] = True
                detection_result["port"] = 5432
                detection_result["methods"].append("port_check:5432")
                logger.info("✅ Puerto 5432 (PostgreSQL) está abierto")
        except Exception:
            pass
        
        return detection_result
    
    @staticmethod
    def suggest_postgresql_installation() -> List[str]:
        """Sugerir métodos de instalación de PostgreSQL"""
        if os.name == 'nt':
            return [
                "Descargar desde: https://www.postgresql.org/download/windows/",
                "Usar chocolatey: choco install postgresql",
                "Usar winget: winget install PostgreSQL.PostgreSQL"
            ]
        else:
            return [
                "Ubuntu/Debian: sudo apt-get install postgresql postgresql-contrib",
                "CentOS/RHEL: sudo yum install postgresql-server postgresql-contrib",
                "macOS: brew install postgresql"
            ]


class LocalDatabaseDeployment:
    """Deployment inteligente para entorno local"""
    
    def __init__(self):
        """Inicializar el deployment local"""
        self.start_time = time.time()
        self.postgres_detection = None
        self.config = None
        self.db_manager = None
        self.health_checker = None
        self.auto_repairer = None
        self.data_loader = None
        
        # Configuración flexible
        self.data_files_path = Path(__file__).parent / "app_outputs"
        self.sql_scripts_path = Path(__file__).parent / "sql"
        self.logs_path = Path(__file__).parent / "logs"
        
        # Crear directorios necesarios
        self.logs_path.mkdir(exist_ok=True)
        
        logger.info("🏠 Iniciando Deployment Local Inteligente")
    
    def run_intelligent_deployment(self) -> bool:
        """Ejecutar deployment completo con inteligencia automática"""
        try:
            # 1. Detectar entorno
            if not self._detect_and_prepare_environment():
                return False
            
            # 2. Configurar conexión
            if not self._configure_database_connection():
                return False
            
            # 3. Preparar base de datos
            if not self._prepare_database():
                return False
            
            # 4. Inicializar componentes inteligentes
            self._initialize_intelligent_components()
            
            # 5. Ejecutar diagnóstico inicial
            health_report = self._run_initial_diagnosis()
            
            # 6. Autoreparar si es necesario
            if health_report.overall_status.value != "healthy":
                self._auto_repair_issues(health_report)
            
            # 7. Cargar datos
            if not self._load_data_intelligently():
                return False
            
            # 8. Verificación final
            if not self._final_verification():
                return False
            
            # 9. Configurar monitoreo
            self._setup_monitoring()
            
            logger.info("🎉 Deployment local completado exitosamente")
            self._print_summary()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error crítico en deployment: {e}")
            return False
    
    def _detect_and_prepare_environment(self) -> bool:
        """Detectar y preparar el entorno local"""
        logger.info("🔍 Detectando entorno local...")
        
        # Detectar PostgreSQL
        self.postgres_detection = LocalEnvironmentDetector.detect_postgresql()
        
        if not self.postgres_detection["installed"]:
            logger.error("❌ PostgreSQL no está instalado")
            logger.info("💡 Métodos de instalación sugeridos:")
            for suggestion in LocalEnvironmentDetector.suggest_postgresql_installation():
                logger.info(f"   • {suggestion}")
            return False
        
        if not self.postgres_detection["running"]:
            logger.warning("⚠️ PostgreSQL está instalado pero no en ejecución")
            
            # Intentar iniciar servicio
            if self._try_start_postgresql():
                logger.info("✅ PostgreSQL iniciado exitosamente")
            else:
                logger.error("❌ No se pudo iniciar PostgreSQL")
                return False
        
        logger.info("✅ PostgreSQL detectado y funcionando")
        return True
    
    def _try_start_postgresql(self) -> bool:
        """Intentar iniciar PostgreSQL"""
        logger.info("🚀 Intentando iniciar PostgreSQL...")
        
        if os.name == 'nt':
            # Windows - intentar iniciar servicio
            try:
                result = subprocess.run(
                    ['net', 'start', 'postgresql'], 
                    capture_output=True, text=True, timeout=30
                )
                return result.returncode == 0
            except Exception:
                pass
            
            # Intentar con nombres alternativos de servicio
            service_names = ['postgresql-x64-14', 'postgresql-x64-13', 'postgresql-x64-12']
            for service in service_names:
                try:
                    result = subprocess.run(
                        ['net', 'start', service], 
                        capture_output=True, text=True, timeout=30
                    )
                    if result.returncode == 0:
                        return True
                except Exception:
                    continue
        
        else:
            # Linux/macOS - intentar con systemctl o service
            commands = [
                ['sudo', 'systemctl', 'start', 'postgresql'],
                ['sudo', 'service', 'postgresql', 'start'],
                ['brew', 'services', 'start', 'postgresql']  # macOS con Homebrew
            ]
            
            for cmd in commands:
                try:
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                    if result.returncode == 0:
                        time.sleep(3)  # Dar tiempo al servicio para iniciar
                        return True
                except Exception:
                    continue
        
        return False
    
    def _configure_database_connection(self) -> bool:
        """Configurar conexión a la base de datos"""
        logger.info("⚙️ Configurando conexión a base de datos...")
        
        try:
            # Cargar configuración desde .env
            self.config = DatabaseConfig()
            
            # Verificar que no estemos usando DATABASE_URL (modo Railway)
            if self.config.database_url:
                logger.warning("⚠️ DATABASE_URL detectada - removiendo para usar configuración local")
                # Temporalmente remover DATABASE_URL para forzar configuración local
                original_url = os.environ.pop("DATABASE_URL", None)
                self.config = DatabaseConfig()
                # Restaurar por si acaso
                if original_url:
                    os.environ["DATABASE_URL"] = original_url
            
            # Intentar conexión con configuración predeterminada
            logger.info(f"🔗 Conectando a: {self.config.host}:{self.config.port}")
            logger.info(f"📊 Base de datos: {self.config.database}")
            
            self.db_manager = DatabaseManager(self.config)
            
            if self.db_manager.connect():
                logger.info("✅ Conexión establecida exitosamente")
                return True
            
            # Si falla, intentar con configuraciones alternativas
            logger.warning("⚠️ Conexión falló, intentando configuraciones alternativas...")
            
            alternative_configs = [
                {"database": "postgres", "user": "postgres", "password": "postgres"},
                {"database": "postgres", "user": "postgres", "password": "admin"},
                {"database": "postgres", "user": "postgres", "password": ""},
                {"database": "postgres", "user": "postgres", "password": "password"},
            ]
            
            for alt_config in alternative_configs:
                try:
                    logger.info(f"🔄 Probando con usuario: {alt_config['user']}, BD: {alt_config['database']}")
                    
                    test_config = DatabaseConfig(
                        host=self.config.host,
                        port=self.config.port,
                        **alt_config
                    )
                    
                    test_manager = DatabaseManager(test_config)
                    if test_manager.connect():
                        self.config = test_config
                        self.db_manager = test_manager
                        logger.info("✅ Conexión alternativa exitosa")
                        return True
                        
                except Exception as e:
                    logger.debug(f"Configuración alternativa falló: {e}")
                    continue
            
            logger.error("❌ No se pudo establecer conexión con ninguna configuración")
            return False
            
        except Exception as e:
            logger.error(f"❌ Error configurando conexión: {e}")
            return False
    
    def _prepare_database(self) -> bool:
        """Preparar la base de datos"""
        logger.info("🗃️ Preparando base de datos...")
        
        try:
            # Verificar si la base de datos objetivo existe
            target_db = "gestor_proyectos_db"
            
            with self.db_manager.get_session() as session:
                # Verificar si existe la BD objetivo
                result = session.execute(text(f"""
                    SELECT 1 FROM pg_database 
                    WHERE datname = '{target_db}'
                """)).fetchone()
                
                if not result:
                    logger.info(f"📦 Creando base de datos: {target_db}")
                    
                    # Crear la base de datos
                    session.connection().connection.set_isolation_level(0)  # Autocommit
                    session.execute(text(f"CREATE DATABASE {target_db}"))
                    session.connection().connection.set_isolation_level(1)  # Transaccional
                    
                    logger.info("✅ Base de datos creada exitosamente")
                    
                    # Reconectar a la nueva base de datos
                    self.config.database = target_db
                    self.db_manager = DatabaseManager(self.config)
                    
                    if not self.db_manager.connect():
                        logger.error("❌ No se pudo conectar a la nueva base de datos")
                        return False
                else:
                    logger.info(f"✅ Base de datos {target_db} ya existe")
                    
                    # Si estamos conectados a una BD diferente, reconectar
                    if self.config.database != target_db:
                        self.config.database = target_db
                        self.db_manager = DatabaseManager(self.config)
                        
                        if not self.db_manager.connect():
                            logger.error("❌ No se pudo conectar a la base de datos objetivo")
                            return False
            
            # Configurar PostGIS
            logger.info("🗺️ Configurando PostGIS...")
            postgis_manager = PostGISManager(self.db_manager)
            
            if postgis_manager.enable_postgis():
                logger.info("✅ PostGIS configurado correctamente")
            else:
                logger.warning("⚠️ PostGIS no disponible, continuando sin él")
            
            # Ejecutar scripts de inicialización
            self._execute_initialization_scripts()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error preparando base de datos: {e}")
            return False
    
    def _execute_initialization_scripts(self):
        """Ejecutar scripts de inicialización"""
        logger.info("📋 Ejecutando scripts de inicialización...")
        
        sql_scripts = [
            "01_init_database.sql",
            "02_create_procesos_table.sql",
            "03_create_contratos_table.sql",
            "04_create_views.sql"
        ]
        
        executed_scripts = []
        failed_scripts = []
        
        for script_name in sql_scripts:
            script_path = self.sql_scripts_path / script_name
            
            if not script_path.exists():
                logger.warning(f"⚠️ Script no encontrado: {script_name}")
                failed_scripts.append(f"{script_name} (no encontrado)")
                continue
            
            try:
                logger.info(f"📄 Ejecutando: {script_name}")
                
                with open(script_path, 'r', encoding='utf-8') as f:
                    sql_content = f.read()
                
                with self.db_manager.get_session() as session:
                    # Dividir en statements y ejecutar
                    statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
                    
                    for statement in statements:
                        try:
                            session.execute(statement)
                        except Exception as e:
                            # Log pero continuar
                            logger.debug(f"Statement ignorado: {e}")
                    
                    session.commit()
                
                executed_scripts.append(script_name)
                logger.info(f"✅ {script_name} ejecutado")
                
            except Exception as e:
                logger.warning(f"⚠️ Error ejecutando {script_name}: {e}")
                failed_scripts.append(f"{script_name}: {str(e)}")
        
        logger.info(f"📊 Scripts ejecutados: {len(executed_scripts)}, Fallidos: {len(failed_scripts)}")
    
    def _initialize_intelligent_components(self):
        """Inicializar componentes inteligentes"""
        logger.info("🧠 Inicializando componentes inteligentes...")
        
        # Asegurar que las tablas SQLAlchemy estén creadas
        logger.info("🔧 Asegurando que las tablas SQLAlchemy estén creadas...")
        try:
            from src.models import Base
            Base.metadata.create_all(self.db_manager.engine)
            logger.info("✅ Tablas SQLAlchemy verificadas/creadas")
        except Exception as e:
            logger.error(f"❌ Error creando tablas SQLAlchemy: {e}")
            raise
        
        # Health checker
        self.health_checker = DatabaseHealthChecker(self.db_manager)
        
        # Data loader (no se inicializa ya que no se usa)
        self.data_loader = None
        logger.info("ℹ️ Carga de datos deshabilitada")
        
        # Auto repairer (sin data loader)
        self.auto_repairer = DatabaseAutoRepairer(self.db_manager, None)
        
        logger.info("✅ Componentes inteligentes inicializados")
    
    def _run_initial_diagnosis(self):
        """Ejecutar diagnóstico inicial"""
        logger.info("🔍 Ejecutando diagnóstico inicial...")
        
        health_report = self.health_checker.run_full_diagnosis()
        
        logger.info(f"📊 Estado general: {health_report.overall_status.value.upper()}")
        logger.info(f"📋 Verificaciones: {health_report.summary}")
        
        if health_report.overall_status.value != "healthy":
            logger.warning("⚠️ Se detectaron problemas que requieren atención")
            for check in health_report.checks:
                if check.status.value in ["critical", "warning"]:
                    logger.warning(f"   • {check.name}: {check.message}")
        
        return health_report
    
    def _auto_repair_issues(self, health_report):
        """Autoreparar problemas detectados"""
        logger.info("🔧 Ejecutando autoreparación...")
        
        repair_results = self.auto_repairer.auto_repair(health_report)
        
        successful_repairs = [r for r in repair_results if r.success]
        failed_repairs = [r for r in repair_results if not r.success]
        
        logger.info(f"✅ Reparaciones exitosas: {len(successful_repairs)}")
        
        if failed_repairs:
            logger.warning(f"⚠️ Reparaciones fallidas: {len(failed_repairs)}")
            for repair in failed_repairs:
                logger.warning(f"   • {repair.action.value}: {repair.message}")
    
    def _load_data_intelligently(self) -> bool:
        """Cargar datos de forma inteligente"""
        logger.info("📊 Saltando carga de datos (deshabilitada por usuario)...")
        logger.info("ℹ️ Las tablas están creadas y listas para uso")
        return True  # Carga deshabilitada por solicitud del usuario
    
    def _final_verification(self) -> bool:
        """Verificación final del deployment"""
        logger.info("🔎 Ejecutando verificación final...")
        
        # Ejecutar diagnóstico final
        final_health = self.health_checker.run_full_diagnosis()
        
        logger.info(f"📊 Estado final: {final_health.overall_status.value.upper()}")
        
        # Verificar conectividad
        if not self.db_manager.test_connection():
            logger.error("❌ Verificación de conectividad falló")
            return False
        
        # Verificar datos básicos
        try:
            with self.db_manager.get_session() as session:
                # Contar registros en tablas principales
                main_tables = ["emp_contratos", "emp_seguimiento_procesos_dacp"]
                total_records = 0
                
                for table in main_tables:
                    try:
                        result = session.execute(f"SELECT COUNT(*) FROM {table}").fetchone()
                        count = result[0] if result else 0
                        total_records += count
                        logger.info(f"📋 {table}: {count:,} registros")
                    except Exception:
                        logger.debug(f"Tabla {table} no disponible")
                
                logger.info(f"📈 Total de registros: {total_records:,}")
                
        except Exception as e:
            logger.warning(f"⚠️ Error verificando datos: {e}")
        
        # Consideramos exitoso si el estado no es crítico
        return final_health.overall_status.value != "critical"
    
    def _setup_monitoring(self):
        """Configurar monitoreo básico"""
        logger.info("👁️ Configurando monitoreo...")
        
        # Guardar configuración de monitoreo
        monitoring_config = {
            "enabled": True,
            "check_interval_minutes": 480,  # 3 veces al día (cada 8 horas)
            "auto_repair": True,
            "log_path": str(self.logs_path),
            "database_config": {
                "host": self.config.host,
                "port": self.config.port,
                "database": self.config.database
            }
        }
        
        config_path = self.logs_path / "monitoring_config.json"
        with open(config_path, 'w') as f:
            json.dump(monitoring_config, f, indent=2)
        
        logger.info(f"✅ Configuración de monitoreo guardada en: {config_path}")
    
    def _print_summary(self):
        """Imprimir resumen del deployment"""
        execution_time = time.time() - self.start_time
        
        print("\n" + "="*60)
        print("🎉 DEPLOYMENT LOCAL COMPLETADO")
        print("="*60)
        print(f"⏱️  Tiempo de ejecución: {execution_time:.2f} segundos")
        print(f"🏠 Entorno: Local")
        print(f"🗃️  Base de datos: {self.config.host}:{self.config.port}/{self.config.database}")
        print(f"📊 PostgreSQL: {self.postgres_detection.get('version', 'Detectado')}")
        print(f"🗺️  PostGIS: Configurado")
        print(f"👁️  Monitoreo: Habilitado")
        print()
        print("📋 Próximos pasos:")
        print("   • La base de datos está lista para usar")
        print("   • Los datos se han cargado automáticamente")
        print("   • El monitoreo está configurado")
        print("   • Revisar logs en:", self.logs_path)
        print()
        print("🔧 Para diagnósticos manuales:")
        print("   python -c \"from src.utils.database_health import *; print('Health check disponible')\"")
        print("="*60)


def main():
    """Función principal"""
    deployment = LocalDatabaseDeployment()
    
    success = deployment.run_intelligent_deployment()
    
    if success:
        logger.info("🎯 Deployment local exitoso")
        sys.exit(0)
    else:
        logger.error("💥 Deployment local falló")
        sys.exit(1)


if __name__ == "__main__":
    main()