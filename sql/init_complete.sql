-- Script maestro para ejecutar toda la inicialización de la base de datos
-- Este script ejecuta todos los archivos de inicialización en el orden correcto

\echo 'Iniciando configuración completa de la base de datos...'
\echo '=================================================='

-- 1. Inicializar base de datos y PostGIS
\echo 'Paso 1: Inicializando base de datos y PostGIS...'
\i 01_init_database.sql

-- 2. Crear tabla de procesos
\echo 'Paso 2: Creando tabla de procesos...'
\i 02_create_procesos_table.sql

-- 3. Crear tabla de contratos
\echo 'Paso 3: Creando tabla de contratos...'
\i 03_create_contratos_table.sql

-- 4. Crear vistas de análisis
\echo 'Paso 4: Creando vistas de análisis...'
\i 04_create_views.sql

-- Verificación final
\echo '=================================================='
\echo 'Verificando la instalación...'

-- Verificar tablas creadas
SELECT 
    schemaname,
    tablename,
    tableowner
FROM pg_tables 
WHERE schemaname = 'public' 
    AND tablename IN ('emp_procesos', 'emp_contratos')
ORDER BY tablename;

-- Verificar vistas creadas
SELECT 
    schemaname,
    viewname,
    viewowner
FROM pg_views 
WHERE schemaname = 'public' 
    AND viewname LIKE 'v_%'
ORDER BY viewname;

-- Verificar PostGIS
SELECT PostGIS_Version() as postgis_version;

-- Verificar índices creados
SELECT 
    tablename,
    indexname,
    indexdef
FROM pg_indexes 
WHERE schemaname = 'public' 
    AND tablename IN ('emp_procesos', 'emp_contratos')
ORDER BY tablename, indexname;

\echo '=================================================='
\echo 'Configuración de base de datos completada exitosamente!'
\echo 'Tablas creadas: emp_procesos, emp_contratos'
\echo 'Vistas creadas: v_procesos_resumen, v_contratos_resumen, v_analisis_entidades,'
\echo '                v_analisis_temporal, v_analisis_proveedores'
\echo 'PostGIS habilitado y configurado'
\echo '=================================================='