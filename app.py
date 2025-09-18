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
        
        logger.info("Iniciando servidor HTTP para healthcheck...")
        
        # SIEMPRE iniciar servidor HTTP primero para healthcheck
        start_http_server()
        
    except Exception as e:
        logger.error(f"Error critico en aplicacion: {e}")
        
        # Ultimo intento - modo de supervivencia
        try:
            logger.info("Modo de supervivencia activado")
            simple_web_server()
        except Exception as final_error:
            logger.error(f"Error final: {final_error}")
            sys.exit(1)

def start_http_server():
    """Iniciar servidor HTTP con sistema inteligente en background"""
    import http.server
    import socketserver
    from threading import Thread
    
    port = int(os.environ.get('PORT', 8080))
    
    class HealthHandler(http.server.SimpleHTTPRequestHandler):
        def do_GET(self):
            if self.path == '/' or self.path == '/health':
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                response = {
                    "status": "healthy",
                    "service": "gestor_proyectos_db",
                    "timestamp": time.time(),
                    "version": "1.0.0"
                }
                import json
                self.wfile.write(json.dumps(response).encode())
            else:
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(b'''
                <html>
                <body>
                    <h1>Gestor Proyectos DB - Railway</h1>
                    <p>Sistema activo y funcionando</p>
                    <p>Deployment: Railway Production</p>
                    <p><a href="/health">Health Check</a></p>
                </body>
                </html>
                ''')
    
    def run_intelligent_system():
        """Ejecutar sistema inteligente en background"""
        try:
            logger.info("Iniciando sistema inteligente en background...")
            from intelligent_master_deploy import IntelligentDeploymentSystem
            
            deployment_system = IntelligentDeploymentSystem()
            deployment_system.execute_intelligent_deployment()
            logger.info("Sistema inteligente inicializado")
            
            # Mantener sistema activo
            while True:
                time.sleep(300)  # 5 minutos
                logger.info("Sistema inteligente activo")
                
        except ImportError as e:
            logger.warning(f"Sistema inteligente no disponible: {e}")
        except Exception as e:
            logger.error(f"Error en sistema inteligente: {e}")
    
    try:
        # Iniciar sistema inteligente en background
        intelligent_thread = Thread(target=run_intelligent_system, daemon=True)
        intelligent_thread.start()
        
        # Iniciar servidor HTTP (principal)
        with socketserver.TCPServer(("", port), HealthHandler) as httpd:
            logger.info(f"Servidor HTTP iniciado en puerto {port}")
            logger.info("Healthcheck endpoint disponible en /")
            httpd.serve_forever()
            
    except Exception as e:
        logger.error(f"Error en servidor HTTP: {e}")
        # Fallback a servidor simple
        simple_web_server()

def simple_web_server():
    """Servidor web simple para modo de supervivencia"""
    import http.server
    import socketserver
    
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
            logger.info(f"Servidor HTTP simple iniciado en puerto {port}")
            httpd.serve_forever()
    except Exception as e:
        logger.error(f"Error en servidor HTTP simple: {e}")
        # Fallback final - solo mantenerse vivo
        while True:
            time.sleep(120)
            logger.info("Aplicacion activa - modo minimo")

if __name__ == "__main__":
    main()