-- Crear tabla de seguimiento de procesos DACP
-- Esta tabla almacena información sobre los procesos de contratación

CREATE TABLE IF NOT EXISTS emp_seguimiento_procesos_dacp (
    -- Identificador principal
    id SERIAL PRIMARY KEY,
    referencia_proceso VARCHAR(100) UNIQUE NOT NULL,
    
    -- Información básica del proceso
    banco VARCHAR(100) NOT NULL,
    descripcion TEXT,
    objeto TEXT NOT NULL,
    
    -- Valores monetarios
    valor_total NUMERIC(15, 2) NOT NULL CHECK (valor_total >= 0),
    valor_plataforma NUMERIC(15, 2) CHECK (valor_plataforma >= 0),
    
    -- Información contractual
    modalidad VARCHAR(100),
    referencia_contrato VARCHAR(100),
    
    -- Fechas y cronograma
    planeado DATE,
    
    -- Estado y seguimiento
    estado_proceso_secop VARCHAR(100) NOT NULL,
    observaciones TEXT,
    
    -- Contacto
    numero_contacto VARCHAR(20),
    
    -- URLs de referencia
    url_proceso VARCHAR(500),
    url_estado_real_proceso VARCHAR(500),
    
    -- Metadatos de procesamiento
    archivo_origen VARCHAR(200),
    fecha_procesamiento TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Campos de auditoría
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Comentarios de la tabla y columnas
COMMENT ON TABLE emp_seguimiento_procesos_dacp IS 'Tabla de seguimiento de procesos DACP registrados en SECOP';
COMMENT ON COLUMN emp_seguimiento_procesos_dacp.id IS 'Identificador único del proceso';
COMMENT ON COLUMN emp_seguimiento_procesos_dacp.referencia_proceso IS 'Referencia única del proceso en SECOP';
COMMENT ON COLUMN emp_seguimiento_procesos_dacp.banco IS 'Banco asociado al empréstito';
COMMENT ON COLUMN emp_seguimiento_procesos_dacp.descripcion IS 'Descripción breve del proceso';
COMMENT ON COLUMN emp_seguimiento_procesos_dacp.objeto IS 'Objeto detallado del proceso';
COMMENT ON COLUMN emp_seguimiento_procesos_dacp.valor_total IS 'Valor total del proceso';
COMMENT ON COLUMN emp_seguimiento_procesos_dacp.valor_plataforma IS 'Valor registrado en plataforma SECOP';
COMMENT ON COLUMN emp_seguimiento_procesos_dacp.modalidad IS 'Modalidad de contratación';
COMMENT ON COLUMN emp_seguimiento_procesos_dacp.referencia_contrato IS 'Referencia del contrato asociado';
COMMENT ON COLUMN emp_seguimiento_procesos_dacp.planeado IS 'Fecha planeada del proceso';
COMMENT ON COLUMN emp_seguimiento_procesos_dacp.estado_proceso_secop IS 'Estado actual en SECOP';
COMMENT ON COLUMN emp_seguimiento_procesos_dacp.observaciones IS 'Observaciones del seguimiento';
COMMENT ON COLUMN emp_seguimiento_procesos_dacp.numero_contacto IS 'Número de contacto';
COMMENT ON COLUMN emp_seguimiento_procesos_dacp.url_proceso IS 'URL del proceso en SECOP';
COMMENT ON COLUMN emp_seguimiento_procesos_dacp.url_estado_real_proceso IS 'URL del estado real del proceso';
COMMENT ON COLUMN emp_seguimiento_procesos_dacp.archivo_origen IS 'Archivo origen de los datos';
COMMENT ON COLUMN emp_seguimiento_procesos_dacp.fecha_procesamiento IS 'Fecha de procesamiento del registro';
COMMENT ON COLUMN emp_seguimiento_procesos_dacp.created_at IS 'Fecha y hora de creación del registro';
COMMENT ON COLUMN emp_seguimiento_procesos_dacp.updated_at IS 'Fecha y hora de última actualización';

-- Crear índices para optimizar consultas
CREATE INDEX IF NOT EXISTS idx_emp_seguimiento_procesos_dacp_referencia ON emp_seguimiento_procesos_dacp(referencia_proceso);
CREATE INDEX IF NOT EXISTS idx_emp_seguimiento_procesos_dacp_banco ON emp_seguimiento_procesos_dacp(banco);
CREATE INDEX IF NOT EXISTS idx_emp_seguimiento_procesos_dacp_estado ON emp_seguimiento_procesos_dacp(estado_proceso_secop);
CREATE INDEX IF NOT EXISTS idx_emp_seguimiento_procesos_dacp_planeado ON emp_seguimiento_procesos_dacp(planeado);
CREATE INDEX IF NOT EXISTS idx_emp_seguimiento_procesos_dacp_valor ON emp_seguimiento_procesos_dacp(valor_total);
CREATE INDEX IF NOT EXISTS idx_emp_seguimiento_procesos_dacp_modalidad ON emp_seguimiento_procesos_dacp(modalidad);
CREATE INDEX IF NOT EXISTS idx_emp_seguimiento_procesos_dacp_created_at ON emp_seguimiento_procesos_dacp(created_at);

-- Crear trigger para actualizar timestamp automáticamente
CREATE TRIGGER update_emp_seguimiento_procesos_dacp_timestamp
    BEFORE UPDATE ON emp_seguimiento_procesos_dacp
    FOR EACH ROW
    EXECUTE FUNCTION update_timestamp();