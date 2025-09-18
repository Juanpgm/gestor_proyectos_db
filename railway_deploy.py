#!/usr/bin/env python3
"""
Punto de entrada específico para Railway deployment.
"""

import os
import sys
from pathlib import Path

# Asegurar que el directorio actual esté en el path
sys.path.insert(0, str(Path(__file__).parent))

def main():
    """Función principal para Railway."""
    print("🚂 Iniciando despliegue Railway...")
    
    # Forzar el uso del sistema inteligente con Railway
    try:
        from intelligent_master_deploy import IntelligentDatabaseManager, DeploymentEnvironment
        
        # Crear manager forzando Railway
        manager = IntelligentDatabaseManager(DeploymentEnvironment.RAILWAY)
        
        # Ejecutar despliegue completo
        success = manager.deploy(force_environment=DeploymentEnvironment.RAILWAY)
        
        if success:
            print("✅ Despliegue Railway exitoso")
            
            # Mantener el proceso vivo para Railway
            print("🔄 Manteniendo servicio activo...")
            try:
                import time
                while True:
                    time.sleep(60)  # Mantener vivo cada minuto
            except KeyboardInterrupt:
                print("🛑 Deteniendo servicio...")
        else:
            print("❌ Fallo en despliegue Railway")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Error en Railway deployment: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()