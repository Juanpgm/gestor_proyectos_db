-- Migración 001: Crear tabla de procesos de empréstito
-- Fecha: 2025-09-17
-- Descripción: Migración inicial para crear la tabla emp_procesos

-- Verificar si la tabla ya existe
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename = 'emp_procesos') THEN
        -- Crear tabla de procesos
        EXECUTE '
        CREATE TABLE emp_procesos (
            id SERIAL PRIMARY KEY,
            referencia_proceso VARCHAR(100) UNIQUE NOT NULL,
            banco VARCHAR(100) NOT NULL,
            descripcion TEXT,
            objeto TEXT NOT NULL,
            valor_total NUMERIC(15, 2) NOT NULL CHECK (valor_total >= 0),
            valor_plataforma NUMERIC(15, 2) CHECK (valor_plataforma >= 0),
            modalidad VARCHAR(100),
            referencia_contrato VARCHAR(100),
            planeado DATE,
            estado_proceso_secop VARCHAR(100) NOT NULL,
            observaciones TEXT,
            numero_contacto VARCHAR(20),
            url_proceso VARCHAR(500),
            url_estado_real_proceso VARCHAR(500),
            archivo_origen VARCHAR(200),
            fecha_procesamiento TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )';
        
        RAISE NOTICE 'Tabla emp_procesos creada exitosamente';
    ELSE
        RAISE NOTICE 'Tabla emp_procesos ya existe, omitiendo creación';
    END IF;
END
$$;