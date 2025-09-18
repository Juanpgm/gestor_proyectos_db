#!/usr/bin/env python3
"""
🔍 Railway GitHub Repository Verification
========================================
Verifica que todos los archivos necesarios estén en el repositorio remoto
"""

import subprocess
import sys

def verify_repository():
    """Verifica que el repositorio tenga todos los archivos necesarios"""
    print("🔍 VERIFICACIÓN REPOSITORIO RAILWAY")
    print("=" * 50)
    
    # Archivos críticos para Railway/Railpack
    critical_files = [
        # Python entry points
        'app.py',
        'main.py', 
        'railway_deploy.py',
        'detect.py',
        
        # Configuration files
        'requirements.txt',
        'runtime.txt',
        'Procfile',
        
        # Railway configs
        'railway.toml',
        'nixpacks.toml',
        'railpack.toml',
        
        # Build scripts
        'build.sh',
        'start.sh',
        
        # Project files
        'intelligent_master_deploy.py',
        'intelligent_railway_deploy.py',
        
        # Ignore files
        '.gitignore',
        '.railwayignore'
    ]
    
    print("📋 Verificando archivos en repositorio remoto...")
    
    # Obtener lista de archivos del repositorio remoto
    try:
        result = subprocess.run(
            ['git', 'ls-tree', '--name-only', 'origin/master'],
            capture_output=True,
            text=True,
            check=True
        )
        remote_files = set(result.stdout.strip().split('\n'))
        
        # Verificar cada archivo crítico
        missing_files = []
        present_files = []
        
        for file in critical_files:
            if file in remote_files:
                present_files.append(file)
                print(f"✅ {file}")
            else:
                missing_files.append(file)
                print(f"❌ {file} - FALTANTE")
        
        print(f"\n📊 RESUMEN:")
        print(f"✅ Archivos presentes: {len(present_files)}")
        print(f"❌ Archivos faltantes: {len(missing_files)}")
        
        if missing_files:
            print(f"\n⚠️ ARCHIVOS FALTANTES:")
            for file in missing_files:
                print(f"   - {file}")
            return False
        else:
            print(f"\n🎉 ¡TODOS LOS ARCHIVOS CRÍTICOS PRESENTES!")
            return True
            
    except subprocess.CalledProcessError as e:
        print(f"❌ Error verificando repositorio: {e}")
        return False

def show_railway_instructions():
    """Muestra instrucciones para Railway deployment"""
    print("\n🚂 INSTRUCCIONES RAILWAY DEPLOYMENT")
    print("=" * 40)
    print("1. En Railway Dashboard:")
    print("   - Ir a https://railway.app/new")
    print("   - Seleccionar 'Deploy from GitHub repo'")
    print("   - Buscar y seleccionar: Juanpgm/gestor_proyectos_db")
    print("   - Railway detectará automáticamente Python")
    print()
    print("2. Configuración automática esperada:")
    print("   - Build System: Nixpacks")
    print("   - Language: Python 3.12")
    print("   - Start Command: python app.py")
    print("   - Build Command: chmod +x build.sh && ./build.sh")
    print()
    print("3. Variables de entorno a configurar:")
    print("   - DATABASE_URL (se generará automáticamente con PostgreSQL)")
    print("   - PYTHONUNBUFFERED=1")
    print("   - PYTHONDONTWRITEBYTECODE=1")
    print()
    print("4. Servicios recomendados:")
    print("   - PostgreSQL (Railway service)")
    print("   - Redis (opcional, para cache)")

def main():
    """Función principal"""
    success = verify_repository()
    
    if success:
        show_railway_instructions()
        print("\n🎯 ESTADO: ✅ LISTO PARA RAILWAY DEPLOYMENT")
        print("🔗 URL del repositorio: https://github.com/Juanpgm/gestor_proyectos_db")
        return 0
    else:
        print("\n🎯 ESTADO: ❌ REPOSITORIO INCOMPLETO")
        print("⚠️ Asegurar que todos los archivos estén en el repositorio antes del deployment")
        return 1

if __name__ == "__main__":
    sys.exit(main())