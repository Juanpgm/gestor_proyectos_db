#!/usr/bin/env python3
"""
Script para debuggear la carga de configuración.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Agregar src al path
sys.path.append(str(Path(__file__).parent / "src"))

from src.config.settings import load_config

def debug_config():
    """Debug de la configuración."""
    
    print("🔍 Debug de configuración\n")
    
    # Verificar archivo .env
    env_file = Path(".env")
    print(f"📁 Archivo .env existe: {env_file.exists()}")
    if env_file.exists():
        print(f"📄 Contenido del .env:")
        with open(env_file, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f, 1):
                if line.strip() and not line.startswith('#'):
                    print(f"   {i}: {line.strip()}")
    
    print(f"\n🔧 Variables de entorno antes de cargar .env:")
    db_vars = {k: v for k, v in os.environ.items() if k.startswith('DB_')}
    for k, v in db_vars.items():
        print(f"   {k}: {v}")
    
    # Cargar configuración
    print(f"\n📦 Cargando configuración...")
    try:
        config = load_config()
        print(f"✅ Configuración cargada exitosamente")
        
        # Mostrar configuración de base de datos
        db_config = config["database"]
        print(f"\n📊 Configuración de base de datos:")
        print(f"   Host: {db_config.host}")
        print(f"   Puerto: {db_config.port}")
        print(f"   Base de datos: {db_config.database}")
        print(f"   Usuario: {db_config.user}")
        print(f"   Contraseña: {'*' * len(db_config.password)}")
        print(f"   Schema: {db_config.db_schema}")
        print(f"   Connection String: {db_config.connection_string}")
        
    except Exception as e:
        print(f"❌ Error cargando configuración: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_config()