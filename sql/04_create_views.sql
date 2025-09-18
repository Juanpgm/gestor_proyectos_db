-- Crear vistas útiles para consultas frecuentes
-- Estas vistas facilitan el análisis de datos sin exponer la complejidad de las tablas base

-- Vista resumen de procesos con estadísticas de contratos
CREATE OR REPLACE VIEW v_procesos_resumen AS
SELECT 
    p.id,
    p.referencia_proceso,
    p.banco,
    p.descripcion,
    p.estado_proceso_secop,
    p.valor_total as valor_proceso,
    p.modalidad,
    p.planeado as fecha_planeada,
    -- Estadísticas de contratos asociados
    COUNT(c.id_contrato) as numero_contratos,
    COALESCE(SUM(c.valor_del_contrato), 0) as valor_total_contratos,
    COALESCE(SUM(c.valor_pagado), 0) as valor_total_pagado,
    COALESCE(SUM(c.valor_pendiente_de_ejecucion), 0) as valor_pendiente_total,
    -- Porcentajes
    CASE 
        WHEN p.valor_total > 0 THEN 
            ROUND((COALESCE(SUM(c.valor_del_contrato), 0) / p.valor_total * 100), 2)
        ELSE 0 
    END as porcentaje_contratado,
    CASE 
        WHEN COALESCE(SUM(c.valor_del_contrato), 0) > 0 THEN
            ROUND((COALESCE(SUM(c.valor_pagado), 0) / COALESCE(SUM(c.valor_del_contrato), 1) * 100), 2)
        ELSE 0
    END as porcentaje_ejecutado,
    p.created_at,
    p.updated_at
FROM emp_seguimiento_procesos_dacp p
LEFT JOIN emp_contratos c ON p.id = c.proceso_id
GROUP BY p.id, p.referencia_proceso, p.banco, p.descripcion, p.estado_proceso_secop, 
         p.valor_total, p.modalidad, p.planeado, p.created_at, p.updated_at;

COMMENT ON VIEW v_procesos_resumen IS 'Vista resumen de procesos con estadísticas agregadas de contratos';

-- Vista resumen de contratos con información clave
CREATE OR REPLACE VIEW v_contratos_resumen AS
SELECT 
    c.id_contrato,
    c.referencia_del_contrato,
    c.nombre_entidad,
    c.departamento,
    c.ciudad,
    c.estado_contrato,
    c.tipo_de_contrato,
    c.modalidad_de_contratacion,
    c.proveedor_adjudicado,
    c.valor_del_contrato,
    c.valor_pagado,
    c.valor_pendiente_de_ejecucion,
    c.fecha_de_firma,
    c.fecha_de_inicio_del_contrato,
    c.fecha_de_fin_del_contrato,
    -- Información del proceso asociado
    p.referencia_proceso,
    p.banco,
    p.estado_proceso_secop,
    -- Cálculos
    CASE 
        WHEN c.valor_del_contrato > 0 THEN 
            ROUND((c.valor_pagado / c.valor_del_contrato * 100), 2)
        ELSE 0 
    END as porcentaje_ejecucion,
    CASE 
        WHEN c.fecha_de_fin_del_contrato IS NOT NULL THEN
            CASE 
                WHEN c.fecha_de_fin_del_contrato < CURRENT_DATE THEN 'Vencido'
                WHEN c.fecha_de_fin_del_contrato <= CURRENT_DATE + INTERVAL '30 days' THEN 'Por vencer'
                ELSE 'Vigente'
            END
        ELSE 'Sin fecha'
    END as estado_vigencia,
    c.created_at,
    c.updated_at
FROM emp_contratos c
LEFT JOIN emp_seguimiento_procesos_dacp p ON c.proceso_id = p.id;

COMMENT ON VIEW v_contratos_resumen IS 'Vista resumen de contratos con información clave y cálculos';

