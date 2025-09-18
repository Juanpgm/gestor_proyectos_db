#!/usr/bin/env python3
"""
Sistema de Creación Automática de Esquemas
==========================================

Este módulo proporciona:
- Creación automática de tablas faltantes
- Verificación de estructura de base de datos
- Creación de índices y restricciones
- Inicialización completa del esquema
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging

# Agregar el directorio src al path
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    from src.database.connection import DatabaseManager
except ImportError as e:
    print(f"Error importando módulos: {e}")
    sys.exit(1)


class SchemaManager:
    """Gestor de esquemas y creación automática de tablas"""
    
    def __init__(self, db_manager: DatabaseManager):
        """
        Inicializar el gestor de esquemas
        
        Args:
            db_manager: Manager de base de datos
        """
        self.db_manager = db_manager
        self.logger = logging.getLogger(__name__)
        
        # Definición del esquema completo
        self.schema_definition = self._get_schema_definition()
    
    def _get_schema_definition(self) -> Dict[str, Any]:
        """Obtener definición completa del esquema"""
        return {
            "tables": {
                "emp_contratos": {
                    "sql": """
                    CREATE TABLE IF NOT EXISTS emp_contratos (
                        id SERIAL PRIMARY KEY,
                        numero_contrato VARCHAR(100) UNIQUE,
                        numero_proceso VARCHAR(100),
                        entidad VARCHAR(200),
                        proveedor_adjudicado VARCHAR(200),
                        valor_del_contrato DECIMAL(15,2),
                        plazo_ejecucion VARCHAR(100),
                        fecha_suscripcion DATE,
                        fecha_inicio_ejecucion DATE,
                        fecha_fin_ejecucion DATE,
                        estado_contrato VARCHAR(50),
                        objeto_contrato TEXT,
                        tipo_contrato VARCHAR(100),
                        modalidad_contratacion VARCHAR(100),
                        justificacion_modalidad TEXT,
                        codigo_entidad VARCHAR(50),
                        nombre_entidad VARCHAR(200),
                        orden_territorial VARCHAR(100),
                        municipio VARCHAR(100),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                    """,
                    "indexes": [
                        "CREATE INDEX IF NOT EXISTS idx_emp_contratos_numero ON emp_contratos(numero_contrato);",
                        "CREATE INDEX IF NOT EXISTS idx_emp_contratos_proceso ON emp_contratos(numero_proceso);",
                        "CREATE INDEX IF NOT EXISTS idx_emp_contratos_entidad ON emp_contratos(entidad);",
                        "CREATE INDEX IF NOT EXISTS idx_emp_contratos_proveedor ON emp_contratos(proveedor_adjudicado);",
                        "CREATE INDEX IF NOT EXISTS idx_emp_contratos_estado ON emp_contratos(estado_contrato);",
                        "CREATE INDEX IF NOT EXISTS idx_emp_contratos_fecha_suscripcion ON emp_contratos(fecha_suscripcion);"
                    ]
                },
                "system_health": {
                    "sql": """
                    CREATE TABLE IF NOT EXISTS system_health (
                        id SERIAL PRIMARY KEY,
                        check_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        overall_status VARCHAR(20),
                        connection_status VARCHAR(20),
                        structure_status VARCHAR(20),
                        data_status VARCHAR(20),
                        performance_status VARCHAR(20),
                        response_time_ms INTEGER,
                        details JSONB,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                    """,
                    "indexes": [
                        "CREATE INDEX IF NOT EXISTS idx_system_health_timestamp ON system_health(check_timestamp);",
                        "CREATE INDEX IF NOT EXISTS idx_system_health_status ON system_health(overall_status);",
                        "CREATE INDEX IF NOT EXISTS idx_system_health_details ON system_health USING GIN (details);"
                    ]
                },
                "system_alerts": {
                    "sql": """
                    CREATE TABLE IF NOT EXISTS system_alerts (
                        id SERIAL PRIMARY KEY,
                        alert_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        alert_level VARCHAR(20),
                        alert_title VARCHAR(200),
                        alert_message TEXT,
                        alert_details JSONB,
                        resolved BOOLEAN DEFAULT FALSE,
                        resolution_timestamp TIMESTAMP,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                    """,
                    "indexes": [
                        "CREATE INDEX IF NOT EXISTS idx_system_alerts_timestamp ON system_alerts(alert_timestamp);",
                        "CREATE INDEX IF NOT EXISTS idx_system_alerts_level ON system_alerts(alert_level);",
                        "CREATE INDEX IF NOT EXISTS idx_system_alerts_resolved ON system_alerts(resolved);",
                        "CREATE INDEX IF NOT EXISTS idx_system_alerts_details ON system_alerts USING GIN (alert_details);"
                    ]
                }
            },
            "triggers": [
                """
                CREATE OR REPLACE FUNCTION update_updated_at_column()
                RETURNS TRIGGER AS $$
                BEGIN
                    NEW.updated_at = CURRENT_TIMESTAMP;
                    RETURN NEW;
                END;
                $$ language 'plpgsql';
                """,
                """
                DROP TRIGGER IF EXISTS update_emp_procesos_updated_at ON emp_procesos;
                CREATE TRIGGER update_emp_procesos_updated_at
                    BEFORE UPDATE ON emp_procesos
                    FOR EACH ROW
                    EXECUTE FUNCTION update_updated_at_column();
                """,
                """
                DROP TRIGGER IF EXISTS update_emp_contratos_updated_at ON emp_contratos;
                CREATE TRIGGER update_emp_contratos_updated_at
                    BEFORE UPDATE ON emp_contratos
                    FOR EACH ROW
                    EXECUTE FUNCTION update_updated_at_column();
                """
            ],
            "views": [
                """
                CREATE OR REPLACE VIEW v_procesos_resumen AS
                SELECT 
                    banco,
                    COUNT(*) as total_procesos,
                    SUM(valor_total) as valor_total_procesos,
                    AVG(valor_total) as valor_promedio,
                    COUNT(CASE WHEN estado_proceso = 'Adjudicado' THEN 1 END) as procesos_adjudicados
                FROM emp_procesos
                GROUP BY banco;
                """,
                """
                CREATE OR REPLACE VIEW v_contratos_resumen AS
                SELECT 
                    entidad,
                    COUNT(*) as total_contratos,
                    SUM(valor_del_contrato) as valor_total_contratos,
                    AVG(valor_del_contrato) as valor_promedio_contrato,
                    COUNT(CASE WHEN estado_contrato = 'Liquidado' THEN 1 END) as contratos_liquidados
                FROM emp_contratos
                GROUP BY entidad;
                """,
                """
                CREATE OR REPLACE VIEW v_system_health_summary AS
                SELECT 
                    DATE(check_timestamp) as check_date,
                    COUNT(*) as total_checks,
                    COUNT(CASE WHEN overall_status = 'HEALTHY' THEN 1 END) as healthy_checks,
                    COUNT(CASE WHEN overall_status = 'WARNING' THEN 1 END) as warning_checks,
                    COUNT(CASE WHEN overall_status = 'CRITICAL' THEN 1 END) as critical_checks,
                    AVG(response_time_ms) as avg_response_time
                FROM system_health
                GROUP BY DATE(check_timestamp)
                ORDER BY check_date DESC;
                """
            ]
        }
    
    def check_and_create_schema(self) -> Dict[str, Any]:
        """
        Verificar y crear esquema completo
        
        Returns:
            Dict con resultados de la creación
        """
        results = {
            "tables_created": [],
            "tables_existed": [],
            "indexes_created": [],
            "triggers_created": [],
            "views_created": [],
            "errors": []
        }
        
        self.logger.info("🔍 Verificando esquema de base de datos...")
        
        try:
            # Verificar extensiones necesarias
            self._ensure_extensions()
            
            # Crear tablas
            self._create_tables(results)
            
            # Crear triggers
            self._create_triggers(results)
            
            # Crear vistas
            self._create_views(results)
            
            self.logger.info("✅ Verificación de esquema completada")
            
        except Exception as e:
            error_msg = f"Error verificando esquema: {e}"
            self.logger.error(error_msg)
            results["errors"].append(error_msg)
        
        return results
    
    def _ensure_extensions(self):
        """Asegurar que las extensiones necesarias estén instaladas"""
        extensions = ["postgis"]  # Agregar más si es necesario
        
        try:
            with self.db_manager.get_connection() as conn:
                with conn.cursor() as cursor:
                    for ext in extensions:
                        try:
                            cursor.execute(f"CREATE EXTENSION IF NOT EXISTS {ext};")
                            self.logger.info(f"✅ Extensión {ext} verificada")
                        except Exception as e:
                            # PostGIS puede no estar disponible, no es crítico
                            self.logger.warning(f"⚠️ No se pudo crear extensión {ext}: {e}")
                    
                    conn.commit()
        except Exception as e:
            self.logger.warning(f"⚠️ Error verificando extensiones: {e}")
    
    def _create_tables(self, results: Dict[str, Any]):
        """Crear tablas del esquema"""
        tables = self.schema_definition["tables"]
        
        with self.db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                for table_name, table_def in tables.items():
                    try:
                        # Verificar si la tabla existe
                        cursor.execute("""
                            SELECT EXISTS (
                                SELECT FROM information_schema.tables 
                                WHERE table_name = %s
                            );
                        """, (table_name,))
                        
                        table_exists = cursor.fetchone()[0]
                        
                        if not table_exists:
                            # Crear tabla
                            cursor.execute(table_def["sql"])
                            results["tables_created"].append(table_name)
                            self.logger.info(f"✅ Tabla {table_name} creada")
                            
                            # Crear índices
                            for index_sql in table_def.get("indexes", []):
                                cursor.execute(index_sql)
                                results["indexes_created"].append(f"{table_name}_index")
                            
                        else:
                            results["tables_existed"].append(table_name)
                            self.logger.info(f"ℹ️ Tabla {table_name} ya existe")
                            
                            # Crear índices faltantes (por si acaso)
                            for index_sql in table_def.get("indexes", []):
                                try:
                                    cursor.execute(index_sql)
                                except Exception:
                                    pass  # Índice ya existe
                    
                    except Exception as e:
                        error_msg = f"Error creando tabla {table_name}: {e}"
                        self.logger.error(error_msg)
                        results["errors"].append(error_msg)
                
                conn.commit()
    
    def _create_triggers(self, results: Dict[str, Any]):
        """Crear triggers del esquema"""
        triggers = self.schema_definition["triggers"]
        
        with self.db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                for trigger_sql in triggers:
                    try:
                        cursor.execute(trigger_sql)
                        results["triggers_created"].append("trigger")
                        self.logger.info("✅ Trigger creado")
                    except Exception as e:
                        error_msg = f"Error creando trigger: {e}"
                        self.logger.warning(error_msg)
                        # Los triggers no son críticos
                
                conn.commit()
    
    def _create_views(self, results: Dict[str, Any]):
        """Crear vistas del esquema"""
        views = self.schema_definition["views"]
        
        with self.db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                for view_sql in views:
                    try:
                        cursor.execute(view_sql)
                        results["views_created"].append("view")
                        self.logger.info("✅ Vista creada")
                    except Exception as e:
                        error_msg = f"Error creando vista: {e}"
                        self.logger.warning(error_msg)
                        # Las vistas no son críticas
                
                conn.commit()
    
    def verify_schema_integrity(self) -> Dict[str, Any]:
        """
        Verificar integridad del esquema
        
        Returns:
            Dict con estado de la verificación
        """
        integrity_report = {
            "tables_status": {},
            "missing_tables": [],
            "missing_indexes": [],
            "overall_status": "HEALTHY"
        }
        
        try:
            with self.db_manager.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    # Verificar tablas existentes
                    expected_tables = list(self.schema_definition["tables"].keys())
                    
                    cursor.execute("""
                        SELECT table_name 
                        FROM information_schema.tables 
                        WHERE table_schema = 'public'
                        AND table_name = ANY(%s)
                    """, (expected_tables,))
                    
                    existing_tables = [row["table_name"] for row in cursor.fetchall()]
                    
                    for table in expected_tables:
                        if table in existing_tables:
                            integrity_report["tables_status"][table] = "EXISTS"
                        else:
                            integrity_report["tables_status"][table] = "MISSING"
                            integrity_report["missing_tables"].append(table)
                    
                    # Si hay tablas faltantes, el estado es WARNING
                    if integrity_report["missing_tables"]:
                        integrity_report["overall_status"] = "WARNING"
                    
        except Exception as e:
            self.logger.error(f"Error verificando integridad: {e}")
            integrity_report["overall_status"] = "CRITICAL"
            integrity_report["error"] = str(e)
        
        return integrity_report
    
    def get_table_statistics(self) -> Dict[str, Any]:
        """
        Obtener estadísticas de las tablas
        
        Returns:
            Dict con estadísticas de cada tabla
        """
        stats = {}
        
        try:
            with self.db_manager.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    tables = ["emp_procesos", "emp_contratos", "system_health", "system_alerts"]
                    
                    for table in tables:
                        try:
                            # Contar registros
                            cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
                            count = cursor.fetchone()["count"]
                            
                            # Obtener tamaño de tabla
                            cursor.execute("""
                                SELECT pg_size_pretty(pg_total_relation_size(%s)) as size
                            """, (table,))
                            size = cursor.fetchone()["size"]
                            
                            stats[table] = {
                                "record_count": count,
                                "table_size": size
                            }
                            
                        except Exception as e:
                            stats[table] = {"error": str(e)}
                    
        except Exception as e:
            self.logger.error(f"Error obteniendo estadísticas: {e}")
            stats["error"] = str(e)
        
        return stats


def main():
    """Función principal para testing del schema manager"""
    from src.config.settings import DatabaseConfig
    
    print("🔧 Probando Sistema de Creación de Esquemas")
    print("=" * 50)
    
    try:
        # Crear configuración y manager
        config = DatabaseConfig()
        db_manager = DatabaseManager(config)
        
        if db_manager.connect():
            schema_manager = SchemaManager(db_manager)
            
            # Verificar y crear esquema
            results = schema_manager.check_and_create_schema()
            
            print(f"✅ Tablas creadas: {results['tables_created']}")
            print(f"ℹ️ Tablas existentes: {results['tables_existed']}")
            print(f"🔧 Índices creados: {len(results['indexes_created'])}")
            print(f"⚙️ Triggers creados: {len(results['triggers_created'])}")
            print(f"📊 Vistas creadas: {len(results['views_created'])}")
            
            if results['errors']:
                print(f"❌ Errores: {results['errors']}")
            
            # Verificar integridad
            integrity = schema_manager.verify_schema_integrity()
            print(f"\n🔍 Estado del esquema: {integrity['overall_status']}")
            
            # Obtener estadísticas
            stats = schema_manager.get_table_statistics()
            print(f"\n📊 Estadísticas de tablas:")
            for table, stat in stats.items():
                if "error" not in stat:
                    print(f"   {table}: {stat['record_count']} registros, {stat['table_size']}")
            
            db_manager.disconnect()
        else:
            print("❌ No se pudo conectar a la base de datos")
    
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()