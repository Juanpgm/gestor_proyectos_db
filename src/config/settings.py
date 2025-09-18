"""
Configuración principal del sistema.

Este módulo maneja la carga y validación de configuraciones desde variables
de entorno usando Pydantic para la validación de tipos y valores.
"""

from typing import Optional
from pathlib import Path
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
import os
from dotenv import load_dotenv


# Configuración base para todas las settings
BASE_CONFIG = SettingsConfigDict(
    env_file=".env",
    env_file_encoding="utf-8",
    extra="ignore",
    case_sensitive=False
)


class DatabaseConfig(BaseSettings):
    """Configuración de la base de datos PostgreSQL."""
    
    model_config = BASE_CONFIG
    
    host: str = Field(default="localhost", alias="DB_HOST")
    port: int = Field(default=5432, alias="DB_PORT") 
    database: str = Field(default="gestor_proyectos_db", alias="DB_NAME")
    user: str = Field(default="postgres", alias="DB_USER")
    password: str = Field(default="postgres", alias="DB_PASSWORD")
    db_schema: str = Field(default="public", alias="DB_SCHEMA")
    
    # Variable de entorno estándar de Railway
    database_url: Optional[str] = Field(default=None, alias="DATABASE_URL")
    
    @field_validator("port")
    @classmethod
    def validate_port(cls, v):
        if not 1 <= v <= 65535:
            raise ValueError("El puerto debe estar entre 1 y 65535")
        return v
    
    def _parse_database_url(self) -> dict:
        """Parsea DATABASE_URL para extraer componentes individuales."""
        if not self.database_url:
            return {}
        
        try:
            from urllib.parse import urlparse
            parsed = urlparse(self.database_url)
            
            return {
                "host": parsed.hostname,
                "port": parsed.port or 5432,
                "database": parsed.path.lstrip('/') if parsed.path else 'postgres',
                "user": parsed.username,
                "password": parsed.password
            }
        except Exception:
            return {}
    
    @property
    def connection_string(self) -> str:
        """Genera la cadena de conexión PostgreSQL."""
        # Si hay DATABASE_URL (Railway), usarla directamente
        if self.database_url:
            # Convertir a formato SQLAlchemy
            url = self.database_url
            if url.startswith("postgres://"):
                url = url.replace("postgres://", "postgresql+psycopg2://", 1)
            elif url.startswith("postgresql://"):
                url = url.replace("postgresql://", "postgresql+psycopg2://", 1)
            return url
        
        # Usar configuración de variables individuales
        return f"postgresql+psycopg2://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"
    
    @property
    def async_connection_string(self) -> str:
        """Genera la cadena de conexión PostgreSQL asíncrona."""
        # Si hay DATABASE_URL (Railway), usarla directamente
        if self.database_url:
            # Convertir a formato asyncpg
            url = self.database_url
            if url.startswith("postgres://"):
                url = url.replace("postgres://", "postgresql+asyncpg://", 1)
            elif url.startswith("postgresql://"):
                url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
            return url
        
        # Usar configuración de variables individuales
        return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"
    
    @property
    def is_railway(self) -> bool:
        """Detecta si se está usando Railway."""
        if self.database_url:
            return "railway" in self.database_url.lower() or "rlwy.net" in self.database_url.lower()
        return "railway" in self.host.lower() or "rlwy.net" in self.host.lower()
    
    @property
    def is_local(self) -> bool:
        """Detecta si se está usando una base de datos local."""
        if self.database_url:
            return "localhost" in self.database_url or "127.0.0.1" in self.database_url
        return self.host in ["localhost", "127.0.0.1", "::1"]
    
    @property
    def connection_info(self) -> dict:
        """Retorna información segura de la conexión (sin contraseña)."""
        if self.database_url:
            parsed = self._parse_database_url()
            return {
                "host": parsed.get("host", "unknown"),
                "port": parsed.get("port", "unknown"),
                "database": parsed.get("database", "unknown"),
                "user": parsed.get("user", "unknown"),
                "schema": self.db_schema,
                "is_railway": self.is_railway,
                "is_local": self.is_local,
                "source": "DATABASE_URL"
            }
        
        return {
            "host": self.host,
            "port": self.port,
            "database": self.database,
            "user": self.user,
            "schema": self.db_schema,
            "is_railway": self.is_railway,
            "is_local": self.is_local,
            "source": "individual_vars"
        }


