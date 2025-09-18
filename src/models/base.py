"""
Modelo base para todas las entidades del sistema.

Define la clase base con campos comunes y funcionalidades compartidas
entre todos los modelos del sistema.
"""

from datetime import datetime
from typing import Any, Dict

from sqlalchemy import Column, DateTime, Integer
from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy.orm import Session

Base = declarative_base()


class BaseModel(Base):
    """
    Clase base para todos los modelos del sistema.
    
    Proporciona campos comunes como timestamps y funcionalidades
    básicas compartidas entre todas las entidades.
    """
    
    __abstract__ = True
    
    # Campos de auditoría
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False,
                       comment="Fecha y hora de creación del registro")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow,
                       comment="Fecha y hora de última actualización")
    
    @declared_attr
    def __tablename__(cls):
        """Genera automáticamente el nombre de la tabla basado en el nombre de la clase."""
        return cls.__name__.lower()
    
    def save(self, session: Session) -> None:
        """
        Guarda o actualiza el registro en la base de datos.
        
        Args:
            session: Sesión de SQLAlchemy
        """
        try:
            session.add(self)
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
    
    def delete(self, session: Session) -> None:
        """
        Elimina el registro de la base de datos.
        
        Args:
            session: Sesión de SQLAlchemy
        """
        try:
            session.delete(self)
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
    
    def update(self, session: Session, **kwargs) -> None:
        """
        Actualiza campos específicos del registro.
        
        Args:
            session: Sesión de SQLAlchemy
            **kwargs: Campos a actualizar
        """
        try:
            for key, value in kwargs.items():
                if hasattr(self, key):
                    setattr(self, key, value)
            
            self.updated_at = datetime.utcnow()
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convierte el modelo a diccionario.
        
        Returns:
            Diccionario con todos los campos del modelo
        """
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }
    
    def __repr__(self) -> str:
        """Representación string del modelo."""
        return f"<{self.__class__.__name__}({', '.join(f'{k}={v}' for k, v in self.to_dict().items())})>"