-- Crear tabla de contratos de empréstito
-- Esta tabla almacena información detallada sobre los contratos

CREATE TABLE IF NOT EXISTS emp_contratos (
    -- Identificadores principales
    id_contrato VARCHAR(50) PRIMARY KEY,
    referencia_del_contrato VARCHAR(100) UNIQUE NOT NULL,
    proceso_de_compra VARCHAR(50) NOT NULL,
    proceso_id INTEGER REFERENCES emp_procesos(id) ON DELETE SET NULL,
    
    -- Información de la entidad
    nombre_entidad VARCHAR(500) NOT NULL,
    nit_entidad VARCHAR(20) NOT NULL,
    departamento VARCHAR(100),
    ciudad VARCHAR(100),
    localizacion VARCHAR(200),
    orden VARCHAR(50),
    sector VARCHAR(200),
    rama VARCHAR(50),
    entidad_centralizada VARCHAR(50),
    codigo_entidad VARCHAR(20),
    
    -- Información del contrato
    estado_contrato VARCHAR(50) NOT NULL,
    codigo_de_categoria_principal VARCHAR(50),
    descripcion_del_proceso TEXT,
    objeto_del_contrato TEXT NOT NULL,
    tipo_de_contrato VARCHAR(100),
    modalidad_de_contratacion VARCHAR(100),
    justificacion_modalidad VARCHAR(200),
    
    -- Fechas importantes
    fecha_de_firma DATE,
    fecha_de_inicio_del_contrato DATE,
    fecha_de_fin_del_contrato DATE,
    duracion_del_contrato VARCHAR(50),
    fecha_inicio_liquidacion DATE,
    fecha_fin_liquidacion DATE,
    
    -- Información del proveedor
    documento_proveedor VARCHAR(20),
    tipodocproveedor VARCHAR(50),
    proveedor_adjudicado VARCHAR(500) NOT NULL,
    es_grupo BOOLEAN,
    es_pyme BOOLEAN,
    codigo_proveedor VARCHAR(20),
    
    -- Información del representante legal
    nombre_representante_legal VARCHAR(200),
    nacionalidad_representante_legal VARCHAR(10),
    domicilio_representante_legal VARCHAR(200),
    tipo_identificacion_representante_legal VARCHAR(50),
    identificacion_representante_legal VARCHAR(50),
    genero_representante_legal VARCHAR(20),
    
    -- Valores monetarios (todos con CHECK para valores no negativos)
    valor_del_contrato NUMERIC(15, 2) NOT NULL CHECK (valor_del_contrato >= 0),
    valor_de_pago_adelantado NUMERIC(15, 2) DEFAULT 0 CHECK (valor_de_pago_adelantado >= 0),
    valor_facturado NUMERIC(15, 2) DEFAULT 0 CHECK (valor_facturado >= 0),
    valor_pendiente_de_pago NUMERIC(15, 2) DEFAULT 0 CHECK (valor_pendiente_de_pago >= 0),
    valor_pagado NUMERIC(15, 2) DEFAULT 0 CHECK (valor_pagado >= 0),
    valor_amortizado NUMERIC(15, 2) DEFAULT 0 CHECK (valor_amortizado >= 0),
    valor_pendiente_de_ejecucion NUMERIC(15, 2) DEFAULT 0 CHECK (valor_pendiente_de_ejecucion >= 0),
    
    -- Recursos financieros
    presupuesto_general_nacion NUMERIC(15, 2) DEFAULT 0 CHECK (presupuesto_general_nacion >= 0),
    sistema_general_participaciones NUMERIC(15, 2) DEFAULT 0 CHECK (sistema_general_participaciones >= 0),
    sistema_general_regalias NUMERIC(15, 2) DEFAULT 0 CHECK (sistema_general_regalias >= 0),
    recursos_propios_alcaldias NUMERIC(15, 2) DEFAULT 0 CHECK (recursos_propios_alcaldias >= 0),
    recursos_de_credito NUMERIC(15, 2) DEFAULT 0 CHECK (recursos_de_credito >= 0),
    recursos_propios NUMERIC(15, 2) DEFAULT 0 CHECK (recursos_propios >= 0),
    
    -- Información de proyecto BPIN
    estado_bpin VARCHAR(50),
    anno_bpin VARCHAR(10),
    bpin VARCHAR(20),
    saldo_cdp VARCHAR(50),
    saldo_vigencia VARCHAR(50),
    
    -- Configuraciones del contrato
    condiciones_de_entrega VARCHAR(100),
    habilita_pago_adelantado BOOLEAN,
    liquidacion BOOLEAN,
    obligacion_ambiental BOOLEAN,
    obligaciones_postconsumo BOOLEAN,
    reversion BOOLEAN,
    origen_de_los_recursos VARCHAR(50),
    destino_gasto VARCHAR(50),
    el_contrato_puede_ser_prorrogado BOOLEAN,
    fecha_notificacion_prorroga DATE,
    
    -- Información de postconflicto
    espostconflicto BOOLEAN,
    dias_adicionados VARCHAR(20),
    puntos_del_acuerdo VARCHAR(100),
    pilares_del_acuerdo VARCHAR(100),
    
    -- Información bancaria
    nombre_del_banco VARCHAR(100),
    tipo_de_cuenta VARCHAR(50),
    numero_de_cuenta VARCHAR(50),
    
    -- Responsables del contrato
    nombre_ordenador_del_gasto VARCHAR(200),
    tipo_documento_ordenador_gasto VARCHAR(50),
    numero_documento_ordenador_gasto VARCHAR(50),
    
    nombre_supervisor VARCHAR(200),
    tipo_documento_supervisor VARCHAR(50),
    numero_documento_supervisor VARCHAR(50),
    
    nombre_ordenador_de_pago VARCHAR(200),
    tipo_documento_ordenador_pago VARCHAR(50),
    numero_documento_ordenador_pago VARCHAR(50),
    
    -- URLs y referencias (usando JSONB para mejor performance)
    urlproceso JSONB,
    
    -- Metadatos de extracción
    dataset_source VARCHAR(50),
    search_field VARCHAR(50),
    referencia_buscada VARCHAR(100),
    search_type VARCHAR(50),
    total_campos INTEGER,
    registro_origen JSONB,
    
    -- Campos de auditoría
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Comentarios de la tabla y columnas principales
COMMENT ON TABLE emp_contratos IS 'Tabla de contratos de empréstito registrados en SECOP';
COMMENT ON COLUMN emp_contratos.id_contrato IS 'Identificador único del contrato en SECOP';
COMMENT ON COLUMN emp_contratos.referencia_del_contrato IS 'Referencia única del contrato';
COMMENT ON COLUMN emp_contratos.proceso_de_compra IS 'ID del proceso de compra asociado';
COMMENT ON COLUMN emp_contratos.proceso_id IS 'ID del proceso en la tabla emp_procesos';
COMMENT ON COLUMN emp_contratos.nombre_entidad IS 'Nombre de la entidad contratante';
COMMENT ON COLUMN emp_contratos.nit_entidad IS 'NIT de la entidad';
COMMENT ON COLUMN emp_contratos.objeto_del_contrato IS 'Objeto del contrato';
COMMENT ON COLUMN emp_contratos.estado_contrato IS 'Estado actual del contrato';
COMMENT ON COLUMN emp_contratos.valor_del_contrato IS 'Valor total del contrato';
COMMENT ON COLUMN emp_contratos.proveedor_adjudicado IS 'Nombre del proveedor adjudicado';
COMMENT ON COLUMN emp_contratos.urlproceso IS 'URLs relacionadas con el proceso (formato JSON)';
COMMENT ON COLUMN emp_contratos.registro_origen IS 'Información del registro origen (formato JSON)';
COMMENT ON COLUMN emp_contratos.created_at IS 'Fecha y hora de creación del registro';
COMMENT ON COLUMN emp_contratos.updated_at IS 'Fecha y hora de última actualización';

-- Crear índices para optimizar consultas
CREATE INDEX IF NOT EXISTS idx_emp_contratos_referencia ON emp_contratos(referencia_del_contrato);
CREATE INDEX IF NOT EXISTS idx_emp_contratos_proceso_compra ON emp_contratos(proceso_de_compra);
CREATE INDEX IF NOT EXISTS idx_emp_contratos_proceso_id ON emp_contratos(proceso_id);
CREATE INDEX IF NOT EXISTS idx_emp_contratos_entidad ON emp_contratos(nombre_entidad);
CREATE INDEX IF NOT EXISTS idx_emp_contratos_nit ON emp_contratos(nit_entidad);
CREATE INDEX IF NOT EXISTS idx_emp_contratos_estado ON emp_contratos(estado_contrato);
CREATE INDEX IF NOT EXISTS idx_emp_contratos_tipo ON emp_contratos(tipo_de_contrato);
CREATE INDEX IF NOT EXISTS idx_emp_contratos_modalidad ON emp_contratos(modalidad_de_contratacion);
CREATE INDEX IF NOT EXISTS idx_emp_contratos_proveedor ON emp_contratos(proveedor_adjudicado);
CREATE INDEX IF NOT EXISTS idx_emp_contratos_valor ON emp_contratos(valor_del_contrato);
CREATE INDEX IF NOT EXISTS idx_emp_contratos_fecha_firma ON emp_contratos(fecha_de_firma);
CREATE INDEX IF NOT EXISTS idx_emp_contratos_fecha_inicio ON emp_contratos(fecha_de_inicio_del_contrato);
CREATE INDEX IF NOT EXISTS idx_emp_contratos_fecha_fin ON emp_contratos(fecha_de_fin_del_contrato);
CREATE INDEX IF NOT EXISTS idx_emp_contratos_departamento ON emp_contratos(departamento);
CREATE INDEX IF NOT EXISTS idx_emp_contratos_ciudad ON emp_contratos(ciudad);
CREATE INDEX IF NOT EXISTS idx_emp_contratos_sector ON emp_contratos(sector);
CREATE INDEX IF NOT EXISTS idx_emp_contratos_bpin ON emp_contratos(bpin);
CREATE INDEX IF NOT EXISTS idx_emp_contratos_created_at ON emp_contratos(created_at);

-- Índices para campos JSON usando GIN
CREATE INDEX IF NOT EXISTS idx_emp_contratos_urlproceso_gin ON emp_contratos USING GIN(urlproceso);
CREATE INDEX IF NOT EXISTS idx_emp_contratos_registro_origen_gin ON emp_contratos USING GIN(registro_origen);

-- Crear trigger para actualizar timestamp automáticamente
CREATE TRIGGER update_emp_contratos_timestamp
    BEFORE UPDATE ON emp_contratos
    FOR EACH ROW
    EXECUTE FUNCTION update_timestamp();

-- Tabla emp_contratos creada exitosamente con índices y triggers