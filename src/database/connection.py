"""
Gestión de conexiones a la base de datos PostgreSQL.

Este módulo proporciona funcionalidades para:
- Establecer conexiones a PostgreSQL con PostGIS
- Gestionar pools de conexiones
- Crear y destruir bases de datos
- Ejecutar operaciones básicas de base de datos
"""

from typing import Optional, Dict, Any, Generator
from contextlib import contextmanager
import logging

import psycopg2
from psycopg2.extras import RealDictCursor
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from sqlalchemy.exc import SQLAlchemyError

from ..config.settings import Settings, DatabaseConfig
from ..models import Base
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class DatabaseManager:
    """
    Gestor principal de la base de datos PostgreSQL.
    
    Maneja conexiones, sesiones y operaciones básicas de base de datos
    usando SQLAlchemy como ORM principal.
    """
    
    def __init__(self, config: DatabaseConfig):
        """
        Inicializa el gestor de base de datos.
        
        Args:
            config: Configuración de la base de datos
        """
        self.config = config
        self.engine = None
        self.session_factory = None
        self._is_connected = False
        
    def connect(self) -> bool:
        """
        Establece la conexión a la base de datos.
        
        Returns:
            True si la conexión fue exitosa, False en caso contrario
        """
        try:
            # Debug: mostrar configuración (sin la contraseña)
            logger.info(f"🔧 Conectando a: {self.config.host}:{self.config.port}")
            logger.info(f"🔧 Base de datos: {self.config.database}")
            logger.info(f"🔧 Usuario: {self.config.user}")
            
            # Crear engine con pool de conexiones
            self.engine = create_engine(
                self.config.connection_string,
                poolclass=QueuePool,
                pool_size=5,
                max_overflow=10,
                pool_timeout=30,
                pool_recycle=3600,
                echo=False  # Cambiar a True para debug SQL
            )
            
            # Crear factory de sesiones
            self.session_factory = sessionmaker(
                bind=self.engine,
                autoflush=False,
                autocommit=False
            )
            
            # Probar la conexión
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT version()"))
                version = result.fetchone()[0]
                logger.info(f"Conectado a PostgreSQL: {version}")
            
            self._is_connected = True
            return True
            
        except Exception as e:
            logger.error(f"Error al conectar a la base de datos: {e}")
            self._is_connected = False
            return False
    
    def disconnect(self) -> None:
        """Cierra todas las conexiones a la base de datos."""
        if self.engine:
            self.engine.dispose()
            logger.info("Conexiones a la base de datos cerradas")
        
        self._is_connected = False
    
    @property
    def is_connected(self) -> bool:
        """Retorna True si hay una conexión activa."""
        return self._is_connected and self.engine is not None
    
    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """
        Context manager para obtener una sesión de SQLAlchemy.
        
        Yields:
            Sesión de SQLAlchemy configurada
            
        Raises:
            RuntimeError: Si no hay conexión activa
        """
        if not self.is_connected:
            raise RuntimeError("No hay conexión activa a la base de datos")
        
        session = self.session_factory()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Error en sesión de base de datos: {e}")
            raise
        finally:
            session.close()
    
    def create_database(self) -> bool:
        """
        Crea la base de datos si no existe.
        
        Returns:
            True si la base de datos fue creada o ya existía
        """
        try:
            # Conectar a postgres para crear la DB
            admin_url = f"postgresql://{self.config.user}:{self.config.password}@{self.config.host}:{self.config.port}/postgres"
            admin_engine = create_engine(admin_url, isolation_level="AUTOCOMMIT")
            
            with admin_engine.connect() as conn:
                # Verificar si la DB existe
                result = conn.execute(
                    text("SELECT 1 FROM pg_database WHERE datname = :db_name"),
                    {"db_name": self.config.database}
                )
                
                if not result.fetchone():
                    # Crear la base de datos
                    conn.execute(text(f'CREATE DATABASE "{self.config.database}"'))
                    logger.info(f"Base de datos '{self.config.database}' creada exitosamente")
                else:
                    logger.info(f"Base de datos '{self.config.database}' ya existe")
            
            admin_engine.dispose()
            return True
            
        except Exception as e:
            logger.error(f"Error al crear la base de datos: {e}")
            return False
    
    def drop_database(self) -> bool:
        """
        Elimina la base de datos completamente.
        
        Returns:
            True si la base de datos fue eliminada exitosamente
        """
        try:
            if self.is_connected:
                self.disconnect()
            
            # Conectar a postgres para eliminar la DB
            admin_url = f"postgresql://{self.config.user}:{self.config.password}@{self.config.host}:{self.config.port}/postgres"
            admin_engine = create_engine(admin_url, isolation_level="AUTOCOMMIT")
            
            with admin_engine.connect() as conn:
                # Terminar conexiones activas a la DB
                conn.execute(
                    text("""
                    SELECT pg_terminate_backend(pid)
                    FROM pg_stat_activity 
                    WHERE datname = :db_name AND pid <> pg_backend_pid()
                    """),
                    {"db_name": self.config.database}
                )
                
                # Eliminar la base de datos
                conn.execute(text(f'DROP DATABASE IF EXISTS "{self.config.database}"'))
                logger.info(f"Base de datos '{self.config.database}' eliminada exitosamente")
            
            admin_engine.dispose()
            return True
            
        except Exception as e:
            logger.error(f"Error al eliminar la base de datos: {e}")
            return False
    
    def create_tables(self) -> bool:
        """
        Crea todas las tablas definidas en los modelos.
        
        Returns:
            True si las tablas fueron creadas exitosamente
        """
        try:
            if not self.is_connected:
                raise RuntimeError("No hay conexión activa")
            
            # Crear todas las tablas
            Base.metadata.create_all(self.engine)
            logger.info("Tablas creadas exitosamente")
            return True
            
        except Exception as e:
            logger.error(f"Error al crear las tablas: {e}")
            return False
    
    def drop_tables(self) -> bool:
        """
        Elimina todas las tablas del sistema.
        
        Returns:
            True si las tablas fueron eliminadas exitosamente
        """
        try:
            if not self.is_connected:
                raise RuntimeError("No hay conexión activa")
            
            Base.metadata.drop_all(self.engine)
            logger.info("Tablas eliminadas exitosamente")
            return True
            
        except Exception as e:
            logger.error(f"Error al eliminar las tablas: {e}")
            return False
    
    def get_table_info(self) -> Dict[str, Any]:
        """
        Obtiene información sobre las tablas existentes.
        
        Returns:
            Diccionario con información de las tablas
        """
        try:
            if not self.is_connected:
                raise RuntimeError("No hay conexión activa")
            
            inspector = inspect(self.engine)
            tables = {}
            
            for table_name in inspector.get_table_names():
                columns = inspector.get_columns(table_name)
                tables[table_name] = {
                    'columns': len(columns),
                    'column_names': [col['name'] for col in columns]
                }
            
            return tables
            
        except Exception as e:
            logger.error(f"Error al obtener información de tablas: {e}")
            return {}
    
    def execute_sql(self, sql: str, params: Optional[Dict] = None) -> Any:
        """
        Ejecuta una consulta SQL directa.
        
        Args:
            sql: Consulta SQL a ejecutar
            params: Parámetros para la consulta
            
        Returns:
            Resultado de la consulta
        """
        try:
            with self.get_session() as session:
                result = session.execute(text(sql), params or {})
                if sql.strip().upper().startswith('SELECT'):
                    return result.fetchall()
                return result.rowcount
                
        except Exception as e:
            logger.error(f"Error al ejecutar SQL: {e}")
            raise
    
    def execute_sql_file(self, file_path: str) -> bool:
        """
        Ejecuta un archivo SQL.
        
        Args:
            file_path: Ruta al archivo SQL
            
        Returns:
            True si el archivo se ejecutó exitosamente
            
        Raises:
            Exception: Si hay error ejecutando el archivo SQL
        """
        try:
            from pathlib import Path
            
            sql_file = Path(file_path)
            if not sql_file.exists():
                logger.error(f"Archivo SQL no encontrado: {file_path}")
                raise FileNotFoundError(f"Archivo SQL no encontrado: {file_path}")
                
            # Leer contenido del archivo
            with open(sql_file, 'r', encoding='utf-8') as f:
                sql_content = f.read()
            
            # Ejecutar SQL
            if sql_content.strip():
                self.execute_sql(sql_content)
                return True
            else:
                logger.error(f"Archivo SQL vacío: {file_path}")
                raise ValueError(f"Archivo SQL vacío: {file_path}")
                
        except Exception as e:
            logger.error(f"Error ejecutando archivo SQL {file_path}: {e}")
            raise
    
    def test_connection(self) -> bool:
        """
        Prueba la conexión a la base de datos.
        
        Returns:
            True si la conexión es exitosa
        """
        try:
            # Primero intentar conectar si no está conectado
            if not self.is_connected:
                logger.info("Intentando conectar a la base de datos...")
                if not self.connect():
                    return False
            
            # Probar con una consulta simple
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
                logger.info("✅ Conexión a la base de datos exitosa")
                return True
                
        except Exception as e:
            logger.error(f"❌ Error detallado en conexión: {e}")
            logger.error(f"🔧 Cadena de conexión: {self.config.connection_string}")
            return False


def create_database_manager(settings: Settings) -> DatabaseManager:
    """
    Factory function para crear un DatabaseManager.
    
    Args:
        settings: Configuración del sistema
        
    Returns:
        Instancia configurada de DatabaseManager
    """
    return DatabaseManager(settings.database)


def get_raw_connection(config: DatabaseConfig) -> psycopg2.extensions.connection:
    """
    Obtiene una conexión raw de psycopg2 para operaciones especiales.
    
    Args:
        config: Configuración de la base de datos
        
    Returns:
        Conexión psycopg2
    """
    return psycopg2.connect(
        host=config.host,
        port=config.port,
        database=config.database,
        user=config.user,
        password=config.password,
        cursor_factory=RealDictCursor
    )