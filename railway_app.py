"""
Aplicación principal para despliegue en Railway.

Esta aplicación se ejecuta en Railway y permite:
- Inicializar la base de datos PostgreSQL automáticamente
- Cargar datos directamente usando los scripts existentes
- Proporcionar endpoints de monitoreo básicos (sin APIs de datos)
"""

import os
import sys
import json
import logging
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler

# Agregar el directorio src al path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from railway_db_deploy import RailwayDatabaseDeployment

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class RailwayApp:
    """Aplicación simplificada para Railway - Solo deployment y monitoreo."""
    
    def __init__(self):
        """Inicializar la aplicación."""
        self.deployment = None
        self.deployment_completed = False
    
    def run_deployment(self) -> bool:
        """Ejecutar el deployment de base de datos."""
        try:
            logger.info("🚀 Iniciando deployment en Railway...")
            
            self.deployment = RailwayDatabaseDeployment()
            self.deployment_completed = self.deployment.run_deployment()
            
            if self.deployment_completed:
                logger.info("✅ Deployment completado exitosamente")
            else:
                logger.error("❌ Deployment falló")
            
            return self.deployment_completed
            
        except Exception as e:
            logger.error(f"❌ Error durante deployment: {str(e)}")
            return False
    
    def get_status(self) -> dict:
        """Obtener estado de la aplicación y base de datos."""
        try:
            if not self.deployment_completed:
                return {
                    "status": "initializing",
                    "message": "Deployment en progreso o falló",
                    "database": "unknown"
                }
            
            # Si el deployment está completo, verificar estado actual
            if self.deployment and self.deployment.db_manager:
                if self.deployment.db_manager.test_connection():
                    # Obtener resumen de tablas
                    tables_info = self.deployment.db_manager.get_tables_summary()
                    
                    return {
                        "status": "healthy",
                        "database": "connected",
                        "deployment": "completed",
                        "tables": tables_info or {},
                        "total_records": sum(tables_info.values()) if tables_info else 0
                    }
                else:
                    return {
                        "status": "unhealthy", 
                        "database": "disconnected",
                        "deployment": "completed"
                    }
            
            return {
                "status": "unknown",
                "database": "unknown",
                "deployment": "completed" if self.deployment_completed else "failed"
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "database": "error"
            }
    
class StatusHandler(BaseHTTPRequestHandler):
    """Manejador de requests HTTP para monitoreo."""
    
    def do_GET(self):
        """Manejar requests GET."""
        if self.path == "/":
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            html = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Gestor Proyectos DB - Railway</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 40px; }
                    .header { color: #2563eb; }
                    .status { margin: 20px 0; padding: 20px; background: #f8fafc; border-radius: 8px; }
                    .success { border-left: 4px solid #10b981; }
                    .error { border-left: 4px solid #ef4444; }
                    .warning { border-left: 4px solid #f59e0b; }
                    a { color: #2563eb; text-decoration: none; }
                    a:hover { text-decoration: underline; }
                </style>
            </head>
            <body>
                <h1 class="header">🚂 Gestor Proyectos DB</h1>
                <p>Sistema de gestión de proyectos ejecutándose en Railway</p>
                
                <div class="status">
                    <h3>📊 Monitoreo del Sistema</h3>
                    <p><a href="/status">🔍 Ver Estado de la Base de Datos</a></p>
                    <p><a href="/health">❤️ Health Check</a></p>
                </div>
                
                <div class="status">
                    <h3>�️ Base de Datos</h3>
                    <p>PostgreSQL con PostGIS activado</p>
                    <p>Datos cargados automáticamente al deployment</p>
                </div>
            </body>
            </html>
            """
            self.wfile.write(html.encode())
            
        elif self.path == "/status":
            status = app.get_status()
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(status, indent=2).encode())
        
        elif self.path == "/health":
            health = {"status": "ok", "service": "railway-db-app"}
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(health).encode())
        
        else:
            self.send_response(404)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            error = {"error": "Not Found", "path": self.path}
            self.wfile.write(json.dumps(error).encode())
    
    def log_message(self, format, *args):
        """Logging personalizado."""
        logger.info(f"HTTP: {format % args}")


def main():
    """Función principal."""
    logger.info("🚂 Iniciando aplicación Railway...")
    
    # Crear y configurar aplicación
    global app
    app = RailwayApp()
    
    # Ejecutar deployment de base de datos
    logger.info("🗃️ Ejecutando deployment de base de datos...")
    deployment_success = app.run_deployment()
    
    if not deployment_success:
        logger.error("❌ Deployment falló - continuando con servidor web para diagnóstico")
    
    # Iniciar servidor web
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), StatusHandler)
    
    logger.info(f"🌐 Servidor web iniciado en puerto {port}")
    logger.info("✅ Aplicación Railway lista")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("🛑 Cerrando aplicación...")
        server.shutdown()


# Instancia global
app = None

if __name__ == "__main__":
    main()