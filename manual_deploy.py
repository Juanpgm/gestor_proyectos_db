#!/usr/bin/env python3
"""
🚀 Script Manual de Deployment para Railway
==========================================

Este script puede ejecutarse manualmente para realizar el deployment
de la base de datos y carga de datos en Railway.

Uso:
    python manual_deploy.py

Variables de entorno requeridas en Railway:
    - DATABASE_URL (proporcionado automáticamente por Railway PostgreSQL)
    - APP_ENV=production
    - LOG_LEVEL=INFO
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

def check_environment():
    """Verificar que el entorno esté configurado."""
    logger.info("🔍 Verificando entorno...")
    
    # Verificar Railway
    is_railway = (
        os.environ.get("RAILWAY_ENVIRONMENT") is not None or 
        os.environ.get("DATABASE_URL") is not None
    )
    
    if is_railway:
        logger.info("🚂 Entorno Railway detectado")
        
        if not os.environ.get("DATABASE_URL"):
            logger.error("❌ DATABASE_URL no configurada")
            logger.info("💡 Agrega PostgreSQL service en Railway dashboard")
            return False
    else:
        logger.info("🏠 Entorno local detectado")
        
        # Verificar variables locales
        required_vars = ["DB_HOST", "DB_NAME", "DB_USER", "DB_PASSWORD"]
        missing_vars = [var for var in required_vars if not os.environ.get(var)]
        
        if missing_vars:
            logger.warning(f"⚠️ Variables faltantes: {', '.join(missing_vars)}")
            logger.info("💡 Configura las variables en .env o como variables de entorno")
    
    # Verificar archivos de datos
    data_dir = Path("app_outputs")
    if not data_dir.exists():
        logger.error(f"❌ Directorio de datos no encontrado: {data_dir}")
        logger.info("💡 Asegúrate de que los archivos JSON estén en app_outputs/")
        return False
    
    logger.info("✅ Entorno verificado correctamente")
    return True

def main():
    """Función principal del deployment manual."""
    logger.info("=" * 60)
    logger.info("🚀 DEPLOYMENT MANUAL RAILWAY - GESTOR PROYECTOS DB")
    logger.info("=" * 60)
    
    # Verificar entorno
    if not check_environment():
        logger.error("❌ Verificación de entorno falló")
        sys.exit(1)
    
    try:
        # Importar y ejecutar deployment
        logger.info("📦 Importando script de deployment...")
        from railway_db_deploy import RailwayDatabaseDeployment
        
        logger.info("🏗️ Creando instancia de deployment...")
        deployment = RailwayDatabaseDeployment()
        
        logger.info("🚀 Ejecutando deployment...")
        success = deployment.run_deployment()
        
        if success:
            logger.info("=" * 60)
            logger.info("🎉 DEPLOYMENT COMPLETADO EXITOSAMENTE")
            logger.info("✅ Base de datos inicializada y datos cargados")
            logger.info("🌐 Aplicación lista para uso")
            logger.info("=" * 60)
            sys.exit(0)
        else:
            logger.error("=" * 60)
            logger.error("❌ DEPLOYMENT FALLÓ")
            logger.error("💡 Revisa los logs anteriores para detalles")
            logger.error("=" * 60)
            sys.exit(1)
            
    except ImportError as e:
        logger.error(f"❌ Error importando módulos: {str(e)}")
        logger.info("💡 Asegúrate de que todos los archivos estén presentes")
        sys.exit(1)
        
    except Exception as e:
        logger.error(f"❌ Error crítico durante deployment: {str(e)}")
        logger.info("💡 Revisa la configuración y conexión a base de datos")
        sys.exit(1)

if __name__ == "__main__":
    main()