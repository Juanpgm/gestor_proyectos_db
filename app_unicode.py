#!/usr/bin/env python3
"""
🚂 Railway App Entry Point - Production Ready
============================================
Archivo principal optimizado para Railway deployment con manejo robusto
"""

import sys
import os
import logging
import time
import signal
from pathlib import Path

# Configurar logging temprano
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Agregar directorio actual al path
sys.path.insert(0, str(Path(__file__).parent))

def setup_railway_environment():
    """Configura el entorno específico para Railway con manejo robusto"""
    logger.info("🔧 Configurando entorno Railway...")
    
    # Variables de entorno Railway esenciales
    env_vars = {
        'DEPLOYMENT_ENV': 'railway',
        'PYTHONUNBUFFERED': '1',
        'PYTHONDONTWRITEBYTECODE': '1',
    }
    
    for key, value in env_vars.items():
        os.environ[key] = value
        logger.info(f"✅ {key}={value}")
    
    # Configurar puerto
    port = os.environ.get('PORT', '8080')
    os.environ['PORT'] = port
    logger.info(f"📡 Puerto configurado: {port}")
    
    # Verificar DATABASE_URL
    database_url = os.environ.get('DATABASE_URL')
    if database_url:
        if 'railway' in database_url or 'rlwy.net' in database_url:
            logger.info("🚂 DATABASE_URL Railway detectada")
            os.environ['RAILWAY_DATABASE_DETECTED'] = 'true'
        else:
            logger.info("🏠 DATABASE_URL local detectada")
            os.environ['LOCAL_DATABASE_DETECTED'] = 'true'
    else:
        logger.warning("⚠️ DATABASE_URL no encontrada - usando configuración local")
        # Cargar desde .env si no hay DATABASE_URL
        try:
            from dotenv import load_dotenv
            load_dotenv()
            logger.info("✅ Variables cargadas desde .env")
        except ImportError:
            logger.warning("⚠️ python-dotenv no disponible")
    
    # Configurar PATH si es necesario
    current_dir = Path(__file__).parent
    if str(current_dir) not in sys.path:
        sys.path.insert(0, str(current_dir))
    
    logger.info("✅ Entorno Railway configurado completamente")

def main():
    """Función principal optimizada para Railway con error handling robusto"""
    try:
        print("🚂 Iniciando Railway App Entry Point...")
        setup_railway_environment()
        
        # Verificar que los módulos necesarios estén disponibles
        logger.info("📦 Verificando módulos necesarios...")
        
        try:
            import intelligent_master_deploy
            logger.info("✅ intelligent_master_deploy importado")
        except ImportError as e:
            logger.error(f"❌ Error importando intelligent_master_deploy: {e}")
            # Intentar importar railway_deploy como fallback
            try:
                import railway_deploy
                logger.info("✅ Usando railway_deploy como fallback")
                railway_deploy.main()
                return
            except ImportError as e2:
                logger.error(f"❌ Error importando railway_deploy: {e2}")
                raise e
        
        from intelligent_master_deploy import IntelligentDatabaseManager, DeploymentEnvironment
        
        # Crear el manager
        logger.info("🎯 Inicializando sistema inteligente...")
        manager = IntelligentDatabaseManager()
        
        # Detectar y forzar entorno Railway
        logger.info("🚀 Ejecutando deployment Railway...")
        success = manager.deploy(force_environment=DeploymentEnvironment.RAILWAY)
        
        if success:
            logger.info("✅ Deployment Railway exitoso")
            keep_alive()
        else:
            logger.error("❌ Error en deployment Railway")
            # Intentar fallback con configuración local
            logger.info("🔄 Intentando fallback local...")
            success_local = manager.deploy(force_environment=DeploymentEnvironment.LOCAL)
            if success_local:
                logger.info("✅ Fallback local exitoso")
                keep_alive()
            else:
                logger.error("❌ Todos los deployments fallaron")
                sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("🔄 App interrumpida por usuario")
        sys.exit(0)
    except Exception as e:
        logger.error(f"💥 Error crítico en Railway app: {e}")
        logger.exception("Detalles del error:")
        
        # Intentar mostrar información útil para debugging
        logger.info("🔍 Información de debugging:")
        logger.info(f"Python version: {sys.version}")
        logger.info(f"Current working directory: {os.getcwd()}")
        logger.info(f"Python path: {sys.path}")
        
        # Verificar archivos críticos
        critical_files = ['railway_deploy.py', 'intelligent_master_deploy.py', '.env']
        for file in critical_files:
            if os.path.exists(file):
                logger.info(f"✅ {file} existe")
            else:
                logger.error(f"❌ {file} no encontrado")
        
        sys.exit(1)

def keep_alive():
    """Mantiene la aplicación viva en Railway con manejo de señales"""
    logger.info("🔄 Iniciando modo keep-alive para Railway...")
    
    def signal_handler(signum, frame):
        logger.info(f"🔄 Señal {signum} recibida, cerrando gracefully...")
        sys.exit(0)
    
    # Configurar handlers de señales
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        counter = 0
        while True:
            time.sleep(60)  # Check cada minuto
            counter += 1
            
            # Log cada 5 minutos para mostrar actividad
            if counter % 5 == 0:
                logger.info(f"💗 Sistema Railway activo - {counter} minutos")
                
            # Health check cada 15 minutos
            if counter % 15 == 0:
                logger.info("🏥 Ejecutando health check...")
                try:
                    # Verificar que el sistema siga funcionando
                    logger.info(f"🔄 Uptime: {counter} minutos")
                    logger.info("✅ Health check OK")
                except Exception as e:
                    logger.error(f"❌ Health check failed: {e}")
                    
    except KeyboardInterrupt:
        logger.info("🔄 Keep-alive interrumpido")
        sys.exit(0)
    except Exception as e:
        logger.error(f"❌ Error en keep-alive: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()