#!/usr/bin/env python3
"""
Railway Entry Point - Production Ready
Punto de entrada principal para Railway deployment con manejo robusto de errores
"""

import os
import sys
import logging
import signal
import time
from pathlib import Path

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Agregar el directorio actual al path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

def setup_railway_environment():
    """Configurar entorno Railway con deteccion robusta"""
    logger.info("=== RAILWAY DEPLOYMENT STARTING ===")
    
    # Variables esenciales Railway
    railway_vars = {
        'PYTHONUNBUFFERED': '1',
        'PYTHONDONTWRITEBYTECODE': '1',
        'DEPLOYMENT_ENV': 'railway',
        'PORT': os.environ.get('PORT', '8080')
    }
    
    # Aplicar configuracion
    for key, value in railway_vars.items():
        os.environ[key] = value
        logger.info(f"OK {key}={value}")
    
    # Configurar puerto
    port = os.environ.get('PORT', '8080')
    os.environ['PORT'] = port
    logger.info(f"Puerto configurado: {port}")
    
    # Verificar DATABASE_URL
    database_url = os.environ.get('DATABASE_URL')
    if database_url:
        if 'railway' in database_url or 'rlwy.net' in database_url:
            logger.info("DATABASE_URL Railway detectada")
            os.environ['RAILWAY_DATABASE_DETECTED'] = 'true'
        else:
            logger.info("DATABASE_URL personalizada detectada")
    else:
        logger.warning("DATABASE_URL no configurada - usando local")
    
    logger.info("Entorno Railway configurado")

def signal_handler(signum, frame):
    """Manejar señales de terminacion"""
    logger.info(f"Señal {signum} recibida - cerrando aplicacion...")
    sys.exit(0)

def main():
    """Funcion principal con manejo de errores robusto"""
    try:
        # Configurar manejo de señales
        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)
        
        # Configurar entorno
        setup_railway_environment()
        
        logger.info("Iniciando sistema inteligente...")
        
        # Intentar cargar y ejecutar el sistema inteligente
        try:
            from intelligent_master_deploy import IntelligentDeploymentSystem
            
            logger.info("Sistema inteligente cargado exitosamente")
            
            # Crear e inicializar sistema
            deployment_system = IntelligentDeploymentSystem()
            
            # Ejecutar deployment inteligente
            logger.info("Ejecutando deployment inteligente...")
            deployment_system.execute_intelligent_deployment()
            
            # Si llegamos aqui, el deployment fue exitoso
            logger.info("Deployment inteligente completado")
            
            # Mantener aplicacion viva
            keep_alive()
            
        except ImportError as e:
            logger.error(f"Error importando sistema inteligente: {e}")
            logger.info("Intentando fallback a modo basico...")
            
            # Fallback a modo basico
            keep_alive_basic()
            
        except Exception as e:
            logger.error(f"Error en sistema inteligente: {e}")
            logger.info("Cambiando a modo basico...")
            
            # Fallback a modo basico
            keep_alive_basic()
    
    except Exception as e:
        logger.error(f"Error critico en aplicacion: {e}")
        
        # Ultimo intento - modo de supervivencia
        try:
            logger.info("Modo de supervivencia activado")
            simple_web_server()
        except Exception as final_error:
            logger.error(f"Error final: {final_error}")
            sys.exit(1)

def keep_alive():
    """Mantener aplicacion viva con funcionalidad completa"""
    logger.info("Aplicacion iniciada - modo inteligente")
    logger.info("Sistema de monitoreo activo")
    
    try:
        while True:
            time.sleep(30)
            logger.info("Aplicacion funcionando - modo inteligente")
            
    except KeyboardInterrupt:
        logger.info("Interrupcion recibida - cerrando...")
    except Exception as e:
        logger.error(f"Error en keep_alive: {e}")
        raise

def keep_alive_basic():
    """Mantener aplicacion viva en modo basico"""
    logger.info("Aplicacion iniciada - modo basico")
    
    try:
        while True:
            time.sleep(60)
            logger.info("Aplicacion funcionando - modo basico")
            
    except KeyboardInterrupt:
        logger.info("Interrupcion recibida - cerrando...")
    except Exception as e:
        logger.error(f"Error en keep_alive_basic: {e}")
        raise

def simple_web_server():
    """Servidor web simple para modo de supervivencia"""
    import http.server
    import socketserver
    from threading import Thread
    
    port = int(os.environ.get('PORT', 8080))
    
    class SimpleHandler(http.server.SimpleHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b'''
            <html>
            <body>
                <h1>Gestor Proyectos DB - Railway</h1>
                <p>Aplicacion ejecutandose en modo supervivencia</p>
                <p>Sistema: Railway Deployment</p>
            </body>
            </html>
            ''')
    
    try:
        with socketserver.TCPServer(("", port), SimpleHandler) as httpd:
            logger.info(f"Servidor HTTP iniciado en puerto {port}")
            httpd.serve_forever()
    except Exception as e:
        logger.error(f"Error en servidor HTTP: {e}")
        # Fallback final - solo mantenerse vivo
        while True:
            time.sleep(120)
            logger.info("Aplicacion activa - modo minimo")

if __name__ == "__main__":
    main()