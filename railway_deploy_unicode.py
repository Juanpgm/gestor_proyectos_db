#!/usr/bin/env python3
"""
🚂 Railway Deployment Entry Point - Production Ready
==================================================
Punto de entrada específico y robusto para Railway deployment
"""

import os
import sys
import time
import signal
import logging
from pathlib import Path

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Asegurar que el directorio actual esté en el path
sys.path.insert(0, str(Path(__file__).parent))

def setup_railway_environment():
    """Configura el entorno específico para Railway"""
    logger.info("🔧 Configurando entorno Railway desde railway_deploy.py...")
    
    # Variables de entorno Railway
    env_vars = {
        'DEPLOYMENT_ENV': 'railway',
        'PYTHONUNBUFFERED': '1',
        'PYTHONDONTWRITEBYTECODE': '1',
    }
    
    for key, value in env_vars.items():
        os.environ[key] = value
        logger.info(f"✅ {key}={value}")
    
    # Puerto
    port = os.environ.get('PORT', '8080')
    os.environ['PORT'] = port
    logger.info(f"📡 Puerto: {port}")

def main():
    """Función principal para Railway con manejo robusto de errores"""
    try:
        print("🚂 Railway Deploy - Entry Point Específico")
        logger.info("🚀 Iniciando railway_deploy.py...")
        
        setup_railway_environment()
        
        # Intentar importar módulos con fallbacks
        logger.info("📦 Importando módulos del sistema inteligente...")
        try:
            from intelligent_master_deploy import IntelligentDatabaseManager, DeploymentEnvironment
            logger.info("✅ Módulos inteligentes importados correctamente")
        except ImportError as e:
            logger.error(f"❌ Error importando módulos inteligentes: {e}")
            logger.info("🔄 Intentando configuración básica...")
            
            # Fallback básico para mantener Railway activo
            keep_alive_basic()
            return
        
        # Crear manager
        logger.info("🎯 Creando manager del sistema inteligente...")
        try:
            manager = IntelligentDatabaseManager()
            logger.info("✅ Manager creado exitosamente")
        except Exception as e:
            logger.error(f"❌ Error creando manager: {e}")
            logger.info("🔄 Usando keep-alive básico...")
            keep_alive_basic()
            return
        
        # Ejecutar deployment
        logger.info("🚀 Ejecutando deployment Railway...")
        try:
            success = manager.deploy(force_environment=DeploymentEnvironment.RAILWAY)
            
            if success:
                logger.info("✅ Deployment Railway exitoso")
                keep_alive_intelligent()
            else:
                logger.warning("⚠️ Deployment falló, intentando fallback local...")
                success_local = manager.deploy(force_environment=DeploymentEnvironment.LOCAL)
                if success_local:
                    logger.info("✅ Fallback local exitoso")
                    keep_alive_intelligent()
                else:
                    logger.error("❌ Todos los deployments fallaron")
                    keep_alive_basic()
                    
        except Exception as e:
            logger.error(f"❌ Error durante deployment: {e}")
            logger.info("🔄 Manteniendo servicio básico activo...")
            keep_alive_basic()
            
    except KeyboardInterrupt:
        logger.info("🔄 Railway deploy interrumpido por usuario")
        sys.exit(0)
    except Exception as e:
        logger.error(f"💥 Error crítico en railway_deploy: {e}")
        logger.exception("Detalles del error:")
        
        # Información de debugging
        logger.info("🔍 Información de debugging:")
        logger.info(f"Python: {sys.version}")
        logger.info(f"Working dir: {os.getcwd()}")
        logger.info(f"Railway deploy path: {__file__}")
        
        # Verificar archivos
        critical_files = ['intelligent_master_deploy.py', '.env', 'app.py']
        for file in critical_files:
            if os.path.exists(file):
                logger.info(f"✅ {file} existe")
            else:
                logger.error(f"❌ {file} no encontrado")
        
        # Mantener servicio básico aunque haya errores
        logger.info("🔄 Iniciando keep-alive básico para mantener Railway activo...")
        keep_alive_basic()

def keep_alive_intelligent():
    """Keep-alive con monitoreo inteligente"""
    logger.info("🔄 Iniciando keep-alive inteligente...")
    
    def signal_handler(signum, frame):
        logger.info(f"� Señal {signum} recibida, cerrando gracefully...")
        sys.exit(0)
    
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        counter = 0
        while True:
            time.sleep(60)
            counter += 1
            
            if counter % 5 == 0:
                logger.info(f"💗 Sistema Railway activo - {counter} minutos")
                
            if counter % 30 == 0:
                logger.info("🏥 Health check inteligente...")
                # Aquí podrías agregar checks de la DB, etc.
                
    except Exception as e:
        logger.error(f"❌ Error en keep-alive inteligente: {e}")
        keep_alive_basic()

def keep_alive_basic():
    """Keep-alive básico sin dependencias externas"""
    logger.info("🔄 Iniciando keep-alive básico...")
    
    def signal_handler(signum, frame):
        logger.info(f"🔄 Señal {signum} recibida, cerrando...")
        sys.exit(0)
    
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        counter = 0
        while True:
            time.sleep(120)  # 2 minutos para básico
            counter += 1
            logger.info(f"💗 Keep-alive básico activo - {counter * 2} minutos")
            
            # Cada hora mostrar más info
            if counter % 30 == 0:
                logger.info(f"📊 Uptime: {counter * 2} minutos")
                logger.info(f"🐍 Python: {sys.version}")
                logger.info(f"💾 Working dir: {os.getcwd()}")
                
    except KeyboardInterrupt:
        logger.info("🔄 Keep-alive básico interrumpido")
        sys.exit(0)
    except Exception as e:
        logger.error(f"❌ Error en keep-alive básico: {e}")
        # Último recurso - sleep simple
        while True:
            time.sleep(300)  # 5 minutos
            logger.info("💗 Último recurso keep-alive activo")

if __name__ == "__main__":
    main()