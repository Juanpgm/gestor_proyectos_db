#!/usr/bin/env python3
"""
🔧 Railway Deployment Diagnostic
==============================
Script de diagnóstico para verificar la configuración Railway
"""

import os
import sys
from pathlib import Path
import json

def diagnostic_check():
    """Ejecuta diagnóstico completo para Railway"""
    print("🔧 DIAGNÓSTICO RAILWAY DEPLOYMENT")
    print("=" * 50)
    
    results = {
        "project_structure": check_project_structure(),
        "python_configuration": check_python_configuration(),
        "railway_configuration": check_railway_configuration(),
        "dependencies": check_dependencies(),
        "environment": check_environment()
    }
    
    # Mostrar resultados
    all_good = True
    for category, checks in results.items():
        print(f"\n📋 {category.upper().replace('_', ' ')}")
        print("-" * 30)
        for check_name, status in checks.items():
            icon = "✅" if status else "❌"
            print(f"{icon} {check_name}")
            if not status:
                all_good = False
    
    print("\n" + "=" * 50)
    if all_good:
        print("🎉 ¡DIAGNÓSTICO EXITOSO! Railway está listo para deployment")
    else:
        print("⚠️ DIAGNÓSTICO FALLÓ - Corregir errores antes del deployment")
    
    return all_good

def check_project_structure():
    """Verifica la estructura del proyecto"""
    required_files = [
        'railway_deploy.py',
        'intelligent_master_deploy.py', 
        'requirements.txt',
        'runtime.txt',
        'Procfile',
        'railway.toml',
        'nixpacks.toml'
    ]
    
    results = {}
    for file in required_files:
        results[f"Archivo {file}"] = Path(file).exists()
    
    return results

def check_python_configuration():
    """Verifica configuración Python"""
    results = {}
    
    # Verificar versión Python
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}"
    results[f"Python {python_version}"] = sys.version_info >= (3, 11)
    
    # Verificar runtime.txt
    if Path('runtime.txt').exists():
        with open('runtime.txt', 'r') as f:
            runtime_content = f.read().strip()
        results[f"runtime.txt: {runtime_content}"] = 'python-3.1' in runtime_content
    else:
        results["runtime.txt"] = False
    
    # Verificar .python-version
    results[".python-version existe"] = Path('.python-version').exists()
    
    return results

def check_railway_configuration():
    """Verifica configuración específica de Railway"""
    results = {}
    
    # railway.toml
    if Path('railway.toml').exists():
        with open('railway.toml', 'r') as f:
            railway_content = f.read()
        results["railway.toml válido"] = 'railway_deploy.py' in railway_content
    else:
        results["railway.toml"] = False
    
    # nixpacks.toml
    if Path('nixpacks.toml').exists():
        with open('nixpacks.toml', 'r') as f:
            nixpacks_content = f.read()
        results["nixpacks.toml válido"] = 'python' in nixpacks_content.lower()
    else:
        results["nixpacks.toml"] = False
    
    # Procfile
    if Path('Procfile').exists():
        with open('Procfile', 'r') as f:
            procfile_content = f.read()
        results["Procfile válido"] = 'railway_deploy.py' in procfile_content
    else:
        results["Procfile"] = False
    
    return results

def check_dependencies():
    """Verifica dependencias"""
    results = {}
    
    if Path('requirements.txt').exists():
        with open('requirements.txt', 'r') as f:
            requirements = f.read()
        
        essential_deps = [
            'psycopg2-binary',
            'sqlalchemy',
            'python-dotenv'
        ]
        
        for dep in essential_deps:
            results[f"Dependencia {dep}"] = dep in requirements.lower()
    else:
        results["requirements.txt"] = False
    
    return results

def check_environment():
    """Verifica configuración de entorno"""
    results = {}
    
    # Verificar .env
    results[".env existe"] = Path('.env').exists()
    
    # Verificar .gitignore
    if Path('.gitignore').exists():
        with open('.gitignore', 'r') as f:
            gitignore_content = f.read()
        results[".gitignore configurado"] = 'app_outputs' in gitignore_content
    else:
        results[".gitignore"] = False
    
    # Verificar archivos de configuración Railway
    results["pyproject.toml existe"] = Path('pyproject.toml').exists()
    results[".railwayignore existe"] = Path('.railwayignore').exists()
    
    return results

def generate_fix_suggestions():
    """Genera sugerencias para arreglar problemas"""
    print("\n🔧 SUGERENCIAS DE CORRECCIÓN")
    print("=" * 30)
    print("Si algún check falló, aquí están las soluciones:")
    print()
    print("1. Archivos faltantes:")
    print("   - Asegurar que todos los archivos estén presentes")
    print("   - Verificar que no hayan sido excluidos por .gitignore")
    print()
    print("2. Configuración Python:")
    print("   - Usar Python 3.11 o superior")
    print("   - Verificar runtime.txt tenga 'python-3.12'")
    print()
    print("3. Configuración Railway:")
    print("   - railway.toml debe tener 'railway_deploy.py'")
    print("   - nixpacks.toml debe incluir 'python311'")
    print("   - Procfile debe apuntar a 'railway_deploy.py'")
    print()
    print("4. Dependencias:")
    print("   - requirements.txt debe tener todas las dependencias esenciales")
    print("   - Verificar versiones compatibles")

def main():
    """Función principal"""
    success = diagnostic_check()
    
    if not success:
        generate_fix_suggestions()
    
    print(f"\n🎯 RESULTADO: {'✅ LISTO' if success else '❌ NECESITA CORRECCIÓN'}")
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())