"""
Configuración de logging para el sistema.

Proporciona funciones utilitarias para configurar el sistema de logging
con diferentes niveles y formatos según el entorno.
"""

import logging
import logging.handlers
from pathlib import Path
from typing import Optional
from rich.logging import RichHandler
from rich.console import Console

from .settings import LoggingConfig


def setup_logger(
    name: str,
    config: Optional[LoggingConfig] = None,
    console: Optional[Console] = None
) -> logging.Logger:
    """
    Configura un logger con el formato y nivel especificados.
    
    Args:
        name: Nombre del logger
        config: Configuración de logging (opcional)
        console: Consola Rich para logging fancy (opcional)
        
    Returns:
        Logger configurado
    """
    if config is None:
        config = LoggingConfig()
    
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, config.level))
    
    # Evitar duplicar handlers
    if logger.handlers:
        return logger
    
    # Handler para consola con Rich si está disponible
    if console:
        console_handler = RichHandler(
            console=console,
            show_path=True,
            show_time=True,
            rich_tracebacks=True
        )
    else:
        console_handler = logging.StreamHandler()
    
    console_handler.setLevel(getattr(logging, config.level))
    
    # Formato del mensaje
    formatter = logging.Formatter(config.format)
    console_handler.setFormatter(formatter)
    
    logger.addHandler(console_handler)
    
    # Handler para archivo si está especificado
    if config.file:
        file_path = Path(config.file)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.handlers.RotatingFileHandler(
            file_path,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(getattr(logging, config.level))
        file_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Obtiene un logger configurado para el módulo especificado.
    
    Args:
        name: Nombre del módulo
        
    Returns:
        Logger configurado
    """
    return setup_logger(name)