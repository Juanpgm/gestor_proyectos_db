#!/usr/bin/env python3

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text

def check_tables():
    try:
        # Usar configuración local directa
        db_url = "postgresql://postgres:root@localhost:5432/dev"
        engine = create_engine(db_url)
        
        with engine.connect() as connection:
            # Verificar tablas existentes
            result = connection.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"))
            tables = [row[0] for row in result]
            
            print("=== TABLAS EXISTENTES ===")
            for table in sorted(tables):
                print(f"  • {table}")
            
            print(f"\nTotal tablas: {len(tables)}")
            
            # Verificar si existen las tablas críticas
            critical_tables = [
                'emp_seguimiento_procesos_dacp',
                'emp_contratos_dacp', 
                'emp_contratos',
                'system_health',
                'system_alerts'
            ]
            
            print("\n=== VERIFICACIÓN DE TABLAS CRÍTICAS ===")
            for table in critical_tables:
                exists = table in tables
                status = "✅ EXISTE" if exists else "❌ FALTA"
                print(f"  {table}: {status}")
                
    except Exception as e:
        print(f"Error verificando tablas: {e}")

if __name__ == "__main__":
    check_tables()