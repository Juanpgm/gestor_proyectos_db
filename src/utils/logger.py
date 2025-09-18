"""
Utilidades de logging para el sistema.
"""

import logging
import sys
from pathlib import Path
from typing import Optional

try:
    from rich.console import Console
    from rich.logging import RichHandler
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


def setup_logger(
    name: str,
    level: str = "INFO",
    log_file: Optional[str] = None,
    use_rich: bool = True
) -> logging.Logger:
    """
    Configura un logger con opciones flexibles.
    
    Args:
        name: Nombre del logger
        level: Nivel de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Archivo para logging (opcional)
        use_rich: Usar Rich para logging fancy en consola
        
    Returns:
        Logger configurado
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # Evitar duplicar handlers
    if logger.handlers:
        return logger
    
    # Handler para consola
    if use_rich and RICH_AVAILABLE:
        console = Console()
        console_handler = RichHandler(
            console=console,
            show_path=True,
            show_time=True,
            rich_tracebacks=True
        )
    else:
        console_handler = logging.StreamHandler(sys.stdout)
    
    # Formato del mensaje
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    if not (use_rich and RICH_AVAILABLE):
        console_handler.setFormatter(formatter)
    
    logger.addHandler(console_handler)
    
    # Handler para archivo si está especificado
    if log_file:
        file_path = Path(log_file)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(file_path)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger