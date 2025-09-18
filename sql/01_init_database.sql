-- Inicialización completa de la base de datos PostgreSQL con PostGIS
-- para el sistema de gestión de proyectos

-- Crear esquema principal si no existe
CREATE SCHEMA IF NOT EXISTS public;

-- Comentario del esquema
COMMENT ON SCHEMA public IS 'Esquema principal para el sistema de gestión de proyectos';

-- Habilitar PostGIS y extensiones relacionadas
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;
CREATE EXTENSION IF NOT EXISTS fuzzystrmatch;

-- Crear función para actualizar timestamp automáticamente
CREATE OR REPLACE FUNCTION update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Comentario de la función
COMMENT ON FUNCTION update_timestamp() IS 'Función para actualizar automáticamente el campo updated_at';

-- Base de datos inicializada correctamente con PostGIS