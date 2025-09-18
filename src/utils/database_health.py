#!/usr/bin/env python3
"""
Sistema de Autodiagnóstico y Salud de Base de Datos
==================================================

Este módulo proporciona funcionalidades completas para:
- Diagnóstico automático de la base de datos
- Verificación de integridad
- Detección de problemas
- Métricas de rendimiento
- Recomendaciones de optimización
"""

import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import json

from sqlalchemy import text, inspect
from sqlalchemy.exc import SQLAlchemyError


logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Estados de salud de la base de datos"""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


class CheckCategory(Enum):
    """Categorías de verificaciones"""
    CONNECTION = "connection"
    STRUCTURE = "structure"
    DATA = "data"
    PERFORMANCE = "performance"
    SECURITY = "security"
    MAINTENANCE = "maintenance"


@dataclass
class HealthCheck:
    """Resultado de una verificación individual"""
    name: str
    category: CheckCategory
    status: HealthStatus
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    execution_time: float = 0.0


@dataclass
class DatabaseHealthReport:
    """Reporte completo de salud de la base de datos"""
    overall_status: HealthStatus
    checks: List[HealthCheck]
    timestamp: datetime
    database_info: Dict[str, Any]
    summary: Dict[str, int]
    recommendations: List[str]
    execution_time: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir el reporte a diccionario para serialización"""
        return {
            "overall_status": self.overall_status.value,
            "timestamp": self.timestamp.isoformat(),
            "execution_time": self.execution_time,
            "database_info": self.database_info,
            "summary": self.summary,
            "recommendations": self.recommendations,
            "checks": [
                {
                    "name": check.name,
                    "category": check.category.value,
                    "status": check.status.value,
                    "message": check.message,
                    "details": check.details,
                    "recommendations": check.recommendations,
                    "timestamp": check.timestamp.isoformat(),
                    "execution_time": check.execution_time
                }
                for check in self.checks
            ]
        }


