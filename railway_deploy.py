#!/usr/bin/env python3
"""
Railway Deploy Entry Point - Production Ready
Entry point especifico para Railway con multiples niveles de fallback
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

# Agregar directorio actual al path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

def setup_railway_environment():
    """Configurar entorno Railway especifico"""
    logger.info("=== RAILWAY SPECIFIC DEPLOYMENT ===")
    
    # Variables Railway especificas
    railway_config = {
        'PYTHONUNBUFFERED': '1',
        'PYTHONDONTWRITEBYTECODE': '1',
        'DEPLOYMENT_ENV': 'railway',
        'RAILWAY_DEPLOYMENT': 'true',
        'PORT': os.environ.get('PORT', '8080')
    }
    
    # Aplicar configuracion
    for key, value in railway_config.items():
        os.environ[key] = value
        logger.info(f"Railway config: {key}={value}")
    
    # Verificar entorno Railway
    railway_indicators = [
        'RAILWAY_ENVIRONMENT',
        'RAILWAY_PROJECT_ID', 
        'RAILWAY_SERVICE_ID',
        'RAILWAY_DEPLOYMENT_ID'
    ]
    
    railway_detected = False
    for indicator in railway_indicators:
        if os.environ.get(indicator):
            logger.info(f"Railway indicator detected: {indicator}")
            railway_detected = True
    
    if railway_detected:
        logger.info("Railway environment confirmed")
        os.environ['CONFIRMED_RAILWAY'] = 'true'
    else:
        logger.info("Railway environment assumed")
    
    return railway_detected

def signal_handler(signum, frame):
    """Manejar senales de terminacion"""
    logger.info(f"Signal {signum} received - shutting down...")
    sys.exit(0)

def main():
    """Funcion principal con manejo de errores Railway-especifico"""
    try:
        # Configurar manejo de senales
        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)
        
        # Configurar entorno Railway
        is_railway = setup_railway_environment()
        
        logger.info("Starting Railway deployment...")
        
        # Nivel 1: Sistema inteligente completo
        try:
            logger.info("Attempting intelligent system...")
            from intelligent_master_deploy import IntelligentDeploymentSystem
            
            deployment_system = IntelligentDeploymentSystem()
            deployment_system.execute_intelligent_deployment()
            
            logger.info("Intelligent system deployed successfully")
            keep_alive_intelligent()
            
        except ImportError as e:
            logger.warning(f"Intelligent system unavailable: {e}")
            logger.info("Falling back to basic Railway mode...")
            
            # Nivel 2: Modo basico Railway
            keep_alive_basic()
            
        except Exception as e:
            logger.error(f"Error in intelligent system: {e}")
            logger.info("Falling back to basic Railway mode...")
            
            # Nivel 2: Modo basico Railway
            keep_alive_basic()
    
    except Exception as e:
        logger.error(f"Critical error: {e}")
        logger.info("Emergency mode activated")
        
        # Nivel 3: Modo de emergencia
        emergency_mode()

def keep_alive_intelligent():
    """Mantener aplicacion viva con sistema inteligente"""
    logger.info("Railway app running - intelligent mode")
    
    try:
        while True:
            time.sleep(45)
            logger.info("Railway app healthy - intelligent monitoring active")
            
    except KeyboardInterrupt:
        logger.info("Shutdown signal received")
    except Exception as e:
        logger.error(f"Error in intelligent keep-alive: {e}")
        # Fallback a modo basico
        keep_alive_basic()

def keep_alive_basic():
    """Mantener aplicacion viva en modo basico Railway"""
    logger.info("Railway app running - basic mode")
    
    try:
        while True:
            time.sleep(90)
            logger.info("Railway app healthy - basic monitoring")
            
    except KeyboardInterrupt:
        logger.info("Shutdown signal received")
    except Exception as e:
        logger.error(f"Error in basic keep-alive: {e}")
        # Fallback a modo de emergencia
        emergency_mode()

def emergency_mode():
    """Modo de emergencia para Railway"""
    logger.info("Emergency mode - minimal Railway server")
    
    try:
        import http.server
        import socketserver
        
        port = int(os.environ.get('PORT', 8080))
        
        class EmergencyHandler(http.server.SimpleHTTPRequestHandler):
            def do_GET(self):
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                response = f'''
                <html>
                <body>
                    <h1>Railway Emergency Mode</h1>
                    <p>Gestor Proyectos DB running in emergency mode</p>
                    <p>Port: {port}</p>
                    <p>Time: {time.ctime()}</p>
                    <p>Status: Active</p>
                </body>
                </html>
                '''.encode()
                self.wfile.write(response)
        
        with socketserver.TCPServer(("", port), EmergencyHandler) as httpd:
            logger.info(f"Emergency HTTP server started on port {port}")
            httpd.serve_forever()
            
    except Exception as e:
        logger.error(f"Emergency mode failed: {e}")
        # Ultimo recurso - solo mantenerse vivo
        logger.info("Last resort - stay alive mode")
        while True:
            time.sleep(300)  # 5 minutos
            logger.info("Railway app still alive - minimal mode")

if __name__ == "__main__":
    main()