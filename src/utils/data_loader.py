"""
Utilidades para carga de datos desde archivos JSON.

Este módulo proporciona funciones para:
- Cargar datos de contratos desde emp_contratos.json
- Cargar datos de procesos desde emp_procesos.json
- Validar y limpiar datos antes de la inserción
- Manejar relaciones entre procesos y contratos
"""

import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from decimal import Decimal, InvalidOperation
from datetime import datetime, date

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..models import Proceso, Contrato
from ..database.connection import DatabaseManager
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class DataLoader:
    """
    Cargador de datos desde archivos JSON a la base de datos.
    
    Maneja la carga de contratos y procesos con validación y limpieza
    de datos, estableciendo las relaciones apropiadas.
    """
    
    def __init__(self, db_manager: DatabaseManager):
        """
        Inicializa el cargador de datos.
        
        Args:
            db_manager: Gestor de base de datos configurado
        """
        self.db_manager = db_manager
        self.loaded_processes = {}  # Cache de procesos cargados
    
    def load_procesos_from_json(self, json_file_path: Path) -> Tuple[int, int]:
        """
        Carga procesos desde archivo JSON.
        
        Args:
            json_file_path: Ruta al archivo emp_procesos.json
            
        Returns:
            Tupla con (registros_cargados, registros_con_error)
        """
        logger.info(f"Iniciando carga de procesos desde: {json_file_path}")
        
        if not json_file_path.exists():
            raise FileNotFoundError(f"Archivo no encontrado: {json_file_path}")
        
        try:
            with open(json_file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
            
            if not isinstance(data, list):
                raise ValueError("El archivo JSON debe contener una lista de procesos")
            
            loaded_count = 0
            error_count = 0
            
            with self.db_manager.get_session() as session:
                for proceso_data in data:
                    try:
                        proceso = self._create_proceso_from_dict(proceso_data)
                        
                        # Verificar si ya existe
                        existing = session.query(Proceso).filter_by(
                            referencia_proceso=proceso.referencia_proceso
                        ).first()
                        
                        if existing:
                            logger.debug(f"Proceso ya existe: {proceso.referencia_proceso}")
                            self.loaded_processes[proceso.referencia_proceso] = existing
                            continue
                        
                        session.add(proceso)
                        session.flush()  # Para obtener el ID
                        
                        self.loaded_processes[proceso.referencia_proceso] = proceso
                        loaded_count += 1
                        
                        logger.debug(f"Proceso cargado: {proceso.referencia_proceso}")
                        
                    except Exception as e:
                        error_count += 1
                        logger.error(f"Error al cargar proceso {proceso_data.get('referencia_proceso', 'N/A')}: {e}")
                        session.rollback()
                        continue
                
                session.commit()
            
            logger.info(f"Carga de procesos completada: {loaded_count} exitosos, {error_count} con error")
            return loaded_count, error_count
            
        except Exception as e:
            logger.error(f"Error al cargar procesos: {e}")
            raise
    
    def load_contratos_from_json(self, json_file_path: Path) -> Tuple[int, int]:
        """
        Carga contratos desde archivo JSON.
        
        Args:
            json_file_path: Ruta al archivo emp_contratos.json
            
        Returns:
            Tupla con (registros_cargados, registros_con_error)
        """
        logger.info(f"Iniciando carga de contratos desde: {json_file_path}")
        
        if not json_file_path.exists():
            raise FileNotFoundError(f"Archivo no encontrado: {json_file_path}")
        
        try:
            with open(json_file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
            
            # El archivo emp_contratos.json tiene estructura con metadata
            if isinstance(data, dict) and 'contratos_encontrados' in data:
                contratos_data = data['contratos_encontrados']
            elif isinstance(data, list):
                contratos_data = data
            else:
                raise ValueError("Formato de archivo JSON no reconocido")
            
            loaded_count = 0
            error_count = 0
            
            with self.db_manager.get_session() as session:
                for contrato_data in contratos_data:
                    try:
                        contrato = self._create_contrato_from_dict(contrato_data, session)
                        
                        # Verificar si ya existe
                        existing = session.query(Contrato).filter_by(
                            id_contrato=contrato.id_contrato
                        ).first()
                        
                        if existing:
                            logger.debug(f"Contrato ya existe: {contrato.id_contrato}")
                            continue
                        
                        session.add(contrato)
                        loaded_count += 1
                        
                        logger.debug(f"Contrato cargado: {contrato.id_contrato}")
                        
                    except Exception as e:
                        error_count += 1
                        logger.error(f"Error al cargar contrato {contrato_data.get('id_contrato', 'N/A')}: {e}")
                        session.rollback()
                        continue
                
                session.commit()
            
            logger.info(f"Carga de contratos completada: {loaded_count} exitosos, {error_count} con error")
            return loaded_count, error_count
            
        except Exception as e:
            logger.error(f"Error al cargar contratos: {e}")
            raise
    
    def _create_proceso_from_dict(self, data: Dict[str, Any]) -> Proceso:
        """
        Crea un objeto Proceso desde un diccionario de datos.
        
        Args:
            data: Diccionario con datos del proceso
            
        Returns:
            Instancia de Proceso
        """
        # Limpiar y validar datos
        cleaned_data = self._clean_proceso_data(data)
        
        return Proceso(
            referencia_proceso=cleaned_data['referencia_proceso'],
            banco=cleaned_data['banco'],
            descripcion=cleaned_data.get('descripcion'),
            objeto=cleaned_data['objeto'],
            valor_total=cleaned_data['valor_total'],
            valor_plataforma=cleaned_data.get('valor_plataforma'),
            modalidad=cleaned_data.get('modalidad'),
            referencia_contrato=cleaned_data.get('referencia_contato'),  # Nota: typo en JSON original
            planeado=cleaned_data.get('planeado'),
            estado_proceso_secop=cleaned_data['estado_proceso_secop'],
            observaciones=cleaned_data.get('observaciones'),
            numero_contacto=cleaned_data.get('numero_contacto'),
            url_proceso=cleaned_data.get('urlProceso'),
            url_estado_real_proceso=cleaned_data.get('urlEstadoRealProceso'),
            archivo_origen=cleaned_data.get('archivo_origen'),
            fecha_procesamiento=cleaned_data.get('fecha_procesamiento')
        )
    
    def _create_contrato_from_dict(self, data: Dict[str, Any], session: Session) -> Contrato:
        """
        Crea un objeto Contrato desde un diccionario de datos.
        
        Args:
            data: Diccionario con datos del contrato
            session: Sesión de base de datos para buscar procesos relacionados
            
        Returns:
            Instancia de Contrato
        """
        # Limpiar y validar datos
        cleaned_data = self._clean_contrato_data(data)
        
        # Buscar proceso relacionado
        proceso_id = self._find_related_proceso(cleaned_data, session)
        
        return Contrato(
            id_contrato=cleaned_data['id_contrato'],
            referencia_del_contrato=cleaned_data['referencia_del_contrato'],
            proceso_de_compra=cleaned_data['proceso_de_compra'],
            proceso_id=proceso_id,
            nombre_entidad=cleaned_data['nombre_entidad'],
            nit_entidad=cleaned_data['nit_entidad'],
            departamento=cleaned_data.get('departamento'),
            ciudad=cleaned_data.get('ciudad'),
            localizacion=cleaned_data.get('localizaci_n'),  # Nota: encoding en JSON original
            orden=cleaned_data.get('orden'),
            sector=cleaned_data.get('sector'),
            rama=cleaned_data.get('rama'),
            entidad_centralizada=cleaned_data.get('entidad_centralizada'),
            codigo_entidad=cleaned_data.get('codigo_entidad'),
            estado_contrato=cleaned_data['estado_contrato'],
            codigo_de_categoria_principal=cleaned_data.get('codigo_de_categoria_principal'),
            descripcion_del_proceso=cleaned_data.get('descripcion_del_proceso'),
            objeto_del_contrato=cleaned_data['objeto_del_contrato'],
            tipo_de_contrato=cleaned_data.get('tipo_de_contrato'),
            modalidad_de_contratacion=cleaned_data.get('modalidad_de_contratacion'),
            justificacion_modalidad=cleaned_data.get('justificacion_modalidad_de'),
            fecha_de_firma=cleaned_data.get('fecha_de_firma'),
            fecha_de_inicio_del_contrato=cleaned_data.get('fecha_de_inicio_del_contrato'),
            fecha_de_fin_del_contrato=cleaned_data.get('fecha_de_fin_del_contrato'),
            duracion_del_contrato=cleaned_data.get('duraci_n_del_contrato'),
            fecha_inicio_liquidacion=cleaned_data.get('fecha_inicio_liquidacion'),
            fecha_fin_liquidacion=cleaned_data.get('fecha_fin_liquidacion'),
            documento_proveedor=cleaned_data.get('documento_proveedor'),
            tipodocproveedor=cleaned_data.get('tipodocproveedor'),
            proveedor_adjudicado=cleaned_data['proveedor_adjudicado'],
            es_grupo=cleaned_data.get('es_grupo'),
            es_pyme=cleaned_data.get('es_pyme'),
            codigo_proveedor=cleaned_data.get('codigo_proveedor'),
            nombre_representante_legal=cleaned_data.get('nombre_representante_legal'),
            nacionalidad_representante_legal=cleaned_data.get('nacionalidad_representante_legal'),
            domicilio_representante_legal=cleaned_data.get('domicilio_representante_legal'),
            tipo_identificacion_representante_legal=cleaned_data.get('tipo_de_identificaci_n_representante_legal'),
            identificacion_representante_legal=cleaned_data.get('identificaci_n_representante_legal'),
            genero_representante_legal=cleaned_data.get('g_nero_representante_legal'),
            valor_del_contrato=cleaned_data['valor_del_contrato'],
            valor_de_pago_adelantado=cleaned_data.get('valor_de_pago_adelantado', 0),
            valor_facturado=cleaned_data.get('valor_facturado', 0),
            valor_pendiente_de_pago=cleaned_data.get('valor_pendiente_de_pago', 0),
            valor_pagado=cleaned_data.get('valor_pagado', 0),
            valor_amortizado=cleaned_data.get('valor_amortizado', 0),
            valor_pendiente_de_ejecucion=cleaned_data.get('valor_pendiente_de_ejecucion', 0),
            presupuesto_general_nacion=cleaned_data.get('presupuesto_general_de_la_nacion_pgn', 0),
            sistema_general_participaciones=cleaned_data.get('sistema_general_de_participaciones', 0),
            sistema_general_regalias=cleaned_data.get('sistema_general_de_regal_as', 0),
            recursos_propios_alcaldias=cleaned_data.get('recursos_propios_alcald_as_gobernaciones_y_resguardos_ind_genas_', 0),
            recursos_de_credito=cleaned_data.get('recursos_de_credito', 0),
            recursos_propios=cleaned_data.get('recursos_propios', 0),
            estado_bpin=cleaned_data.get('estado_bpin'),
            anno_bpin=cleaned_data.get('anno_bpin'),
            bpin=cleaned_data.get('bpin'),
            saldo_cdp=cleaned_data.get('saldo_cdp'),
            saldo_vigencia=cleaned_data.get('saldo_vigencia'),
            condiciones_de_entrega=cleaned_data.get('condiciones_de_entrega'),
            habilita_pago_adelantado=cleaned_data.get('habilita_pago_adelantado'),
            liquidacion=cleaned_data.get('liquidaci_n'),
            obligacion_ambiental=cleaned_data.get('obligaci_n_ambiental'),
            obligaciones_postconsumo=cleaned_data.get('obligaciones_postconsumo'),
            reversion=cleaned_data.get('reversion'),
            origen_de_los_recursos=cleaned_data.get('origen_de_los_recursos'),
            destino_gasto=cleaned_data.get('destino_gasto'),
            el_contrato_puede_ser_prorrogado=cleaned_data.get('el_contrato_puede_ser_prorrogado'),
            fecha_notificacion_prorroga=cleaned_data.get('fecha_de_notificaci_n_de_prorrogaci_n'),
            espostconflicto=cleaned_data.get('espostconflicto'),
            dias_adicionados=cleaned_data.get('dias_adicionados'),
            puntos_del_acuerdo=cleaned_data.get('puntos_del_acuerdo'),
            pilares_del_acuerdo=cleaned_data.get('pilares_del_acuerdo'),
            nombre_del_banco=cleaned_data.get('nombre_del_banco'),
            tipo_de_cuenta=cleaned_data.get('tipo_de_cuenta'),
            numero_de_cuenta=cleaned_data.get('n_mero_de_cuenta'),
            nombre_ordenador_del_gasto=cleaned_data.get('nombre_ordenador_del_gasto'),
            tipo_documento_ordenador_gasto=cleaned_data.get('tipo_de_documento_ordenador_del_gasto'),
            numero_documento_ordenador_gasto=cleaned_data.get('n_mero_de_documento_ordenador_del_gasto'),
            nombre_supervisor=cleaned_data.get('nombre_supervisor'),
            tipo_documento_supervisor=cleaned_data.get('tipo_de_documento_supervisor'),
            numero_documento_supervisor=cleaned_data.get('n_mero_de_documento_supervisor'),
            nombre_ordenador_de_pago=cleaned_data.get('nombre_ordenador_de_pago'),
            tipo_documento_ordenador_pago=cleaned_data.get('tipo_de_documento_ordenador_de_pago'),
            numero_documento_ordenador_pago=cleaned_data.get('n_mero_de_documento_ordenador_de_pago'),
            urlproceso=cleaned_data.get('urlproceso'),
            dataset_source=cleaned_data.get('_dataset_source'),
            search_field=cleaned_data.get('_search_field'),
            referencia_buscada=cleaned_data.get('_referencia_buscada'),
            search_type=cleaned_data.get('_search_type'),
            total_campos=cleaned_data.get('_total_campos'),
            registro_origen=cleaned_data.get('_registro_origen')
        )
    
    def _clean_proceso_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Limpia y valida datos de proceso."""
        cleaned = {}
        
        # Campos obligatorios
        cleaned['referencia_proceso'] = str(data.get('referencia_proceso', '')).strip()
        if not cleaned['referencia_proceso']:
            raise ValueError("referencia_proceso es obligatorio")
        
        cleaned['banco'] = str(data.get('banco', '')).strip()
        if not cleaned['banco']:
            raise ValueError("banco es obligatorio")
        
        cleaned['objeto'] = str(data.get('objeto', '')).strip()
        if not cleaned['objeto']:
            raise ValueError("objeto es obligatorio")
        
        cleaned['estado_proceso_secop'] = str(data.get('estado_proceso_secop', '')).strip()
        if not cleaned['estado_proceso_secop']:
            raise ValueError("estado_proceso_secop es obligatorio")
        
        # Valores monetarios
        cleaned['valor_total'] = self._parse_decimal(data.get('valor_total'))
        if cleaned['valor_total'] is None or cleaned['valor_total'] < 0:
            raise ValueError("valor_total debe ser un número positivo")
        
        cleaned['valor_plataforma'] = self._parse_decimal(data.get('valor_plataforma'))
        
        # Campos opcionales
        cleaned['descripcion'] = self._clean_text(data.get('descripcion'))
        cleaned['modalidad'] = self._clean_text(data.get('modalidad'))
        cleaned['referencia_contato'] = self._clean_text(data.get('referencia_contato'))  # Typo en original
        cleaned['observaciones'] = self._clean_text(data.get('observaciones'))
        cleaned['numero_contacto'] = self._clean_text(data.get('numero_contacto'))
        cleaned['urlProceso'] = self._clean_text(data.get('urlProceso'))
        cleaned['urlEstadoRealProceso'] = self._clean_text(data.get('urlEstadoRealProceso'))
        cleaned['archivo_origen'] = self._clean_text(data.get('archivo_origen'))
        
        # Fechas
        cleaned['planeado'] = self._parse_date(data.get('planeado'))
        cleaned['fecha_procesamiento'] = self._parse_datetime(data.get('fecha_procesamiento'))
        
        return cleaned
    
    def _clean_contrato_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Limpia y valida datos de contrato."""
        cleaned = {}
        
        # Campos obligatorios
        required_fields = [
            'id_contrato', 'referencia_del_contrato', 'proceso_de_compra',
            'nombre_entidad', 'nit_entidad', 'estado_contrato', 
            'objeto_del_contrato', 'proveedor_adjudicado', 'valor_del_contrato'
        ]
        
        for field in required_fields:
            if field == 'valor_del_contrato':
                cleaned[field] = self._parse_decimal(data.get(field))
                if cleaned[field] is None or cleaned[field] < 0:
                    raise ValueError(f"{field} debe ser un número positivo")
            else:
                cleaned[field] = str(data.get(field, '')).strip()
                if not cleaned[field]:
                    raise ValueError(f"{field} es obligatorio")
        
        # Campos booleanos que necesitan conversión (nombres exactos del JSON)
        boolean_fields = [
            'es_grupo', 'es_pyme', 'habilita_pago_adelantado', 'liquidaci_n',
            'obligaci_n_ambiental', 'obligaciones_postconsumo', 'reversion',
            'el_contrato_puede_ser_prorrogado', 'espostconflicto'
        ]
        
        # Copiar y convertir todos los demás campos
        for key, value in data.items():
            if key not in cleaned:
                if key in boolean_fields:
                    # Convertir strings "Si"/"No" a booleanos
                    cleaned[key] = self._convert_to_boolean(value)
                else:
                    cleaned[key] = value
        
        return cleaned
    
    def _find_related_proceso(self, contrato_data: Dict[str, Any], session: Session) -> Optional[int]:
        """
        Busca el proceso relacionado con un contrato.
        
        Args:
            contrato_data: Datos del contrato
            session: Sesión de base de datos
            
        Returns:
            ID del proceso relacionado o None
        """
        # Buscar por referencia de proceso en los datos origen
        if '_registro_origen' in contrato_data:
            origen = contrato_data['_registro_origen']
            if isinstance(origen, dict) and 'referencia_proceso' in origen:
                ref_proceso = origen['referencia_proceso']
                proceso = session.query(Proceso).filter_by(referencia_proceso=ref_proceso).first()
                if proceso:
                    return proceso.id
        
        # Buscar por proceso de compra
        proceso_compra = contrato_data.get('proceso_de_compra')
        if proceso_compra:
            proceso = session.query(Proceso).filter_by(referencia_proceso=proceso_compra).first()
            if proceso:
                return proceso.id
        
        return None
    
    def _parse_decimal(self, value: Any) -> Optional[Decimal]:
        """Parsea un valor a Decimal."""
        if value is None or value == '' or value == 'No definido':
            return None
        
        try:
            if isinstance(value, str):
                # Limpiar formato de número
                cleaned = value.replace(',', '').replace('$', '').strip()
                return Decimal(cleaned) if cleaned else None
            return Decimal(str(value))
        except (InvalidOperation, ValueError):
            return None
    
    def _convert_to_boolean(self, value: Any) -> Optional[bool]:
        """Convierte valores a booleanos."""
        if value is None or value == '' or value == 'No definido':
            return None
        
        if isinstance(value, bool):
            return value
        
        if isinstance(value, str):
            value_lower = value.lower().strip()
            if value_lower in ['si', 'sí', 'yes', 'true', '1']:
                return True
            elif value_lower in ['no', 'false', '0']:
                return False
        
        return None
    
    def _parse_date(self, value: Any) -> Optional[date]:
        """Parsea un valor a date."""
        if value is None or value == '' or value == 'No definido':
            return None
        
        try:
            if isinstance(value, str):
                return datetime.strptime(value, '%Y-%m-%d').date()
            return value
        except (ValueError, TypeError):
            return None
    
    def _parse_datetime(self, value: Any) -> Optional[datetime]:
        """Parsea un valor a datetime."""
        if value is None or value == '' or value == 'No definido':
            return None
        
        try:
            if isinstance(value, str):
                return datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
            return value
        except (ValueError, TypeError):
            return None
    
    def _clean_text(self, value: Any) -> Optional[str]:
        """Limpia y valida texto."""
        if value is None or value == '' or value == 'No definido':
            return None
        
        cleaned = str(value).strip()
        return cleaned if cleaned else None
    
    def _parse_boolean(self, value: Any) -> Optional[bool]:
        """Parsea un valor a boolean."""
        if value is None or value == '' or value == 'No definido':
            return None
        
        if isinstance(value, bool):
            return value
        
        if isinstance(value, str):
            value_lower = value.lower().strip()
            if value_lower in ('true', 'si', 'sí', 'yes', '1'):
                return True
            elif value_lower in ('false', 'no', '0'):
                return False
        
        return None


def load_all_data(db_manager: DatabaseManager, contratos_file: Path, procesos_file: Path) -> Dict[str, Any]:
    """
    Carga todos los datos desde archivos JSON.
    
    Args:
        db_manager: Gestor de base de datos
        contratos_file: Archivo de contratos
        procesos_file: Archivo de procesos
        
    Returns:
        Diccionario con estadísticas de carga
    """
    loader = DataLoader(db_manager)
    
    # Cargar procesos primero (para establecer relaciones)
    procesos_loaded, procesos_errors = loader.load_procesos_from_json(procesos_file)
    
    # Cargar contratos
    contratos_loaded, contratos_errors = loader.load_contratos_from_json(contratos_file)
    
    return {
        'procesos': {
            'loaded': procesos_loaded,
            'errors': procesos_errors
        },
        'contratos': {
            'loaded': contratos_loaded,
            'errors': contratos_errors
        },
        'total_loaded': procesos_loaded + contratos_loaded,
        'total_errors': procesos_errors + contratos_errors
    }