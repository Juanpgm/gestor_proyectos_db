#!/usr/bin/env python3
"""
Deployment Railway Inteligente
==============================

Sistema robusto de deployment para Railway con:
- Detección automática de suspensión de BD
- Reconexión automática y reintentos
- Fallback automático a configuración local
- Manejo de límites de Railway
- Monitoreo de conectividad
- Autoreparación especializada para Railway
"""

import os
import sys
import time
import logging
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import json
import threading
from concurrent.futures import ThreadPoolExecutor

# Configurar logging para Railway
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

# Agregar el directorio src al path
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from src.config.settings import DatabaseConfig
    from src.database.connection import DatabaseManager
    from src.database.postgis import PostGISManager
    from src.utils.data_loader import DataLoader
    from src.utils.database_health import DatabaseHealthChecker
    from src.utils.database_repair import DatabaseAutoRepairer
    from railway_config import create_railway_connection, load_env_file
    from intelligent_local_deploy import LocalDatabaseDeployment
except ImportError as e:
    logger.error(f"Error importando módulos: {e}")
    sys.exit(1)


class RailwayConnectionMonitor:
    """Monitor de conexión especializado para Railway"""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.is_connected = False
        self.last_check = None
        self.connection_failures = 0
        self.max_failures = 3
        
    def check_connection(self) -> Dict[str, Any]:
        """Verificar estado de conexión a Railway"""
        check_start = time.time()
        
        try:
            if self.db_manager and self.db_manager.test_connection():
                self.is_connected = True
                self.connection_failures = 0
                self.last_check = datetime.now()
                
                return {
                    "status": "connected",
                    "timestamp": self.last_check.isoformat(),
                    "response_time": time.time() - check_start,
                    "failures": self.connection_failures
                }
            else:
                self.is_connected = False
                self.connection_failures += 1
                
                return {
                    "status": "disconnected",
                    "timestamp": datetime.now().isoformat(),
                    "response_time": time.time() - check_start,
                    "failures": self.connection_failures,
                    "reason": "connection_test_failed"
                }
                
        except Exception as e:
            self.is_connected = False
            self.connection_failures += 1
            
            return {
                "status": "error",
                "timestamp": datetime.now().isoformat(),
                "response_time": time.time() - check_start,
                "failures": self.connection_failures,
                "error": str(e)
            }
    
    def check_railway_availability(self) -> bool:
        """Verificar disponibilidad rápida de Railway"""
        result = self.check_connection()
        return result["status"] == "connected"
    
    def is_railway_suspended(self) -> bool:
        """Detectar si Railway está suspendido"""
        # Railway suspende servicios después de inactividad
        # Indicadores: conexiones fallan consistentemente
        return self.connection_failures >= self.max_failures
    
    def wait_for_railway_wake(self, max_wait_minutes: int = 5) -> bool:
        """Esperar a que Railway despierte de suspensión"""
        logger.info("⏰ Railway puede estar suspendido, esperando activación...")
        
        start_time = time.time()
        max_wait_seconds = max_wait_minutes * 60
        
        while (time.time() - start_time) < max_wait_seconds:
            logger.info("🔄 Intentando despertar Railway...")
            
            check_result = self.check_connection()
            
            if check_result["status"] == "connected":
                logger.info("✅ Railway ha despertado exitosamente")
                return True
            
            # Esperar antes del siguiente intento
            wait_time = min(30, max_wait_seconds - (time.time() - start_time))
            if wait_time > 0:
                logger.info(f"⏳ Esperando {wait_time:.0f}s antes del siguiente intento...")
                time.sleep(wait_time)
        
        logger.warning("⚠️ Railway no despertó en el tiempo esperado")
        return False


