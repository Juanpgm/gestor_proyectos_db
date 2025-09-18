#!/usr/bin/env python3
"""
🚂 Railway App Entry Point
=========================
Archivo principal para que Railway/Railpack detecte automáticamente Python
"""

import sys
import os
from pathlib import Path

# Agregar directorio actual al path
sys.path.insert(0, str(Path(__file__).parent))

def main():
    """Función principal que redirige al railway_deploy.py"""
    print("🚂 App.py - Punto de entrada Railway")
    
    # Configurar entorno Railway
    os.environ['PYTHONUNBUFFERED'] = '1'
    os.environ['DEPLOYMENT_ENV'] = 'railway'
    
    # Importar y ejecutar railway_deploy
    try:
        import railway_deploy
        railway_deploy.main()
    except Exception as e:
        print(f"❌ Error en app.py: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()