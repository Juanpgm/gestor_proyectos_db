#!/usr/bin/env python3
"""
Setup.py para Gestor Proyectos DB - Railway Optimized
====================================================
Configuración del paquete optimizada para Railway deployment
"""

from setuptools import setup, find_packages
import os

# Leer requirements desde archivo
def read_requirements():
    """Lee requirements.txt y retorna lista de dependencias"""
    requirements_path = os.path.join(os.path.dirname(__file__), 'requirements.txt')
    with open(requirements_path, 'r', encoding='utf-8') as f:
        return [
            line.strip() 
            for line in f 
            if line.strip() and not line.startswith('#') and not line.startswith('-')
        ]

# Leer README si existe
def read_readme():
    """Lee README.md si existe"""
    readme_path = os.path.join(os.path.dirname(__file__), 'README.md')
    if os.path.exists(readme_path):
        with open(readme_path, 'r', encoding='utf-8') as f:
            return f.read()
    return "Sistema Inteligente de Gestión de Base de Datos para Proyectos"

setup(
    name="gestor-proyectos-db",
    version="1.0.0",
    description="Sistema Inteligente de Gestión de Base de Datos para Proyectos - Railway Ready",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    author="Sistema Inteligente",
    author_email="admin@gestorproyectosdb.com",
    url="https://github.com/Juanpgm/gestor_proyectos_db",
    python_requires=">=3.11",
    packages=find_packages(where="."),
    package_dir={"": "."},
    install_requires=read_requirements(),
    entry_points={
        "console_scripts": [
            "railway-app=app:main",
            "railway-deploy=railway_deploy:main",
            "intelligent-deploy=intelligent_master_deploy:main",
            "gestordb=main:main",
        ],
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Framework :: Railway",
        "Topic :: Database :: Front-Ends",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    keywords="railway database postgresql postgis intelligent deployment",
    include_package_data=True,
    zip_safe=False,
    platforms=["any"],
    project_urls={
        "Bug Reports": "https://github.com/Juanpgm/gestor_proyectos_db/issues",
        "Source": "https://github.com/Juanpgm/gestor_proyectos_db",
        "Railway Deploy": "https://railway.app",
    },
)