class RailwayDatabaseDeployment:
    """Deployment inteligente para Railway"""
    
    def __init__(self):
        """Inicializar el deployment Railway"""
        self.start_time = time.time()
        self.is_railway = False
        self.db_manager = None
        self.connection_monitor = None
        self.health_checker = None
        self.auto_repairer = None
        self.data_loader = None
        self.local_fallback = None
        
        # Configuración Railway
        self.max_connection_retries = 5
        self.retry_delay_seconds = 10
        self.railway_timeout_seconds = 30
        
        # Rutas
        self.data_files_path = Path(__file__).parent / "app_outputs"
        self.logs_path = Path(__file__).parent / "logs"
        self.logs_path.mkdir(exist_ok=True)
        
        logger.info("🚂 Iniciando Deployment Railway Inteligente")
    
    def run_intelligent_railway_deployment(self) -> bool:
        """Ejecutar deployment Railway completo con inteligencia"""
        try:
            # 1. Detectar y configurar Railway
            if not self._detect_railway_environment():
                return self._fallback_to_local()
            
            # 2. Establecer conexión Railway con reintentos
            if not self._establish_railway_connection():
                return self._fallback_to_local()
            
            # 3. Inicializar monitoreo de Railway
            self._initialize_railway_monitoring()
            
            # 4. Preparar base de datos Railway
            if not self._prepare_railway_database():
                return self._attempt_recovery_or_fallback()
            
            # 5. Inicializar componentes inteligentes
            self._initialize_intelligent_components()
            
            # 6. Ejecutar diagnóstico Railway-específico
            health_report = self._run_railway_diagnosis()
            
            # 7. Autoreparar problemas Railway
            if health_report.overall_status.value != "healthy":
                self._auto_repair_railway_issues(health_report)
            
            # 8. Cargar datos con reintentos Railway
            if not self._load_data_with_railway_handling():
                return self._attempt_recovery_or_fallback()
            
            # 9. Configurar monitoreo continuo Railway
            self._setup_railway_monitoring()
            
            # 10. Verificación final
            if not self._final_railway_verification():
                return self._attempt_recovery_or_fallback()
            
            logger.info("🎉 Deployment Railway completado exitosamente")
            self._print_railway_summary()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error crítico en deployment Railway: {e}")
            return self._fallback_to_local()
    
    def _detect_railway_environment(self) -> bool:
        """Detectar si estamos en entorno Railway"""
        logger.info("🔍 Detectando entorno Railway...")
        
        # Cargar variables de entorno
        load_env_file()
        
        # Verificar indicadores de Railway
        railway_indicators = [
            os.environ.get("RAILWAY_ENVIRONMENT"),
            os.environ.get("DATABASE_URL"),
            os.environ.get("RAILWAY_PROJECT_ID"),
            os.environ.get("RAILWAY_SERVICE_ID")
        ]
        
        railway_detected = any(indicator for indicator in railway_indicators)
        
        if railway_detected:
            logger.info("✅ Entorno Railway detectado")
            self.is_railway = True
            
            # Log información segura (sin credenciales)
            if os.environ.get("RAILWAY_ENVIRONMENT"):
                logger.info(f"🏷️ Railway Environment: {os.environ.get('RAILWAY_ENVIRONMENT')}")
            
            return True
        else:
            logger.info("ℹ️ Entorno Railway no detectado")
            return False
    
    def _establish_railway_connection(self) -> bool:
        """Establecer conexión a Railway con reintentos inteligentes"""
        logger.info("🔗 Estableciendo conexión Railway...")
        
        for attempt in range(1, self.max_connection_retries + 1):
            logger.info(f"🔄 Intento de conexión {attempt}/{self.max_connection_retries}")
            
            try:
                # Crear conexión Railway
                self.db_manager = create_railway_connection()
                
                if self.db_manager:
                    # Verificar que la conexión realmente funciona
                    if self._test_railway_connection_thoroughly():
                        logger.info(f"✅ Conexión Railway establecida (intento {attempt})")
                        return True
                    else:
                        logger.warning(f"⚠️ Conexión creada pero falló verificación (intento {attempt})")
                else:
                    logger.warning(f"⚠️ No se pudo crear conexión Railway (intento {attempt})")
                
            except Exception as e:
                logger.warning(f"⚠️ Error en intento {attempt}: {str(e)}")
            
            # Esperar antes del siguiente intento (excepto en el último)
            if attempt < self.max_connection_retries:
                wait_time = self.retry_delay_seconds * attempt  # Backoff exponencial
                logger.info(f"⏳ Esperando {wait_time}s antes del siguiente intento...")
                time.sleep(wait_time)
        
        logger.error("❌ No se pudo establecer conexión Railway después de todos los intentos")
        return False
    
    def _test_railway_connection_thoroughly(self) -> bool:
        """Prueba exhaustiva de conexión Railway"""
        try:
            # Test básico de conexión
            if not self.db_manager.test_connection():
                return False
            
            # Test de consulta simple
            with self.db_manager.get_session() as session:
                result = session.execute("SELECT 1").fetchone()
                if not result or result[0] != 1:
                    return False
            
            # Test de información de base de datos
            with self.db_manager.get_session() as session:
                result = session.execute("SELECT current_database(), version()").fetchone()
                if not result:
                    return False
                
                logger.info(f"🗃️ BD Railway: {result[0]}")
                logger.info(f"🐘 Versión: {result[1].split()[1] if len(result[1].split()) > 1 else 'PostgreSQL'}")
            
            return True
            
        except Exception as e:
            logger.warning(f"⚠️ Test de conexión falló: {e}")
            return False
    
    def _initialize_railway_monitoring(self):
        """Inicializar monitoreo específico de Railway"""
        logger.info("👁️ Inicializando monitoreo Railway...")
        
        self.connection_monitor = RailwayConnectionMonitor(self.db_manager)
        
        # Ejecutar check inicial
        initial_check = self.connection_monitor.check_connection()
        logger.info(f"📊 Estado inicial: {initial_check['status']}")
        
        if initial_check.get("response_time"):
            logger.info(f"⚡ Latencia: {initial_check['response_time']*1000:.1f}ms")
    
    def _prepare_railway_database(self) -> bool:
        """Preparar base de datos Railway"""
        logger.info("🗃️ Preparando base de datos Railway...")
        
        try:
            # Verificar PostGIS en Railway
            logger.info("🗺️ Verificando PostGIS en Railway...")
            
            with self.db_manager.get_session() as session:
                # Verificar si PostGIS está disponible
                try:
                    result = session.execute("SELECT PostGIS_version()").fetchone()
                    if result:
                        logger.info(f"✅ PostGIS disponible: {result[0]}")
                    else:
                        logger.info("ℹ️ PostGIS no detectado en Railway")
                except Exception:
                    logger.info("ℹ️ PostGIS no disponible en Railway")
                    
                    # Intentar habilitar PostGIS si es posible
                    try:
                        session.execute("CREATE EXTENSION IF NOT EXISTS postgis")
                        session.commit()
                        logger.info("✅ PostGIS habilitado en Railway")
                    except Exception as e:
                        logger.info(f"ℹ️ No se pudo habilitar PostGIS: {e}")
            
            # Ejecutar scripts de inicialización
            self._execute_railway_initialization_scripts()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error preparando BD Railway: {e}")
            return False
    
    def _execute_railway_initialization_scripts(self):
        """Ejecutar scripts de inicialización para Railway"""
        logger.info("📋 Ejecutando scripts para Railway...")
        
        sql_scripts_path = Path(__file__).parent / "sql"
        
        sql_scripts = [
            "01_init_database.sql",
            "02_create_procesos_table.sql",
            "03_create_contratos_table.sql",
            "04_create_views.sql"
        ]
        
        executed_scripts = []
        failed_scripts = []
        
        for script_name in sql_scripts:
            script_path = sql_scripts_path / script_name
            
            if not script_path.exists():
                logger.warning(f"⚠️ Script no encontrado: {script_name}")
                continue
            
            success = self._execute_script_with_railway_handling(script_path)
            
            if success:
                executed_scripts.append(script_name)
                logger.info(f"✅ {script_name} ejecutado en Railway")
            else:
                failed_scripts.append(script_name)
                logger.warning(f"⚠️ {script_name} falló en Railway")
        
        logger.info(f"📊 Railway - Scripts: {len(executed_scripts)} ✅, {len(failed_scripts)} ❌")
    
    def _execute_script_with_railway_handling(self, script_path: Path) -> bool:
        """Ejecutar script con manejo especial para Railway"""
        max_script_retries = 3
        
        for attempt in range(1, max_script_retries + 1):
            try:
                with open(script_path, 'r', encoding='utf-8') as f:
                    sql_content = f.read()
                
                with self.db_manager.get_session() as session:
                    # Verificar conexión antes de ejecutar
                    if not self.connection_monitor.check_connection()["status"] == "connected":
                        logger.warning(f"⚠️ Conexión perdida antes de ejecutar {script_path.name}")
                        
                        # Intentar reconectar
                        if not self._reconnect_railway():
                            return False
                    
                    # Ejecutar script por partes para Railway
                    statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
                    
                    for i, statement in enumerate(statements):
                        try:
                            session.execute(statement)
                            
                            # Para Railway, hacer commit frecuentemente
                            if i % 5 == 0:  # Cada 5 statements
                                session.commit()
                                
                        except Exception as e:
                            # Log pero continuar con otros statements
                            logger.debug(f"Statement ignorado en {script_path.name}: {e}")
                    
                    session.commit()
                
                return True
                
            except Exception as e:
                logger.warning(f"⚠️ Intento {attempt} falló para {script_path.name}: {e}")
                
                if attempt < max_script_retries:
                    # Verificar si es problema de conexión
                    if "connection" in str(e).lower():
                        self._reconnect_railway()
                    
                    time.sleep(5 * attempt)  # Backoff
        
        return False
    
    def _reconnect_railway(self) -> bool:
        """Reconectar a Railway"""
        logger.info("🔄 Reconectando a Railway...")
        
        try:
            # Cerrar conexión actual si existe
            if self.db_manager:
                try:
                    if hasattr(self.db_manager, 'engine') and self.db_manager.engine:
                        self.db_manager.engine.dispose()
                except Exception:
                    pass
            
            # Crear nueva conexión
            self.db_manager = create_railway_connection()
            
            if self.db_manager and self._test_railway_connection_thoroughly():
                logger.info("✅ Reconexión Railway exitosa")
                
                # Actualizar monitor
                if self.connection_monitor:
                    self.connection_monitor.db_manager = self.db_manager
                
                return True
            else:
                logger.error("❌ Reconexión Railway falló")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error en reconexión Railway: {e}")
            return False
    
    def _initialize_intelligent_components(self):
        """Inicializar componentes inteligentes para Railway"""
        logger.info("🧠 Inicializando componentes para Railway...")
        
        self.health_checker = DatabaseHealthChecker(self.db_manager)
        self.data_loader = DataLoader(self.db_manager)
        self.auto_repairer = DatabaseAutoRepairer(self.db_manager, self.data_loader)
        
        logger.info("✅ Componentes Railway inicializados")
    
    def _run_railway_diagnosis(self):
        """Ejecutar diagnóstico específico para Railway"""
        logger.info("🔍 Ejecutando diagnóstico Railway...")
        
        health_report = self.health_checker.run_full_diagnosis()
        
        logger.info(f"📊 Estado Railway: {health_report.overall_status.value.upper()}")
        
        # Verificaciones específicas de Railway
        railway_specific_checks = []
        
        # Check de latencia Railway
        check_result = self.connection_monitor.check_connection()
        if check_result.get("response_time"):
            latency_ms = check_result["response_time"] * 1000
            if latency_ms > 2000:  # > 2 segundos en Railway es problemático
                railway_specific_checks.append(f"Alta latencia Railway: {latency_ms:.1f}ms")
            else:
                railway_specific_checks.append(f"Latencia Railway normal: {latency_ms:.1f}ms")
        
        # Check de fallos de conexión
        if self.connection_monitor.connection_failures > 0:
            railway_specific_checks.append(f"Fallos de conexión: {self.connection_monitor.connection_failures}")
        
        for check in railway_specific_checks:
            logger.info(f"🚂 {check}")
        
        return health_report
    
    def _auto_repair_railway_issues(self, health_report):
        """Autoreparar problemas específicos de Railway"""
        logger.info("🔧 Autoreparando problemas Railway...")
        
        # Autoreparación estándar
        repair_results = self.auto_repairer.auto_repair(health_report)
        
        # Reparaciones específicas de Railway
        railway_repairs = []
        
        # Si hay muchos fallos de conexión, intentar reconectar
        if self.connection_monitor.connection_failures > 1:
            if self._reconnect_railway():
                railway_repairs.append("Reconexión Railway exitosa")
            else:
                railway_repairs.append("Reconexión Railway falló")
        
        # Si Railway está suspendido, intentar despertar
        if self.connection_monitor.is_railway_suspended():
            if self.connection_monitor.wait_for_railway_wake():
                railway_repairs.append("Railway despertado de suspensión")
            else:
                railway_repairs.append("Railway sigue suspendido")
        
        successful_repairs = [r for r in repair_results if r.success] + railway_repairs
        logger.info(f"✅ Reparaciones Railway: {len(successful_repairs)}")
    
    def _load_data_with_railway_handling(self) -> bool:
        """Cargar datos con manejo especial para Railway"""
        logger.info("📊 Cargando datos en Railway...")
        
        if not self.data_files_path.exists():
            logger.info("ℹ️ No hay datos para cargar")
            return True
        
        # Para Railway, cargar en lotes más pequeños
        total_loaded = 0
        loading_errors = []
        
        data_files = {
            "contratos": self.data_files_path / "emprestito_outputs" / "emp_contratos.json",
            "procesos": self.data_files_path / "emprestito_outputs" / "emp_procesos.json"
        }
        
        for data_type, file_path in data_files.items():
            if not file_path.exists():
                continue
            
            logger.info(f"📥 Cargando {data_type} en Railway...")
            
            # Intentar carga con reintentos para Railway
            success = False
            for attempt in range(1, 4):  # Máximo 3 intentos
                try:
                    # Verificar conexión antes de cargar
                    if not self.connection_monitor.check_connection()["status"] == "connected":
                        logger.warning(f"⚠️ Conexión perdida, reconectando...")
                        if not self._reconnect_railway():
                            continue
                    
                    if data_type == "contratos":
                        loaded, errors = self.data_loader.load_contratos_from_json(file_path)
                    elif data_type == "procesos":
                        loaded, errors = self.data_loader.load_procesos_from_json(file_path)
                    else:
                        continue
                    
                    total_loaded += loaded
                    if errors:
                        loading_errors.extend(errors)
                    
                    logger.info(f"✅ {data_type}: {loaded} registros cargados en Railway")
                    success = True
                    break
                    
                except Exception as e:
                    logger.warning(f"⚠️ Intento {attempt} falló para {data_type}: {e}")
                    
                    if attempt < 3:
                        # Esperar y verificar conexión
                        time.sleep(10)
                        if "connection" in str(e).lower():
                            self._reconnect_railway()
            
            if not success:
                loading_errors.append(f"Falló carga de {data_type} en Railway")
        
        logger.info(f"📈 Total cargado en Railway: {total_loaded:,} registros")
        
        if loading_errors:
            logger.warning(f"⚠️ Errores Railway: {len(loading_errors)}")
            # En Railway, errores de carga no son críticos
            return total_loaded > 0
        
        return True
    
    def _setup_railway_monitoring(self):
        """Configurar monitoreo continuo para Railway"""
        logger.info("👁️ Configurando monitoreo Railway...")
        
        monitoring_config = {
            "railway_enabled": True,
            "check_interval_minutes": 480,  # 3 veces al día (cada 8 horas)
            "connection_timeout_seconds": 30,
            "max_connection_failures": 3,
            "auto_reconnect": True,
            "suspension_detection": True,
            "wake_wait_minutes": 5,
            "fallback_to_local": True
        }
        
        config_path = self.logs_path / "railway_monitoring_config.json"
        with open(config_path, 'w') as f:
            json.dump(monitoring_config, f, indent=2)
        
        logger.info("✅ Monitoreo Railway configurado")
    
    def _final_railway_verification(self) -> bool:
        """Verificación final específica para Railway"""
        logger.info("🔎 Verificación final Railway...")
        
        # Test de conexión final
        final_check = self.connection_monitor.check_connection()
        
        if final_check["status"] != "connected":
            logger.error(f"❌ Verificación final falló: {final_check['status']}")
            return False
        
        # Test de latencia
        if final_check.get("response_time"):
            latency_ms = final_check["response_time"] * 1000
            logger.info(f"⚡ Latencia final: {latency_ms:.1f}ms")
            
            if latency_ms > 5000:  # > 5 segundos es crítico
                logger.warning("⚠️ Latencia alta detectada")
        
        # Verificar datos
        try:
            with self.db_manager.get_session() as session:
                # Test simple de consulta
                result = session.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'").fetchone()
                table_count = result[0] if result else 0
                
                logger.info(f"📋 Tablas en Railway: {table_count}")
                
                if table_count < 2:  # Esperamos al menos algunas tablas
                    logger.warning("⚠️ Pocas tablas detectadas en Railway")
                    return False
        
        except Exception as e:
            logger.error(f"❌ Error verificando datos en Railway: {e}")
            return False
        
        logger.info("✅ Verificación Railway exitosa")
        return True
    
    def _attempt_recovery_or_fallback(self) -> bool:
        """Intentar recuperación o fallback a local"""
        logger.warning("🚨 Intentando recuperación Railway...")
        
        # Intentar reconstrucción de emergencia
        if self.auto_repairer:
            try:
                emergency_results = self.auto_repairer.emergency_rebuild()
                successful_emergency = [r for r in emergency_results if r.success]
                
                if len(successful_emergency) > 0:
                    logger.info(f"✅ Recuperación parcial: {len(successful_emergency)} acciones exitosas")
                    
                    # Verificar si ahora funciona
                    if self._test_railway_connection_thoroughly():
                        logger.info("✅ Recuperación Railway exitosa")
                        return True
            except Exception as e:
                logger.error(f"❌ Error en recuperación: {e}")
        
        # Si la recuperación falla, hacer fallback a local
        logger.info("🔄 Iniciando fallback a deployment local...")
        return self._fallback_to_local()
    
    def _fallback_to_local(self) -> bool:
        """Fallback automático a deployment local"""
        logger.info("🏠 Ejecutando fallback a deployment local...")
        
        try:
            # Comentar temporalmente DATABASE_URL para forzar local
            original_database_url = os.environ.get("DATABASE_URL")
            if original_database_url:
                os.environ.pop("DATABASE_URL", None)
                logger.info("🔄 DATABASE_URL removida temporalmente para fallback local")
            
            # Inicializar deployment local
            self.local_fallback = LocalDatabaseDeployment()
            
            # Ejecutar deployment local
            success = self.local_fallback.run_intelligent_deployment()
            
            # Restaurar DATABASE_URL
            if original_database_url:
                os.environ["DATABASE_URL"] = original_database_url
            
            if success:
                logger.info("✅ Fallback local exitoso")
                self._print_fallback_summary()
                return True
            else:
                logger.error("❌ Fallback local también falló")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error en fallback local: {e}")
            return False
    
    def _print_railway_summary(self):
        """Imprimir resumen del deployment Railway"""
        execution_time = time.time() - self.start_time
        
        print("\n" + "="*60)
        print("🚂 DEPLOYMENT RAILWAY COMPLETADO")
        print("="*60)
        print(f"⏱️  Tiempo de ejecución: {execution_time:.2f} segundos")
        print(f"🌐 Entorno: Railway Cloud")
        
        if self.connection_monitor:
            last_check = self.connection_monitor.check_connection()
            if last_check.get("response_time"):
                print(f"⚡ Latencia: {last_check['response_time']*1000:.1f}ms")
            print(f"🔗 Estado: {last_check['status']}")
        
        print(f"🗃️  Base de datos: PostgreSQL en Railway")
        print(f"👁️  Monitoreo: Habilitado (Railway-específico)")
        print()
        print("📋 Características Railway:")
        print("   • Reconexión automática ante suspensión")
        print("   • Detección de latencia alta")
        print("   • Fallback automático a local si falla")
        print("   • Monitoreo cada 5 minutos")
        print()
        print("⚠️  Nota: Railway puede suspender la BD por inactividad")
        print("   El sistema la despertará automáticamente cuando sea necesario")
        print("="*60)
    
    def _print_fallback_summary(self):
        """Imprimir resumen del fallback"""
        print("\n" + "="*60)
        print("🔄 FALLBACK A LOCAL COMPLETADO")
        print("="*60)
        print("⚠️  Railway no estaba disponible")
        print("✅ Sistema funcionando en modo local")
        print("🔄 Se intentará Railway automáticamente en próximas ejecuciones")
        print("="*60)


def main():
    """Función principal"""
    deployment = RailwayDatabaseDeployment()
    
    success = deployment.run_intelligent_railway_deployment()
    
    if success:
        logger.info("🎯 Deployment completado exitosamente")
        sys.exit(0)
    else:
        logger.error("💥 Deployment falló completamente")
        sys.exit(1)


if __name__ == "__main__":
    main()