class DatabaseHealthChecker:
    """Sistema de verificación de salud de base de datos"""
    
    def __init__(self, db_manager):
        """
        Inicializar el verificador de salud
        
        Args:
            db_manager: Instancia de DatabaseManager
        """
        self.db_manager = db_manager
        self.checks = []
        
    def run_full_diagnosis(self) -> DatabaseHealthReport:
        """Ejecutar diagnóstico completo de la base de datos"""
        start_time = time.time()
        logger.info("🔍 Iniciando diagnóstico completo de base de datos...")
        
        self.checks = []
        
        # Ejecutar todas las verificaciones
        self._check_connection()
        self._check_database_structure()
        self._check_data_integrity()
        self._check_performance()
        self._check_security()
        self._check_maintenance()
        
        # Calcular estado general
        overall_status = self._calculate_overall_status()
        
        # Obtener información de la base de datos
        db_info = self._get_database_info()
        
        # Generar resumen
        summary = self._generate_summary()
        
        # Generar recomendaciones generales
        recommendations = self._generate_recommendations()
        
        execution_time = time.time() - start_time
        
        report = DatabaseHealthReport(
            overall_status=overall_status,
            checks=self.checks,
            timestamp=datetime.now(),
            database_info=db_info,
            summary=summary,
            recommendations=recommendations,
            execution_time=execution_time
        )
        
        logger.info(f"✅ Diagnóstico completado en {execution_time:.2f}s - Estado: {overall_status.value}")
        return report
    
    def _check_connection(self):
        """Verificar conectividad de la base de datos"""
        start_time = time.time()
        
        try:
            if self.db_manager.test_connection():
                self._add_check(
                    "connection_basic",
                    CheckCategory.CONNECTION,
                    HealthStatus.HEALTHY,
                    "Conexión a base de datos exitosa",
                    execution_time=time.time() - start_time
                )
            else:
                self._add_check(
                    "connection_basic",
                    CheckCategory.CONNECTION,
                    HealthStatus.CRITICAL,
                    "No se puede conectar a la base de datos",
                    recommendations=["Verificar configuración de conexión", "Comprobar que PostgreSQL esté ejecutándose"],
                    execution_time=time.time() - start_time
                )
                return
                
        except Exception as e:
            self._add_check(
                "connection_basic",
                CheckCategory.CONNECTION,
                HealthStatus.CRITICAL,
                f"Error de conexión: {str(e)}",
                execution_time=time.time() - start_time
            )
            return
        
        # Verificar pool de conexiones
        self._check_connection_pool()
        
        # Verificar latencia
        self._check_connection_latency()
    
    def _check_connection_pool(self):
        """Verificar estado del pool de conexiones"""
        start_time = time.time()
        
        try:
            with self.db_manager.get_session() as session:
                # Verificar configuración del pool
                if hasattr(self.db_manager.engine.pool, 'size'):
                    pool_size = self.db_manager.engine.pool.size()
                    checked_in = self.db_manager.engine.pool.checkedin()
                    checked_out = self.db_manager.engine.pool.checkedout()
                    
                    details = {
                        "pool_size": pool_size,
                        "checked_in": checked_in,
                        "checked_out": checked_out,
                        "utilization": (checked_out / pool_size * 100) if pool_size > 0 else 0
                    }
                    
                    if details["utilization"] > 80:
                        status = HealthStatus.WARNING
                        message = f"Alta utilización del pool de conexiones: {details['utilization']:.1f}%"
                        recommendations = ["Considerar aumentar el tamaño del pool", "Verificar conexiones no cerradas"]
                    else:
                        status = HealthStatus.HEALTHY
                        message = f"Pool de conexiones saludable: {details['utilization']:.1f}% utilización"
                        recommendations = []
                    
                    self._add_check(
                        "connection_pool",
                        CheckCategory.CONNECTION,
                        status,
                        message,
                        details=details,
                        recommendations=recommendations,
                        execution_time=time.time() - start_time
                    )
                else:
                    self._add_check(
                        "connection_pool",
                        CheckCategory.CONNECTION,
                        HealthStatus.UNKNOWN,
                        "Información del pool no disponible",
                        execution_time=time.time() - start_time
                    )
                    
        except Exception as e:
            self._add_check(
                "connection_pool",
                CheckCategory.CONNECTION,
                HealthStatus.WARNING,
                f"Error verificando pool: {str(e)}",
                execution_time=time.time() - start_time
            )
    
    def _check_connection_latency(self):
        """Verificar latencia de conexión"""
        start_time = time.time()
        
        try:
            with self.db_manager.get_session() as session:
                # Medir tiempo de respuesta
                query_start = time.time()
                session.execute(text("SELECT 1"))
                query_time = (time.time() - query_start) * 1000  # en ms
                
                details = {"latency_ms": query_time}
                
                if query_time > 1000:  # > 1 segundo
                    status = HealthStatus.CRITICAL
                    message = f"Latencia crítica: {query_time:.1f}ms"
                    recommendations = ["Verificar red y conectividad", "Comprobar carga del servidor"]
                elif query_time > 100:  # > 100ms
                    status = HealthStatus.WARNING
                    message = f"Latencia alta: {query_time:.1f}ms"
                    recommendations = ["Monitorear rendimiento de red"]
                else:
                    status = HealthStatus.HEALTHY
                    message = f"Latencia normal: {query_time:.1f}ms"
                    recommendations = []
                
                self._add_check(
                    "connection_latency",
                    CheckCategory.CONNECTION,
                    status,
                    message,
                    details=details,
                    recommendations=recommendations,
                    execution_time=time.time() - start_time
                )
                
        except Exception as e:
            self._add_check(
                "connection_latency",
                CheckCategory.CONNECTION,
                HealthStatus.WARNING,
                f"Error midiendo latencia: {str(e)}",
                execution_time=time.time() - start_time
            )
    
    def _check_database_structure(self):
        """Verificar estructura de la base de datos"""
        start_time = time.time()
        
        try:
            with self.db_manager.get_session() as session:
                inspector = inspect(self.db_manager.engine)
                
                # Verificar tablas esperadas
                expected_tables = [
                    'emp_contratos', 'emp_seguimiento_procesos_dacp', 
                    'emp_proyectos', 'flujo_caja',
                    'unidad_proyecto_infraestructura_equipamientos',
                    'unidad_proyecto_infraestructura_vial'
                ]
                
                existing_tables = inspector.get_table_names()
                missing_tables = [t for t in expected_tables if t not in existing_tables]
                extra_tables = [t for t in existing_tables if t not in expected_tables and not t.startswith('spatial_ref_sys')]
                
                details = {
                    "expected_tables": len(expected_tables),
                    "existing_tables": len(existing_tables),
                    "missing_tables": missing_tables,
                    "extra_tables": extra_tables
                }
                
                if missing_tables:
                    status = HealthStatus.CRITICAL
                    message = f"Faltan {len(missing_tables)} tablas críticas"
                    recommendations = [
                        "Ejecutar scripts de creación de tablas",
                        "Verificar proceso de inicialización de BD"
                    ]
                elif extra_tables:
                    status = HealthStatus.WARNING
                    message = f"Se encontraron {len(extra_tables)} tablas no esperadas"
                    recommendations = ["Revisar tablas adicionales para determinar si son necesarias"]
                else:
                    status = HealthStatus.HEALTHY
                    message = "Estructura de tablas correcta"
                    recommendations = []
                
                self._add_check(
                    "database_structure",
                    CheckCategory.STRUCTURE,
                    status,
                    message,
                    details=details,
                    recommendations=recommendations,
                    execution_time=time.time() - start_time
                )
                
        except Exception as e:
            self._add_check(
                "database_structure",
                CheckCategory.STRUCTURE,
                HealthStatus.CRITICAL,
                f"Error verificando estructura: {str(e)}",
                execution_time=time.time() - start_time
            )
    
    def _check_data_integrity(self):
        """Verificar integridad de los datos"""
        start_time = time.time()
        
        try:
            with self.db_manager.get_session() as session:
                total_records = 0
                table_counts = {}
                
                tables_to_check = [
                    'emp_contratos', 'emp_seguimiento_procesos_dacp', 
                    'emp_proyectos', 'flujo_caja'
                ]
                
                for table in tables_to_check:
                    try:
                        result = session.execute(text(f"SELECT COUNT(*) FROM {table}")).fetchone()
                        count = result[0] if result else 0
                        table_counts[table] = count
                        total_records += count
                    except Exception:
                        table_counts[table] = "ERROR"
                
                # Verificar que hay datos
                if total_records == 0:
                    status = HealthStatus.CRITICAL
                    message = "No hay datos en ninguna tabla"
                    recommendations = ["Ejecutar proceso de carga de datos", "Verificar archivos fuente"]
                elif total_records < 100:
                    status = HealthStatus.WARNING
                    message = f"Pocos registros: {total_records}"
                    recommendations = ["Verificar completitud de la carga de datos"]
                else:
                    status = HealthStatus.HEALTHY
                    message = f"Datos presentes: {total_records:,} registros totales"
                    recommendations = []
                
                details = {
                    "total_records": total_records,
                    "table_counts": table_counts
                }
                
                self._add_check(
                    "data_integrity",
                    CheckCategory.DATA,
                    status,
                    message,
                    details=details,
                    recommendations=recommendations,
                    execution_time=time.time() - start_time
                )
                
        except Exception as e:
            self._add_check(
                "data_integrity",
                CheckCategory.DATA,
                HealthStatus.CRITICAL,
                f"Error verificando integridad: {str(e)}",
                execution_time=time.time() - start_time
            )
    
    def _check_performance(self):
        """Verificar rendimiento de la base de datos"""
        start_time = time.time()
        
        try:
            with self.db_manager.get_session() as session:
                # Verificar índices
                inspector = inspect(self.db_manager.engine)
                tables = inspector.get_table_names()
                
                indexes_info = {}
                for table in tables[:5]:  # Limitar a las primeras 5 tablas
                    try:
                        indexes = inspector.get_indexes(table)
                        indexes_info[table] = len(indexes)
                    except Exception:
                        indexes_info[table] = "ERROR"
                
                # Verificar estadísticas de PostgreSQL si está disponible
                try:
                    stats_result = session.execute(text("""
                        SELECT 
                            schemaname,
                            tablename,
                            n_tup_ins + n_tup_upd + n_tup_del as total_changes,
                            n_tup_ins,
                            n_tup_upd,
                            n_tup_del
                        FROM pg_stat_user_tables 
                        ORDER BY total_changes DESC 
                        LIMIT 5
                    """)).fetchall()
                    
                    table_stats = [
                        {
                            "table": f"{row[0]}.{row[1]}",
                            "total_changes": row[2],
                            "inserts": row[3],
                            "updates": row[4],
                            "deletes": row[5]
                        }
                        for row in stats_result
                    ]
                except Exception:
                    table_stats = []
                
                details = {
                    "indexes_per_table": indexes_info,
                    "table_statistics": table_stats
                }
                
                # Evaluar rendimiento
                avg_indexes = sum(v for v in indexes_info.values() if isinstance(v, int)) / len(indexes_info) if indexes_info else 0
                
                if avg_indexes < 1:
                    status = HealthStatus.WARNING
                    message = "Pocos índices detectados, rendimiento puede verse afectado"
                    recommendations = ["Revisar necesidad de índices en tablas principales"]
                else:
                    status = HealthStatus.HEALTHY
                    message = f"Rendimiento normal - {avg_indexes:.1f} índices promedio por tabla"
                    recommendations = []
                
                self._add_check(
                    "performance",
                    CheckCategory.PERFORMANCE,
                    status,
                    message,
                    details=details,
                    recommendations=recommendations,
                    execution_time=time.time() - start_time
                )
                
        except Exception as e:
            self._add_check(
                "performance",
                CheckCategory.PERFORMANCE,
                HealthStatus.WARNING,
                f"Error verificando rendimiento: {str(e)}",
                execution_time=time.time() - start_time
            )
    
    def _check_security(self):
        """Verificar aspectos de seguridad"""
        start_time = time.time()
        
        try:
            with self.db_manager.get_session() as session:
                # Verificar extensiones de seguridad
                extensions_result = session.execute(text("SELECT extname FROM pg_extension")).fetchall()
                extensions = [row[0] for row in extensions_result]
                
                # Verificar usuarios y roles
                users_result = session.execute(text("SELECT rolname, rolsuper FROM pg_roles")).fetchall()
                users_info = [{"name": row[0], "is_superuser": row[1]} for row in users_result]
                
                details = {
                    "extensions": extensions,
                    "user_count": len(users_info),
                    "superuser_count": sum(1 for u in users_info if u["is_superuser"])
                }
                
                # Evaluar seguridad básica
                if "postgis" in extensions:
                    message = "PostGIS disponible, extensiones básicas presentes"
                    status = HealthStatus.HEALTHY
                    recommendations = []
                else:
                    message = "PostGIS no detectado"
                    status = HealthStatus.WARNING
                    recommendations = ["Instalar PostGIS si se requiere funcionalidad geoespacial"]
                
                self._add_check(
                    "security",
                    CheckCategory.SECURITY,
                    status,
                    message,
                    details=details,
                    recommendations=recommendations,
                    execution_time=time.time() - start_time
                )
                
        except Exception as e:
            self._add_check(
                "security",
                CheckCategory.SECURITY,
                HealthStatus.WARNING,
                f"Error verificando seguridad: {str(e)}",
                execution_time=time.time() - start_time
            )
    
    def _check_maintenance(self):
        """Verificar aspectos de mantenimiento"""
        start_time = time.time()
        
        try:
            with self.db_manager.get_session() as session:
                # Verificar versión de PostgreSQL
                version_result = session.execute(text("SELECT version()")).fetchone()
                version_info = version_result[0] if version_result else "Desconocida"
                
                # Verificar tamaño de la base de datos
                try:
                    size_result = session.execute(text("""
                        SELECT pg_size_pretty(pg_database_size(current_database()))
                    """)).fetchone()
                    db_size = size_result[0] if size_result else "Desconocido"
                except Exception:
                    db_size = "No disponible"
                
                details = {
                    "postgresql_version": version_info,
                    "database_size": db_size
                }
                
                # Evaluación básica
                if "PostgreSQL" in version_info:
                    status = HealthStatus.HEALTHY
                    message = f"PostgreSQL funcionando - Tamaño: {db_size}"
                    recommendations = ["Realizar mantenimiento rutinario periódicamente"]
                else:
                    status = HealthStatus.WARNING
                    message = "Información de versión no estándar"
                    recommendations = ["Verificar instalación de PostgreSQL"]
                
                self._add_check(
                    "maintenance",
                    CheckCategory.MAINTENANCE,
                    status,
                    message,
                    details=details,
                    recommendations=recommendations,
                    execution_time=time.time() - start_time
                )
                
        except Exception as e:
            self._add_check(
                "maintenance",
                CheckCategory.MAINTENANCE,
                HealthStatus.WARNING,
                f"Error verificando mantenimiento: {str(e)}",
                execution_time=time.time() - start_time
            )
    
    def _add_check(self, name: str, category: CheckCategory, status: HealthStatus, 
                   message: str, details: Dict[str, Any] = None, 
                   recommendations: List[str] = None, execution_time: float = 0.0):
        """Agregar un resultado de verificación"""
        check = HealthCheck(
            name=name,
            category=category,
            status=status,
            message=message,
            details=details or {},
            recommendations=recommendations or [],
            execution_time=execution_time
        )
        self.checks.append(check)
    
    def _calculate_overall_status(self) -> HealthStatus:
        """Calcular el estado general basado en todas las verificaciones"""
        if not self.checks:
            return HealthStatus.UNKNOWN
        
        critical_count = sum(1 for check in self.checks if check.status == HealthStatus.CRITICAL)
        warning_count = sum(1 for check in self.checks if check.status == HealthStatus.WARNING)
        
        if critical_count > 0:
            return HealthStatus.CRITICAL
        elif warning_count > 0:
            return HealthStatus.WARNING
        else:
            return HealthStatus.HEALTHY
    
    def _get_database_info(self) -> Dict[str, Any]:
        """Obtener información general de la base de datos"""
        try:
            with self.db_manager.get_session() as session:
                # Información básica
                version_result = session.execute(text("SELECT version()")).fetchone()
                current_db_result = session.execute(text("SELECT current_database()")).fetchone()
                
                return {
                    "version": version_result[0] if version_result else "Desconocida",
                    "current_database": current_db_result[0] if current_db_result else "Desconocida",
                    "engine": str(self.db_manager.engine.url).split("://")[0] if self.db_manager.engine else "Desconocido"
                }
        except Exception as e:
            return {"error": str(e)}
    
    def _generate_summary(self) -> Dict[str, int]:
        """Generar resumen de verificaciones"""
        summary = {
            "total_checks": len(self.checks),
            "healthy": sum(1 for check in self.checks if check.status == HealthStatus.HEALTHY),
            "warning": sum(1 for check in self.checks if check.status == HealthStatus.WARNING),
            "critical": sum(1 for check in self.checks if check.status == HealthStatus.CRITICAL),
            "unknown": sum(1 for check in self.checks if check.status == HealthStatus.UNKNOWN)
        }
        return summary
    
    def _generate_recommendations(self) -> List[str]:
        """Generar recomendaciones generales basadas en todos los checks"""
        all_recommendations = []
        
        for check in self.checks:
            all_recommendations.extend(check.recommendations)
        
        # Remover duplicados manteniendo orden
        seen = set()
        unique_recommendations = []
        for rec in all_recommendations:
            if rec not in seen:
                seen.add(rec)
                unique_recommendations.append(rec)
        
        return unique_recommendations[:10]  # Limitar a las 10 más importantes