class PostGISConfig(BaseSettings):
    """Configuración específica de PostGIS."""
    
    model_config = BASE_CONFIG
    
    version: str = Field(default="3.3", alias="POSTGIS_VERSION")
    enable_geography: bool = Field(default=True)
    enable_topology: bool = Field(default=False)


class LoggingConfig(BaseSettings):
    """Configuración de logging."""
    
    model_config = BASE_CONFIG
    
    level: str = Field(default="INFO", alias="LOG_LEVEL")
    file: Optional[str] = Field(default=None, alias="LOG_FILE")
    format: str = Field(default="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    
    @field_validator("level")
    @classmethod
    def validate_level(cls, v):
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if v.upper() not in valid_levels:
            raise ValueError(f"Nivel de log debe ser uno de: {valid_levels}")
        return v.upper()


class ApplicationConfig(BaseSettings):
    """Configuración general de la aplicación."""
    
    model_config = BASE_CONFIG
    
    name: str = Field(default="Gestor Proyectos DB", alias="APP_NAME")
    version: str = Field(default="1.0.0", alias="APP_VERSION")
    environment: str = Field(default="development", alias="APP_ENV")
    
    # Rutas de archivos
    data_dir: Path = Field(default=Path("app_outputs"), env="DATA_DIR")
    contratos_file: Path = Field(
        default=Path("app_outputs/emprestito_outputs/emp_contratos.json"),
        env="CONTRATOS_FILE"
    )
    procesos_file: Path = Field(
        default=Path("app_outputs/emprestito_outputs/emp_procesos.json"),
        env="PROCESOS_FILE"
    )
    
    @field_validator("data_dir", "contratos_file", "procesos_file", mode="before")
    @classmethod
    def validate_paths(cls, v):
        return Path(v) if isinstance(v, str) else v


class ConnectionConfig(BaseSettings):
    """Configuración de conexiones y pools."""
    
    model_config = BASE_CONFIG
    
    timeout: int = Field(default=30, alias="CONNECTION_TIMEOUT")
    pool_size: int = Field(default=5, alias="POOL_SIZE")
    max_overflow: int = Field(default=10, alias="MAX_OVERFLOW")
    
    @field_validator("timeout", "pool_size", "max_overflow")
    @classmethod
    def validate_positive_int(cls, v):
        if v <= 0:
            raise ValueError("El valor debe ser positivo")
        return v


class Settings(BaseSettings):
    """Configuración principal que agrupa todas las configuraciones."""
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8"
    }


def load_config(env_file: str = ".env") -> dict:
    """
    Carga la configuración desde el archivo de entorno especificado.
    
    Args:
        env_file: Ruta al archivo de variables de entorno
        
    Returns:
        Diccionario con toda la configuración cargada
        
    Raises:
        FileNotFoundError: Si el archivo .env no existe
        ValidationError: Si hay errores en la validación de configuración
    """
    env_path = Path(env_file)
    
    if not env_path.exists():
        raise FileNotFoundError(f"Archivo de configuración no encontrado: {env_file}")
    
    # Cargar variables de entorno explícitamente
    load_dotenv(env_path, override=True)
    
    # Crear configuraciones individuales (pydantic-settings usará las variables cargadas)
    database = DatabaseConfig()
    postgis = PostGISConfig()
    logging = LoggingConfig()
    application = ApplicationConfig()
    connection = ConnectionConfig()
    
    # Retornar como diccionario para compatibilidad
    return {
        "database": database,
        "postgis": postgis,
        "logging": logging,
        "application": application,
        "connection": connection
    }


def get_database_url(config: dict) -> str:
    """
    Obtiene la URL de conexión a la base de datos.
    
    Args:
        config: Configuración del sistema
        
    Returns:
        URL de conexión a PostgreSQL
    """
    db_config = config["database"]
    return db_config.connection_string


# Configuración global (se carga cuando se importa el módulo)
_config: Optional[dict] = None


def get_settings() -> dict:
    """
    Obtiene la configuración global del sistema.
    
    Returns:
        Diccionario con la configuración global
    """
    global _config
    if _config is None:
        _config = load_config()
    return _config