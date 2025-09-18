"""
Modelos de datos del sistema de gestión de proyectos.

Este módulo exporta todos los modelos disponibles en el sistema
para facilitar las importaciones.
"""

from .base import BaseModel, Base
from .contrato import Contrato
from .proceso import Proceso

# Importar todas las clases principales
__all__ = [
    "BaseModel",
    "Base", 
    "Contrato",
    "Proceso"
]

# Metadatos para Alembic
metadata = Base.metadata