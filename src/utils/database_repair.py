#!/usr/bin/env python3
"""
Sistema de Autoreparación Automática de Base de Datos
====================================================

Este módulo proporciona funcionalidades para:
- Detección automática de problemas
- Reparación automática de estructura
- Recuperación de datos
- Reconstrucción de índices
- Optimización automática
"""

import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from sqlalchemy import text, inspect
from sqlalchemy.exc import SQLAlchemyError

from .database_health import DatabaseHealthChecker, HealthStatus, CheckCategory


logger = logging.getLogger(__name__)


class RepairAction(Enum):
    """Tipos de acciones de reparación"""
    CREATE_TABLE = "create_table"
    RECREATE_INDEX = "recreate_index"
    LOAD_DATA = "load_data"
    VACUUM_ANALYZE = "vacuum_analyze"
    UPDATE_STATISTICS = "update_statistics"
    REPAIR_STRUCTURE = "repair_structure"
    OPTIMIZE_PERFORMANCE = "optimize_performance"


@dataclass
class RepairResult:
    """Resultado de una acción de reparación"""
    action: RepairAction
    success: bool
    message: str
    details: Dict[str, Any]
    execution_time: float
    timestamp: datetime


class DatabaseAutoRepairer:
    """Sistema de autoreparación automática de base de datos"""
    
    def __init__(self, db_manager, data_loader=None):
        """
        Inicializar el sistema de autoreparación
        
        Args:
            db_manager: Instancia de DatabaseManager
            data_loader: Instancia de DataLoader (opcional)
        """
        self.db_manager = db_manager
        self.data_loader = data_loader
        self.health_checker = DatabaseHealthChecker(db_manager)
        self.repair_results = []
        
        # Rutas de scripts SQL
        self.sql_scripts_path = Path(__file__).parent.parent.parent / "sql"
        
    def auto_repair(self, health_report=None) -> List[RepairResult]:
        """
        Ejecutar autoreparación completa basada en diagnóstico
        
        Args:
            health_report: Reporte de salud existente (opcional)
            
        Returns:
            Lista de resultados de reparación
        """
        logger.info("🔧 Iniciando autoreparación automática...")
        
        self.repair_results = []
        
        # Obtener reporte de salud si no se proporciona
        if health_report is None:
            health_report = self.health_checker.run_full_diagnosis()
        
        # Ejecutar reparaciones basadas en problemas detectados
        for check in health_report.checks:
            if check.status in [HealthStatus.CRITICAL, HealthStatus.WARNING]:
                self._repair_check_issue(check)
        
        # Ejecutar optimizaciones generales si no hay problemas críticos
        critical_issues = [r for r in self.repair_results if not r.success]
        if not critical_issues:
            self._perform_maintenance_tasks()
        
        logger.info(f"✅ Autoreparación completada - {len(self.repair_results)} acciones ejecutadas")
        return self.repair_results
    
    def _repair_check_issue(self, check):
        """Reparar problema específico detectado en un check"""
        if check.category == CheckCategory.CONNECTION:
            self._repair_connection_issues(check)
        elif check.category == CheckCategory.STRUCTURE:
            self._repair_structure_issues(check)
        elif check.category == CheckCategory.DATA:
            self._repair_data_issues(check)
        elif check.category == CheckCategory.PERFORMANCE:
            self._repair_performance_issues(check)
        elif check.category == CheckCategory.MAINTENANCE:
            self._repair_maintenance_issues(check)
    
    def _repair_connection_issues(self, check):
        """Reparar problemas de conexión"""
        if "pool" in check.name.lower():
            # Intentar limpiar pool de conexiones
            result = self._cleanup_connection_pool()
            self.repair_results.append(result)
    
    def _repair_structure_issues(self, check):
        """Reparar problemas de estructura"""
        if "missing_tables" in check.details:
            missing_tables = check.details["missing_tables"]
            for table in missing_tables:
                result = self._create_missing_table(table)
                self.repair_results.append(result)
    
    def _repair_data_issues(self, check):
        """Reparar problemas de datos"""
        if check.details.get("total_records", 0) == 0:
            # Intentar cargar datos
            result = self._reload_data()
            self.repair_results.append(result)
    
    def _repair_performance_issues(self, check):
        """Reparar problemas de rendimiento"""
        # Actualizar estadísticas
        result = self._update_statistics()
        self.repair_results.append(result)
        
        # Vacuum y analyze
        result = self._vacuum_analyze()
        self.repair_results.append(result)
    
    def _repair_maintenance_issues(self, check):
        """Reparar problemas de mantenimiento"""
        # Ejecutar tareas de mantenimiento básico
        result = self._vacuum_analyze()
        self.repair_results.append(result)
    
    def _cleanup_connection_pool(self) -> RepairResult:
        """Limpiar pool de conexiones"""
        start_time = time.time()
        
        try:
            # Disponer del engine actual y recrear
            if hasattr(self.db_manager, 'engine') and self.db_manager.engine:
                self.db_manager.engine.dispose()
            
            # Reconectar
            if self.db_manager.connect():
                return RepairResult(
                    action=RepairAction.REPAIR_STRUCTURE,
                    success=True,
                    message="Pool de conexiones limpiado exitosamente",
                    details={"action": "connection_pool_cleanup"},
                    execution_time=time.time() - start_time,
                    timestamp=datetime.now()
                )
            else:
                return RepairResult(
                    action=RepairAction.REPAIR_STRUCTURE,
                    success=False,
                    message="No se pudo reconectar después de limpiar pool",
                    details={"action": "connection_pool_cleanup"},
                    execution_time=time.time() - start_time,
                    timestamp=datetime.now()
                )
                
        except Exception as e:
            return RepairResult(
                action=RepairAction.REPAIR_STRUCTURE,
                success=False,
                message=f"Error limpiando pool: {str(e)}",
                details={"action": "connection_pool_cleanup", "error": str(e)},
                execution_time=time.time() - start_time,
                timestamp=datetime.now()
            )
    
    def _create_missing_table(self, table_name: str) -> RepairResult:
        """Crear tabla faltante"""
        start_time = time.time()
        
        try:
            # Mapeo de tablas a scripts SQL
            table_script_map = {
                "emp_contratos": "03_create_contratos_table.sql",
                "emp_seguimiento_procesos_dacp": "02_create_procesos_table.sql",
                "emp_proyectos": "01_init_database.sql",  # Tabla incluida en init
                "flujo_caja": "01_init_database.sql"  # Tabla incluida en init
            }
            
            script_name = table_script_map.get(table_name)
            if not script_name:
                return RepairResult(
                    action=RepairAction.CREATE_TABLE,
                    success=False,
                    message=f"No se encontró script para tabla {table_name}",
                    details={"table": table_name},
                    execution_time=time.time() - start_time,
                    timestamp=datetime.now()
                )
            
            script_path = self.sql_scripts_path / script_name
            if not script_path.exists():
                return RepairResult(
                    action=RepairAction.CREATE_TABLE,
                    success=False,
                    message=f"Script no encontrado: {script_path}",
                    details={"table": table_name, "script": str(script_path)},
                    execution_time=time.time() - start_time,
                    timestamp=datetime.now()
                )
            
            # Ejecutar script
            success = self._execute_sql_script(script_path)
            
            return RepairResult(
                action=RepairAction.CREATE_TABLE,
                success=success,
                message=f"Tabla {table_name} {'creada' if success else 'falló al crear'}",
                details={"table": table_name, "script": script_name},
                execution_time=time.time() - start_time,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            return RepairResult(
                action=RepairAction.CREATE_TABLE,
                success=False,
                message=f"Error creando tabla {table_name}: {str(e)}",
                details={"table": table_name, "error": str(e)},
                execution_time=time.time() - start_time,
                timestamp=datetime.now()
            )
    
    def _reload_data(self) -> RepairResult:
        """Recargar datos desde archivos fuente"""
        start_time = time.time()
        
        if not self.data_loader:
            return RepairResult(
                action=RepairAction.LOAD_DATA,
                success=False,
                message="DataLoader no disponible para recarga de datos",
                details={},
                execution_time=time.time() - start_time,
                timestamp=datetime.now()
            )
        
        try:
            # Buscar archivos de datos
            data_files_path = Path(__file__).parent.parent.parent / "app_outputs"
            
            total_loaded = 0
            errors = []
            
            # Cargar contratos
            contratos_file = data_files_path / "emprestito_outputs" / "emp_contratos.json"
            if contratos_file.exists():
                try:
                    loaded, _ = self.data_loader.load_contratos_from_json(contratos_file)
                    total_loaded += loaded
                except Exception as e:
                    errors.append(f"Contratos: {str(e)}")
            
            # Cargar procesos
            procesos_file = data_files_path / "emprestito_outputs" / "emp_procesos.json"
            if procesos_file.exists():
                try:
                    loaded, _ = self.data_loader.load_procesos_from_json(procesos_file)
                    total_loaded += loaded
                except Exception as e:
                    errors.append(f"Procesos: {str(e)}")
            
            success = total_loaded > 0 and len(errors) == 0
            
            return RepairResult(
                action=RepairAction.LOAD_DATA,
                success=success,
                message=f"Datos recargados: {total_loaded} registros, {len(errors)} errores",
                details={"loaded_records": total_loaded, "errors": errors},
                execution_time=time.time() - start_time,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            return RepairResult(
                action=RepairAction.LOAD_DATA,
                success=False,
                message=f"Error recargando datos: {str(e)}",
                details={"error": str(e)},
                execution_time=time.time() - start_time,
                timestamp=datetime.now()
            )
    
    def _update_statistics(self) -> RepairResult:
        """Actualizar estadísticas de la base de datos"""
        start_time = time.time()
        
        try:
            with self.db_manager.get_session() as session:
                # Obtener tablas del usuario
                tables_result = session.execute(text("""
                    SELECT tablename 
                    FROM pg_tables 
                    WHERE schemaname = 'public'
                """)).fetchall()
                
                updated_tables = []
                for row in tables_result:
                    table_name = row[0]
                    try:
                        session.execute(text(f"ANALYZE {table_name}"))
                        updated_tables.append(table_name)
                    except Exception as e:
                        logger.warning(f"Error analizando tabla {table_name}: {e}")
                
                session.commit()
                
                return RepairResult(
                    action=RepairAction.UPDATE_STATISTICS,
                    success=True,
                    message=f"Estadísticas actualizadas para {len(updated_tables)} tablas",
                    details={"updated_tables": updated_tables},
                    execution_time=time.time() - start_time,
                    timestamp=datetime.now()
                )
                
        except Exception as e:
            return RepairResult(
                action=RepairAction.UPDATE_STATISTICS,
                success=False,
                message=f"Error actualizando estadísticas: {str(e)}",
                details={"error": str(e)},
                execution_time=time.time() - start_time,
                timestamp=datetime.now()
            )
    
    def _vacuum_analyze(self) -> RepairResult:
        """Ejecutar VACUUM y ANALYZE en la base de datos"""
        start_time = time.time()
        
        try:
            with self.db_manager.get_session() as session:
                # VACUUM no puede ejecutarse en transacción, usar autocommit
                session.connection().connection.set_isolation_level(0)
                
                # Obtener tablas principales
                main_tables = [
                    "emp_contratos", "emp_seguimiento_procesos_dacp", 
                    "emp_proyectos", "flujo_caja"
                ]
                
                vacuumed_tables = []
                for table in main_tables:
                    try:
                        session.execute(text(f"VACUUM ANALYZE {table}"))
                        vacuumed_tables.append(table)
                    except Exception as e:
                        logger.warning(f"Error en VACUUM de tabla {table}: {e}")
                
                # Restaurar modo de transacción
                session.connection().connection.set_isolation_level(1)
                
                return RepairResult(
                    action=RepairAction.VACUUM_ANALYZE,
                    success=True,
                    message=f"VACUUM ANALYZE ejecutado en {len(vacuumed_tables)} tablas",
                    details={"vacuumed_tables": vacuumed_tables},
                    execution_time=time.time() - start_time,
                    timestamp=datetime.now()
                )
                
        except Exception as e:
            return RepairResult(
                action=RepairAction.VACUUM_ANALYZE,
                success=False,
                message=f"Error ejecutando VACUUM ANALYZE: {str(e)}",
                details={"error": str(e)},
                execution_time=time.time() - start_time,
                timestamp=datetime.now()
            )
    
    def _perform_maintenance_tasks(self):
        """Ejecutar tareas de mantenimiento preventivo"""
        logger.info("🧹 Ejecutando tareas de mantenimiento preventivo...")
        
        # Actualizar estadísticas
        result = self._update_statistics()
        self.repair_results.append(result)
        
        # Optimizar rendimiento si es necesario
        result = self._optimize_performance()
        self.repair_results.append(result)
    
    def _optimize_performance(self) -> RepairResult:
        """Optimizar rendimiento de la base de datos"""
        start_time = time.time()
        
        try:
            optimizations = []
            
            with self.db_manager.get_session() as session:
                # Verificar y crear índices faltantes en columnas importantes
                important_columns = {
                    "emp_contratos": ["numero_contrato", "estado", "fecha_firma"],
                    "emp_seguimiento_procesos_dacp": ["numero_proceso", "estado"],
                    "emp_proyectos": ["codigo_proyecto", "estado"]
                }
                
                for table, columns in important_columns.items():
                    try:
                        # Verificar si la tabla existe
                        table_exists = session.execute(text(f"""
                            SELECT EXISTS (
                                SELECT FROM information_schema.tables 
                                WHERE table_name = '{table}'
                            )
                        """)).scalar()
                        
                        if table_exists:
                            for column in columns:
                                try:
                                    # Verificar si el índice ya existe
                                    index_exists = session.execute(text(f"""
                                        SELECT EXISTS (
                                            SELECT FROM pg_indexes 
                                            WHERE tablename = '{table}' 
                                            AND indexname LIKE '%{column}%'
                                        )
                                    """)).scalar()
                                    
                                    if not index_exists:
                                        # Crear índice
                                        index_name = f"idx_{table}_{column}"
                                        session.execute(text(f"CREATE INDEX CONCURRENTLY IF NOT EXISTS {index_name} ON {table} ({column})"))
                                        optimizations.append(f"Índice creado: {index_name}")
                                        
                                except Exception as e:
                                    logger.warning(f"Error creando índice en {table}.{column}: {e}")
                    
                    except Exception as e:
                        logger.warning(f"Error optimizando tabla {table}: {e}")
                
                session.commit()
            
            return RepairResult(
                action=RepairAction.OPTIMIZE_PERFORMANCE,
                success=True,
                message=f"Optimizaciones aplicadas: {len(optimizations)}",
                details={"optimizations": optimizations},
                execution_time=time.time() - start_time,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            return RepairResult(
                action=RepairAction.OPTIMIZE_PERFORMANCE,
                success=False,
                message=f"Error optimizando rendimiento: {str(e)}",
                details={"error": str(e)},
                execution_time=time.time() - start_time,
                timestamp=datetime.now()
            )
    
    def _execute_sql_script(self, script_path: Path) -> bool:
        """Ejecutar script SQL desde archivo"""
        try:
            with open(script_path, 'r', encoding='utf-8') as f:
                sql_content = f.read()
            
            with self.db_manager.get_session() as session:
                # Dividir en statements individuales
                statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
                
                for statement in statements:
                    try:
                        session.execute(text(statement))
                    except Exception as e:
                        # Log pero continuar con otros statements
                        logger.warning(f"Error ejecutando statement: {e}")
                
                session.commit()
            
            return True
            
        except Exception as e:
            logger.error(f"Error ejecutando script {script_path}: {e}")
            return False
    
    def emergency_rebuild(self) -> List[RepairResult]:
        """Reconstrucción de emergencia completa"""
        logger.warning("🚨 Iniciando reconstrucción de emergencia...")
        
        self.repair_results = []
        
        # 1. Intentar reconectar
        if not self.db_manager.test_connection():
            result = self._cleanup_connection_pool()
            self.repair_results.append(result)
        
        # 2. Recrear estructura básica
        result = self._recreate_basic_structure()
        self.repair_results.append(result)
        
        # 3. Recargar datos críticos
        if self.data_loader:
            result = self._reload_data()
            self.repair_results.append(result)
        
        # 4. Optimizar
        result = self._vacuum_analyze()
        self.repair_results.append(result)
        
        logger.info("✅ Reconstrucción de emergencia completada")
        return self.repair_results
    
    def _recreate_basic_structure(self) -> RepairResult:
        """Recrear estructura básica de la base de datos"""
        start_time = time.time()
        
        try:
            sql_scripts = [
                "01_init_database.sql",
                "02_create_procesos_table.sql",
                "03_create_contratos_table.sql"
            ]
            
            executed_scripts = []
            failed_scripts = []
            
            for script_name in sql_scripts:
                script_path = self.sql_scripts_path / script_name
                if script_path.exists():
                    if self._execute_sql_script(script_path):
                        executed_scripts.append(script_name)
                    else:
                        failed_scripts.append(script_name)
                else:
                    failed_scripts.append(f"{script_name} (no encontrado)")
            
            success = len(executed_scripts) > 0 and len(failed_scripts) == 0
            
            return RepairResult(
                action=RepairAction.REPAIR_STRUCTURE,
                success=success,
                message=f"Estructura recreada: {len(executed_scripts)} scripts ejecutados, {len(failed_scripts)} fallos",
                details={
                    "executed_scripts": executed_scripts,
                    "failed_scripts": failed_scripts
                },
                execution_time=time.time() - start_time,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            return RepairResult(
                action=RepairAction.REPAIR_STRUCTURE,
                success=False,
                message=f"Error recreando estructura: {str(e)}",
                details={"error": str(e)},
                execution_time=time.time() - start_time,
                timestamp=datetime.now()
            )