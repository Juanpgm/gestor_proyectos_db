#!/usr/bin/env python3
"""
🚂 Configuración Específica para Railway
========================================

Este archivo maneja la configuración específica para Railway,
incluyendo la conexión a PostgreSQL en Railway.

SEGURIDAD: Este archivo NO contiene credenciales hardcodeadas.
Todas las credenciales se obtienen de variables de entorno.
"""

import os
import logging
from typing import Optional
from pathlib import Path

logger = logging.getLogger(__name__)

def load_env_file(env_file: str = ".env"):
    """
    Cargar variables de entorno desde archivo específico
    
    Args:
        env_file: Nombre del archivo de entorno (por defecto .env)
    """
    env_path = Path(__file__).parent / env_file
    
    if not env_path.exists():
        # Si no existe el archivo específico, intentar con .env por defecto
        if env_file != ".env":
            env_path = Path(__file__).parent / ".env"
            if not env_path.exists():
                return
        else:
            return
    
    try:
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    # Sobrescribir variables existentes para permitir override
                    os.environ[key] = value
                    
        print(f"✅ Variables de entorno cargadas desde: {env_file}")
    except Exception as e:
        print(f"⚠️ Error loading {env_file} file: {e}")


def load_local_env():
    """Cargar configuración específica para entorno local"""
    load_env_file(".env.local")

class RailwayDatabaseConfig:
    """Configuración específica para Railway PostgreSQL"""
    
    def __init__(self):
        self.database_url = os.environ.get("DATABASE_URL")
        self.is_railway = bool(self.database_url)
        
        if self.is_railway:
            self._parse_railway_url()
        else:
            self._use_local_config()
    
    def _parse_railway_url(self):
        """Parsear la URL de Railway PostgreSQL"""
        try:
            import urllib.parse as urlparse
            
            url = urlparse.urlparse(self.database_url)
            
            self.host = url.hostname
            self.port = url.port or 5432
            self.user = url.username
            self.password = url.password
            self.database = url.path[1:]  # Remover el '/' inicial
            
            logger.info(f"🔗 Railway PostgreSQL configurado: {self.host}:{self.port}")
            
        except Exception as e:
            logger.error(f"❌ Error parseando DATABASE_URL: {str(e)}")
            raise
    
    def _use_local_config(self):
        """Configuración local alternativa"""
        self.host = os.environ.get("DB_HOST", "localhost")
        self.port = int(os.environ.get("DB_PORT", "5432"))
        self.user = os.environ.get("DB_USER", "postgres")
        self.password = os.environ.get("DB_PASSWORD", "")
        self.database = os.environ.get("DB_NAME", "gestor_proyectos")
        
        logger.info(f"🏠 Configuración local: {self.host}:{self.port}")
    
    @property
    def connection_string(self) -> str:
        """Obtener string de conexión"""
        if self.database_url:
            return self.database_url
        else:
            return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"
    
    def test_connection_params(self) -> dict:
        """Obtener parámetros para test de conexión"""
        return {
            "host": self.host,
            "port": self.port,
            "user": self.user,
            "password": self.password,
            "database": self.database
        }
    
    def is_railway_environment(self) -> bool:
        """Verificar si estamos en Railway"""
        return self.is_railway
    
    def get_safe_info(self) -> dict:
        """Obtener información segura (sin credenciales) para logging"""
        return {
            "host": self.host,
            "port": self.port,
            "database": self.database,
            "environment": "Railway" if self.is_railway else "Local",
            "connection_method": "DATABASE_URL" if self.database_url else "Individual vars"
        }

def create_railway_connection():
    """Factory para crear conexión Railway DatabaseManager con fallback automático"""
    # Cargar variables de entorno desde .env
    load_env_file()
    
    # Verificar si tenemos configuración Railway
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        logger.warning("No se encontró DATABASE_URL en variables de entorno")
        return None
    
    try:
        # Importar aquí para evitar dependencias circulares
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent / "src"))
        
        from src.config.settings import DatabaseConfig
        from src.database.connection import DatabaseManager
        
        # Crear configuración usando DatabaseConfig que ya maneja DATABASE_URL
        config = DatabaseConfig()
        
        # Log información segura (sin credenciales)
        logger.info(f"Intentando conectar a Railway...")
        
        # Crear el DatabaseManager
        db_manager = DatabaseManager(config)
        
        # Intentar conectar con timeout corto para Railway
        try:
            if db_manager.connect():
                # Verificar que la conexión realmente funciona
                if db_manager.test_connection():
                    logger.info("DatabaseManager Railway conectado exitosamente")
                    return db_manager
                else:
                    logger.warning("Railway: conexión establecida pero test falló")
            else:
                logger.warning("Railway: no se pudo establecer conexión")
        except Exception as conn_error:
            logger.warning(f"Railway no disponible: {str(conn_error)}")
        
        # Si llegamos aquí, Railway falló
        logger.info("Railway no disponible, intentando fallback local...")
        
        # Intentar fallback local temporal removiendo DATABASE_URL
        original_url = os.environ.pop("DATABASE_URL", None)
        try:
            # Crear nueva configuración sin DATABASE_URL
            local_config = DatabaseConfig()
            local_db_manager = DatabaseManager(local_config)
            
            if local_db_manager.connect() and local_db_manager.test_connection():
                logger.info("Fallback local exitoso")
                return local_db_manager
            else:
                logger.error("Fallback local también falló")
                
        finally:
            # Restaurar DATABASE_URL
            if original_url:
                os.environ["DATABASE_URL"] = original_url
        
        return None
        
    except Exception as e:
        logger.error(f"Error crítico creando DatabaseManager: {e}")
        return None

# Verificación de configuración
def verify_railway_setup():
    """Verificar que Railway esté configurado correctamente"""
    try:
        config = create_railway_connection()
        
        if not config.is_railway_environment():
            logger.warning("⚠️ No se detectó entorno Railway")
            return False
        
        if not all([config.host, config.port, config.user, config.password, config.database]):
            logger.error("❌ Faltan parámetros de conexión")
            return False
        
        logger.info("✅ Configuración Railway verificada")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error verificando Railway: {str(e)}")
        return False