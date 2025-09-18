#!/usr/bin/env python3
"""
Main Entry Point - Sistema Gestor Proyectos DB
Entry point principal para el sistema de gestion de base de datos
"""

import os
import sys
import logging
from pathlib import Path

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Agregar directorio actual al path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

def detect_environment():
    """Detectar entorno de ejecucion"""
    if os.environ.get('RAILWAY_ENVIRONMENT'):
        return 'railway'
    elif os.environ.get('PORT'):
        return 'cloud'
    else:
        return 'local'

def main():
    """Funcion principal con deteccion automatica de entorno"""
    try:
        environment = detect_environment()
        logger.info(f"Entorno detectado: {environment}")
        
        if environment == 'railway':
            # Ejecutar entry point Railway
            logger.info("Ejecutando entry point Railway...")
            from app import main as railway_main
            railway_main()
            
        elif environment == 'cloud':
            # Ejecutar entry point generico para cloud
            logger.info("Ejecutando entry point cloud...")
            from railway_deploy import main as cloud_main
            cloud_main()
            
        else:
            # Ejecutar deployment local
            logger.info("Ejecutando deployment local...")
            from intelligent_local_deploy import main as local_main
            local_main()
            
    except ImportError as e:
        logger.error(f"Error importando modulos: {e}")
        logger.info("Ejecutando modo basico...")
        basic_mode()
        
    except Exception as e:
        logger.error(f"Error en main: {e}")
        logger.info("Ejecutando modo de emergencia...")
        emergency_mode()

def basic_mode():
    """Modo basico cuando fallan las importaciones"""
    logger.info("Modo basico activado")
    
    try:
        # Intentar cargar sistema inteligente
        from intelligent_master_deploy import IntelligentDeploymentSystem
        
        system = IntelligentDeploymentSystem()
        system.execute_intelligent_deployment()
        
        # Mantener vivo
        import time
        while True:
            time.sleep(60)
            logger.info("Sistema activo - modo basico")
            
    except Exception as e:
        logger.error(f"Error en modo basico: {e}")
        emergency_mode()

def emergency_mode():
    """Modo de emergencia minimo"""
    logger.info("Modo de emergencia activado")
    
    import time
    try:
        while True:
            time.sleep(120)
            logger.info("Sistema activo - modo emergencia")
    except KeyboardInterrupt:
        logger.info("Cerrando sistema...")

if __name__ == "__main__":
    main()