#!/usr/bin/env python3
"""
Setup.py para Gestor Proyectos DB
=================================
Configuración del paquete para Railway deployment
"""

from setuptools import setup, find_packages

with open("requirements.txt", "r", encoding="utf-8") as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith("#")]

setup(
    name="gestor-proyectos-db",
    version="1.0.0",
    description="Sistema Inteligente de Gestión de Base de Datos para Proyectos",
    author="Sistema Inteligente",
    python_requires=">=3.11",
    packages=find_packages(),
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "railway-deploy=railway_deploy:main",
            "intelligent-deploy=intelligent_master_deploy:main",
        ],
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    include_package_data=True,
    zip_safe=False,
)