-- Vista de análisis financiero por entidad
CREATE OR REPLACE VIEW v_analisis_entidades AS
SELECT 
    c.nombre_entidad,
    c.nit_entidad,
    c.departamento,
    c.ciudad,
    c.sector,
    COUNT(c.id_contrato) as total_contratos,
    SUM(c.valor_del_contrato) as valor_total_contratado,
    SUM(c.valor_pagado) as valor_total_pagado,
    SUM(c.valor_pendiente_de_ejecucion) as valor_pendiente_total,
    AVG(c.valor_del_contrato) as valor_promedio_contrato,
    -- Distribución por estado
    COUNT(CASE WHEN c.estado_contrato = 'En ejecución' THEN 1 END) as contratos_en_ejecucion,
    COUNT(CASE WHEN c.estado_contrato = 'Aprobado' THEN 1 END) as contratos_aprobados,
    COUNT(CASE WHEN c.estado_contrato = 'Terminado' THEN 1 END) as contratos_terminados,
    -- Porcentaje de ejecución general
    CASE 
        WHEN SUM(c.valor_del_contrato) > 0 THEN 
            ROUND((SUM(c.valor_pagado) / SUM(c.valor_del_contrato) * 100), 2)
        ELSE 0 
    END as porcentaje_ejecucion_general
FROM emp_contratos c
GROUP BY c.nombre_entidad, c.nit_entidad, c.departamento, c.ciudad, c.sector
ORDER BY valor_total_contratado DESC;

COMMENT ON VIEW v_analisis_entidades IS 'Vista de análisis financiero agregado por entidad';

-- Vista de análisis temporal
CREATE OR REPLACE VIEW v_analisis_temporal AS
SELECT 
    DATE_TRUNC('month', c.fecha_de_firma) as mes_firma,
    DATE_TRUNC('quarter', c.fecha_de_firma) as trimestre_firma,
    EXTRACT(YEAR FROM c.fecha_de_firma) as año_firma,
    COUNT(c.id_contrato) as contratos_firmados,
    SUM(c.valor_del_contrato) as valor_total_mes,
    AVG(c.valor_del_contrato) as valor_promedio_mes,
    COUNT(DISTINCT c.nombre_entidad) as entidades_activas,
    COUNT(DISTINCT c.proveedor_adjudicado) as proveedores_activos
FROM emp_contratos c
WHERE c.fecha_de_firma IS NOT NULL
GROUP BY DATE_TRUNC('month', c.fecha_de_firma), 
         DATE_TRUNC('quarter', c.fecha_de_firma),
         EXTRACT(YEAR FROM c.fecha_de_firma)
ORDER BY mes_firma;

COMMENT ON VIEW v_analisis_temporal IS 'Vista de análisis temporal de contratos por mes/trimestre/año';

-- Vista de proveedores con estadísticas
CREATE OR REPLACE VIEW v_analisis_proveedores AS
SELECT 
    c.proveedor_adjudicado,
    c.documento_proveedor,
    c.tipodocproveedor,
    c.es_pyme,
    c.es_grupo,
    COUNT(c.id_contrato) as total_contratos,
    SUM(c.valor_del_contrato) as valor_total_adjudicado,
    SUM(c.valor_pagado) as valor_total_pagado,
    AVG(c.valor_del_contrato) as valor_promedio_contrato,
    COUNT(DISTINCT c.nombre_entidad) as entidades_cliente,
    COUNT(DISTINCT c.departamento) as departamentos_trabajo,
    -- Distribución por tipo de contrato
    COUNT(CASE WHEN c.tipo_de_contrato = 'Obra' THEN 1 END) as contratos_obra,
    COUNT(CASE WHEN c.tipo_de_contrato = 'Prestación de servicios' THEN 1 END) as contratos_servicios,
    COUNT(CASE WHEN c.tipo_de_contrato = 'Compraventa' THEN 1 END) as contratos_compraventa,
    -- Porcentaje de ejecución
    CASE 
        WHEN SUM(c.valor_del_contrato) > 0 THEN 
            ROUND((SUM(c.valor_pagado) / SUM(c.valor_del_contrato) * 100), 2)
        ELSE 0 
    END as porcentaje_ejecucion_proveedor
FROM emp_contratos c
GROUP BY c.proveedor_adjudicado, c.documento_proveedor, c.tipodocproveedor, 
         c.es_pyme, c.es_grupo
ORDER BY valor_total_adjudicado DESC;

COMMENT ON VIEW v_analisis_proveedores IS 'Vista de análisis de proveedores con estadísticas de contratos';

-- Vistas de análisis creadas exitosamente