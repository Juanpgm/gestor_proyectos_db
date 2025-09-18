"""
Modelos de datos para contratos de empréstito.

Este módulo define los modelos SQLAlchemy para la tabla de contratos,
incluyendo validaciones y relaciones con otras entidades.
"""

from datetime import datetime, date
from typing import Optional, Dict, Any
from decimal import Decimal

from sqlalchemy import (
    Column, String, Integer, Numeric, Date, DateTime, 
    Boolean, Text, JSON, ForeignKey
)
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

from .base import BaseModel

Base = declarative_base()


class Contrato(BaseModel):
    """
    Modelo para contratos de empréstito.
    
    Representa un contrato registrado en SECOP con toda la información
    relevante para seguimiento y análisis.
    """
    
    __tablename__ = "emp_contratos"
    
    # Identificadores principales
    id_contrato = Column(String(50), primary_key=True, comment="ID único del contrato en SECOP")
    referencia_del_contrato = Column(String(100), unique=True, nullable=False, 
                                   comment="Referencia única del contrato")
    proceso_de_compra = Column(String(50), nullable=False, 
                              comment="ID del proceso de compra asociado")
    
    # Información de la entidad
    nombre_entidad = Column(String(500), nullable=False, comment="Nombre de la entidad contratante")
    nit_entidad = Column(String(20), nullable=False, comment="NIT de la entidad")
    departamento = Column(String(100), comment="Departamento de la entidad")
    ciudad = Column(String(100), comment="Ciudad de la entidad")
    localizacion = Column(String(200), comment="Localización completa")
    orden = Column(String(50), comment="Orden territorial/nacional")
    sector = Column(String(200), comment="Sector de la entidad")
    rama = Column(String(50), comment="Rama del poder público")
    entidad_centralizada = Column(String(50), comment="Tipo de centralización")
    codigo_entidad = Column(String(20), comment="Código interno de la entidad")
    
    # Información del contrato
    estado_contrato = Column(String(50), nullable=False, comment="Estado actual del contrato")
    codigo_de_categoria_principal = Column(String(50), comment="Código de categoría UNSPSC")
    descripcion_del_proceso = Column(Text, comment="Descripción detallada del proceso")
    objeto_del_contrato = Column(Text, nullable=False, comment="Objeto del contrato")
    tipo_de_contrato = Column(String(100), comment="Tipo de contrato")
    modalidad_de_contratacion = Column(String(100), comment="Modalidad de contratación")
    justificacion_modalidad = Column(String(200), comment="Justificación de la modalidad")
    
    # Fechas importantes
    fecha_de_firma = Column(Date, comment="Fecha de firma del contrato")
    fecha_de_inicio_del_contrato = Column(Date, comment="Fecha de inicio de ejecución")
    fecha_de_fin_del_contrato = Column(Date, comment="Fecha de finalización")
    duracion_del_contrato = Column(String(50), comment="Duración expresada en texto")
    fecha_inicio_liquidacion = Column(Date, comment="Fecha de inicio de liquidación")
    fecha_fin_liquidacion = Column(Date, comment="Fecha de fin de liquidación")
    
    # Información del proveedor
    documento_proveedor = Column(String(20), comment="Documento del proveedor")
    tipodocproveedor = Column(String(50), comment="Tipo de documento del proveedor")
    proveedor_adjudicado = Column(String(500), nullable=False, comment="Nombre del proveedor")
    es_grupo = Column(Boolean, comment="Si es un grupo empresarial")
    es_pyme = Column(Boolean, comment="Si es una PYME")
    codigo_proveedor = Column(String(20), comment="Código interno del proveedor")
    
    # Información del representante legal
    nombre_representante_legal = Column(String(200), comment="Nombre del representante legal")
    nacionalidad_representante_legal = Column(String(10), comment="Nacionalidad del representante")
    domicilio_representante_legal = Column(String(200), comment="Domicilio del representante")
    tipo_identificacion_representante_legal = Column(String(50), comment="Tipo de ID del representante")
    identificacion_representante_legal = Column(String(50), comment="ID del representante")
    genero_representante_legal = Column(String(20), comment="Género del representante")
    
    # Valores monetarios
    valor_del_contrato = Column(Numeric(15, 2), nullable=False, comment="Valor total del contrato")
    valor_de_pago_adelantado = Column(Numeric(15, 2), default=0, comment="Valor de pago adelantado")
    valor_facturado = Column(Numeric(15, 2), default=0, comment="Valor facturado")
    valor_pendiente_de_pago = Column(Numeric(15, 2), default=0, comment="Valor pendiente de pago")
    valor_pagado = Column(Numeric(15, 2), default=0, comment="Valor pagado")
    valor_amortizado = Column(Numeric(15, 2), default=0, comment="Valor amortizado")
    valor_pendiente_de_ejecucion = Column(Numeric(15, 2), default=0, comment="Valor pendiente de ejecución")
    
    # Recursos financieros
    presupuesto_general_nacion = Column(Numeric(15, 2), default=0, comment="Recursos del PGN")
    sistema_general_participaciones = Column(Numeric(15, 2), default=0, comment="Recursos del SGP")
    sistema_general_regalias = Column(Numeric(15, 2), default=0, comment="Recursos del SGR")
    recursos_propios_alcaldias = Column(Numeric(15, 2), default=0, comment="Recursos propios territoriales")
    recursos_de_credito = Column(Numeric(15, 2), default=0, comment="Recursos de crédito")
    recursos_propios = Column(Numeric(15, 2), default=0, comment="Otros recursos propios")
    
    # Información de proyecto BPIN
    estado_bpin = Column(String(50), comment="Estado en BPIN")
    anno_bpin = Column(String(10), comment="Año del BPIN")
    bpin = Column(String(20), comment="Código BPIN")
    saldo_cdp = Column(String(50), comment="Saldo CDP")
    saldo_vigencia = Column(String(50), comment="Saldo vigencia")
    
    # Configuraciones del contrato
    condiciones_de_entrega = Column(String(100), comment="Condiciones de entrega")
    habilita_pago_adelantado = Column(Boolean, comment="Permite pago adelantado")
    liquidacion = Column(Boolean, comment="Requiere liquidación")
    obligacion_ambiental = Column(Boolean, comment="Tiene obligación ambiental")
    obligaciones_postconsumo = Column(Boolean, comment="Tiene obligaciones postconsumo")
    reversion = Column(Boolean, comment="Tiene reversión")
    origen_de_los_recursos = Column(String(50), comment="Origen de recursos")
    destino_gasto = Column(String(50), comment="Destino del gasto")
    el_contrato_puede_ser_prorrogado = Column(Boolean, comment="Puede ser prorrogado")
    fecha_notificacion_prorroga = Column(Date, comment="Fecha de notificación de prórroga")
    
    # Información de postconflicto
    espostconflicto = Column(Boolean, comment="Es proceso de postconflicto")
    dias_adicionados = Column(String(20), comment="Días adicionados")
    puntos_del_acuerdo = Column(String(100), comment="Puntos del acuerdo de paz")
    pilares_del_acuerdo = Column(String(100), comment="Pilares del acuerdo")
    
    # Información bancaria
    nombre_del_banco = Column(String(100), comment="Banco del contrato")
    tipo_de_cuenta = Column(String(50), comment="Tipo de cuenta")
    numero_de_cuenta = Column(String(50), comment="Número de cuenta")
    
    # Responsables del contrato
    nombre_ordenador_del_gasto = Column(String(200), comment="Ordenador del gasto")
    tipo_documento_ordenador_gasto = Column(String(50), comment="Tipo doc ordenador gasto")
    numero_documento_ordenador_gasto = Column(String(50), comment="Número doc ordenador gasto")
    
    nombre_supervisor = Column(String(200), comment="Supervisor del contrato")
    tipo_documento_supervisor = Column(String(50), comment="Tipo doc supervisor")
    numero_documento_supervisor = Column(String(50), comment="Número doc supervisor")
    
    nombre_ordenador_de_pago = Column(String(200), comment="Ordenador de pago")
    tipo_documento_ordenador_pago = Column(String(50), comment="Tipo doc ordenador pago")
    numero_documento_ordenador_pago = Column(String(50), comment="Número doc ordenador pago")
    
    # URLs y referencias
    urlproceso = Column(JSON, comment="URL del proceso en SECOP")
    
    # Metadatos de extracción
    search_field = Column(String(50), comment="Campo de búsqueda usado")
    referencia_buscada = Column(String(100), comment="Referencia buscada")
    search_type = Column(String(50), comment="Tipo de búsqueda")
    total_campos = Column(Integer, comment="Total de campos extraídos")
    
    def __repr__(self) -> str:
        return f"<Contrato(id='{self.id_contrato}', referencia='{self.referencia_del_contrato}')>"
    
    @property
    def valor_total_recursos(self) -> Decimal:
        """Calcula el total de recursos asignados al contrato."""
        recursos = [
            self.presupuesto_general_nacion or 0,
            self.sistema_general_participaciones or 0,
            self.sistema_general_regalias or 0,
            self.recursos_propios_alcaldias or 0,
            self.recursos_de_credito or 0,
            self.recursos_propios or 0
        ]
        return sum(recursos)
    
    @property
    def porcentaje_ejecucion(self) -> float:
        """Calcula el porcentaje de ejecución del contrato."""
        if not self.valor_del_contrato or self.valor_del_contrato == 0:
            return 0.0
        
        valor_ejecutado = (self.valor_pagado or 0) + (self.valor_facturado or 0)
        return float((valor_ejecutado / self.valor_del_contrato) * 100)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte el modelo a diccionario para serialización."""
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }