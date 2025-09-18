"""
Funciones para configuración e inicialización de PostGIS.

Este módulo proporciona utilidades para:
- Habilitar PostGIS en la base de datos
- Configurar extensiones geoespaciales
- Verificar la instalación de PostGIS
- Crear funciones geoespaciales personalizadas
"""

from typing import Dict, List, Optional
import logging

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from .connection import DatabaseManager
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class PostGISManager:
    """
    Gestor para operaciones específicas de PostGIS.
    
    Maneja la configuración y inicialización de capacidades
    geoespaciales en PostgreSQL.
    """
    
    def __init__(self, db_manager: DatabaseManager):
        """
        Inicializa el gestor de PostGIS.
        
        Args:
            db_manager: Gestor de base de datos configurado
        """
        self.db_manager = db_manager
    
    def enable_postgis(self) -> bool:
        """
        Habilita PostGIS en la base de datos.
        
        Returns:
            True si PostGIS fue habilitado exitosamente
        """
        try:
            with self.db_manager.get_session() as session:
                # Verificar si PostGIS ya está habilitado
                result = session.execute(
                    text("""
                    SELECT EXISTS(
                        SELECT 1 FROM pg_extension WHERE extname = 'postgis'
                    )
                    """)
                )
                
                if result.scalar():
                    logger.info("PostGIS ya está habilitado")
                    return True
                
                # Habilitar PostGIS
                session.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
                logger.info("PostGIS habilitado exitosamente")
                
                # Habilitar extensiones adicionales
                extensions = [
                    "postgis_topology",
                    "postgis_raster", 
                    "fuzzystrmatch",
                    "postgis_tiger_geocoder"
                ]
                
                for ext in extensions:
                    try:
                        session.execute(text(f"CREATE EXTENSION IF NOT EXISTS {ext}"))
                        logger.debug(f"Extensión {ext} habilitada")
                    except Exception as e:
                        logger.warning(f"No se pudo habilitar {ext}: {e}")
                
                return True
                
        except Exception as e:
            logger.error(f"Error al habilitar PostGIS: {e}")
            return False
    
    def get_postgis_version(self) -> Optional[str]:
        """
        Obtiene la versión de PostGIS instalada.
        
        Returns:
            Versión de PostGIS o None si no está instalado
        """
        try:
            with self.db_manager.get_session() as session:
                result = session.execute(text("SELECT PostGIS_Version()"))
                version = result.scalar()
                logger.info(f"Versión de PostGIS: {version}")
                return version
                
        except Exception as e:
            logger.error(f"Error al obtener versión de PostGIS: {e}")
            return None
    
    def create_spatial_indexes(self, table_name: str, geometry_column: str = "geom") -> bool:
        """
        Crea índices espaciales para una tabla.
        
        Args:
            table_name: Nombre de la tabla
            geometry_column: Nombre de la columna de geometría
            
        Returns:
            True si los índices fueron creados exitosamente
        """
        try:
            with self.db_manager.get_session() as session:
                # Crear índice GIST para consultas espaciales
                index_name = f"idx_{table_name}_{geometry_column}_gist"
                session.execute(
                    text(f"""
                    CREATE INDEX IF NOT EXISTS {index_name}
                    ON {table_name} USING GIST ({geometry_column})
                    """)
                )
                
                logger.info(f"Índice espacial creado: {index_name}")
                return True
                
        except Exception as e:
            logger.error(f"Error al crear índices espaciales: {e}")
            return False
    
    def get_geometry_columns(self) -> List[Dict]:
        """
        Obtiene información sobre las columnas de geometría.
        
        Returns:
            Lista con información de columnas geométricas
        """
        try:
            with self.db_manager.get_session() as session:
                result = session.execute(
                    text("""
                    SELECT 
                        f_table_schema,
                        f_table_name,
                        f_geometry_column,
                        coord_dimension,
                        srid,
                        type
                    FROM geometry_columns
                    ORDER BY f_table_schema, f_table_name
                    """)
                )
                
                columns = []
                for row in result:
                    columns.append({
                        'schema': row[0],
                        'table': row[1], 
                        'column': row[2],
                        'dimension': row[3],
                        'srid': row[4],
                        'type': row[5]
                    })
                
                return columns
                
        except Exception as e:
            logger.error(f"Error al obtener columnas de geometría: {e}")
            return []
    
    def set_srid(self, table_name: str, geometry_column: str, srid: int) -> bool:
        """
        Establece el SRID para una columna de geometría.
        
        Args:
            table_name: Nombre de la tabla
            geometry_column: Nombre de la columna de geometría
            srid: Sistema de referencia espacial (SRID)
            
        Returns:
            True si el SRID fue establecido exitosamente
        """
        try:
            with self.db_manager.get_session() as session:
                session.execute(
                    text(f"""
                    ALTER TABLE {table_name} 
                    ALTER COLUMN {geometry_column} 
                    TYPE geometry({geometry_column}, {srid}) 
                    USING ST_SetSRID({geometry_column}, {srid})
                    """)
                )
                
                logger.info(f"SRID {srid} establecido para {table_name}.{geometry_column}")
                return True
                
        except Exception as e:
            logger.error(f"Error al establecer SRID: {e}")
            return False
    
    def validate_geometries(self, table_name: str, geometry_column: str = "geom") -> Dict:
        """
        Valida las geometrías en una tabla.
        
        Args:
            table_name: Nombre de la tabla
            geometry_column: Nombre de la columna de geometría
            
        Returns:
            Diccionario con estadísticas de validación
        """
        try:
            with self.db_manager.get_session() as session:
                # Contar total de registros
                total_result = session.execute(
                    text(f"SELECT COUNT(*) FROM {table_name}")
                )
                total_records = total_result.scalar()
                
                # Contar geometrías válidas
                valid_result = session.execute(
                    text(f"""
                    SELECT COUNT(*) FROM {table_name} 
                    WHERE ST_IsValid({geometry_column}) = true
                    """)
                )
                valid_records = valid_result.scalar()
                
                # Contar geometrías nulas
                null_result = session.execute(
                    text(f"""
                    SELECT COUNT(*) FROM {table_name} 
                    WHERE {geometry_column} IS NULL
                    """)
                )
                null_records = null_result.scalar()
                
                stats = {
                    'total_records': total_records,
                    'valid_geometries': valid_records,
                    'invalid_geometries': total_records - valid_records - null_records,
                    'null_geometries': null_records,
                    'validity_percentage': (valid_records / total_records * 100) if total_records > 0 else 0
                }
                
                logger.info(f"Validación de geometrías para {table_name}: {stats}")
                return stats
                
        except Exception as e:
            logger.error(f"Error al validar geometrías: {e}")
            return {}
    
    def create_geometry_column(self, table_name: str, column_name: str, 
                             geometry_type: str, srid: int = 4326) -> bool:
        """
        Crea una columna de geometría en una tabla existente.
        
        Args:
            table_name: Nombre de la tabla
            column_name: Nombre de la nueva columna
            geometry_type: Tipo de geometría (POINT, LINESTRING, POLYGON, etc.)
            srid: Sistema de referencia espacial
            
        Returns:
            True si la columna fue creada exitosamente
        """
        try:
            with self.db_manager.get_session() as session:
                session.execute(
                    text(f"""
                    SELECT AddGeometryColumn(
                        '{table_name}', 
                        '{column_name}', 
                        {srid}, 
                        '{geometry_type}', 
                        2
                    )
                    """)
                )
                
                logger.info(f"Columna de geometría {column_name} creada en {table_name}")
                return True
                
        except Exception as e:
            logger.error(f"Error al crear columna de geometría: {e}")
            return False


def setup_postgis(db_manager: DatabaseManager) -> bool:
    """
    Configura PostGIS completamente en la base de datos.
    
    Args:
        db_manager: Gestor de base de datos
        
    Returns:
        True si PostGIS fue configurado exitosamente
    """
    postgis_manager = PostGISManager(db_manager)
    
    # Habilitar PostGIS
    if not postgis_manager.enable_postgis():
        return False
    
    # Verificar versión
    version = postgis_manager.get_postgis_version()
    if not version:
        logger.error("No se pudo verificar la versión de PostGIS")
        return False
    
    logger.info("PostGIS configurado exitosamente")
    return True