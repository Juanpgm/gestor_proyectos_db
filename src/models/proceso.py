"""
Modelos de datos para procesos de empréstito.

Este módulo define los modelos SQLAlchemy para la tabla de procesos,
incluyendo validaciones y relaciones con contratos.
"""

from datetime import datetime, date
from typing import Optional, Dict, Any
from decimal import Decimal

from sqlalchemy import (
    Column, String, Integer, Numeric, Date, DateTime, 
    Boolean, Text, JSON, ForeignKey
)
from sqlalchemy.orm import relationship

from .base import BaseModel


class Proceso(BaseModel):
    """
    Modelo para procesos de seguimiento DACP.
    
    Representa un proceso de contratación registrado en SECOP con información
    de seguimiento y estado del proceso.
    """
    
    __tablename__ = "emp_seguimiento_procesos_dacp"
    
    # Identificador principal
    id = Column(Integer, primary_key=True, comment="ID único del proceso")
    referencia_proceso = Column(String(100), unique=True, nullable=False, 
                              comment="Referencia única del proceso")
    
    # Información básica del proceso
    banco = Column(String(100), nullable=False, comment="Banco asociado al empréstito")
    descripcion = Column(Text, comment="Descripción breve del proceso")
    objeto = Column(Text, nullable=False, comment="Objeto detallado del proceso")
    
    # Valores monetarios
    valor_total = Column(Numeric(15, 2), nullable=False, comment="Valor total del proceso")
    valor_plataforma = Column(Numeric(15, 2), comment="Valor registrado en plataforma SECOP")
    
    # Información contractual
    modalidad = Column(String(100), comment="Modalidad de contratación")
    referencia_contrato = Column(String(100), comment="Referencia del contrato asociado")
    
    # Fechas y cronograma
    planeado = Column(Date, comment="Fecha planeada del proceso")
    
    # Estado y seguimiento
    estado_proceso_secop = Column(String(100), nullable=False, comment="Estado actual en SECOP")
    observaciones = Column(Text, comment="Observaciones del seguimiento")
    
    # Contacto
    numero_contacto = Column(String(20), comment="Número de contacto")
    
    # URLs de referencia
    url_proceso = Column(String(500), comment="URL del proceso en SECOP")
    url_estado_real_proceso = Column(String(500), comment="URL del estado real del proceso")
    
    # Metadatos de procesamiento
    archivo_origen = Column(String(200), comment="Archivo origen de los datos")
    fecha_procesamiento = Column(DateTime, default=datetime.utcnow, 
                                comment="Fecha de procesamiento del registro")
    
    # Relación con contratos (un proceso puede tener múltiples contratos)
    contratos = relationship("Contrato", back_populates="proceso", 
                           cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<Proceso(id={self.id}, referencia='{self.referencia_proceso}')>"
    
    @property
    def numero_contratos(self) -> int:
        """Retorna el número de contratos asociados al proceso."""
        return len(self.contratos) if self.contratos else 0
    
    @property
    def valor_total_contratos(self) -> Decimal:
        """Calcula el valor total de todos los contratos asociados."""
        if not self.contratos:
            return Decimal('0')
        
        return sum(
            contrato.valor_del_contrato or Decimal('0') 
            for contrato in self.contratos
        )
    
    @property
    def porcentaje_contratacion(self) -> float:
        """Calcula el porcentaje de contratación vs valor total del proceso."""
        if not self.valor_total or self.valor_total == 0:
            return 0.0
        
        valor_contratado = self.valor_total_contratos
        return float((valor_contratado / self.valor_total) * 100)
    
    def get_contratos_por_estado(self, estado: str) -> list:
        """
        Obtiene contratos filtrados por estado.
        
        Args:
            estado: Estado del contrato a filtrar
            
        Returns:
            Lista de contratos con el estado especificado
        """
        if not self.contratos:
            return []
        
        return [
            contrato for contrato in self.contratos 
            if contrato.estado_contrato and contrato.estado_contrato.lower() == estado.lower()
        ]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte el modelo a diccionario para serialización."""
        result = {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }
        
        # Agregar información calculada
        result['numero_contratos'] = self.numero_contratos
        result['valor_total_contratos'] = float(self.valor_total_contratos)
        result['porcentaje_contratacion'] = self.porcentaje_contratacion
        
        return result


# Actualizar el modelo de Contrato para incluir la relación con Proceso
from .contrato import Contrato

# Agregar la relación en Contrato
Contrato.proceso_id = Column(Integer, ForeignKey('emp_seguimiento_procesos_dacp.id'), 
                            comment="ID del proceso asociado")
Contrato.proceso = relationship("Proceso", back_populates="contratos")