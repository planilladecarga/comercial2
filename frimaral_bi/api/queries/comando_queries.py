"""
Consultas SQL centralizadas para el Centro de Comando Comercial.
Nunca escribir SQL directamente en los servicios.
"""

# ─── Resumen Ejecutivo ────────────────────────────────────────────────────────

QUERY_RESUMEN_TOTALES = """
    SELECT
        (SELECT COUNT(*) FROM movimientos) AS cantidad_movimientos,
        COALESCE(SUM(kilos_netos), 0) AS kg_totales
    FROM movimientos;
"""

QUERY_RESUMEN_EXPORTACIONES = """
    SELECT COALESCE(SUM(kilos_netos), 0) AS kg_exportaciones
    FROM movimientos
    WHERE tipo_movimiento LIKE '%EXPORT%';
"""

QUERY_RESUMEN_DEPOSITO = """
    SELECT COALESCE(SUM(kilos_netos), 0) AS kg_deposito
    FROM movimientos
    WHERE solo_deposito = 1;
"""

QUERY_RESUMEN_CANTIDADES = """
    SELECT
        (SELECT COUNT(DISTINCT id_empresa) FROM dim_empresas WHERE activo = 1) AS empresas,
        (SELECT COUNT(DISTINCT id_empresa) FROM dim_empresas WHERE es_productor = 1 AND activo = 1) AS productoras,
        (SELECT COUNT(DISTINCT id_empresa) FROM dim_empresas WHERE es_certificador = 1 AND activo = 1) AS certificadores,
        (SELECT COUNT(DISTINCT id_empresa) FROM dim_empresas WHERE es_deposito = 1 AND activo = 1) AS depositos,
        (SELECT COUNT(DISTINCT COALESCE(NULLIF(TRIM(destino), ''), 'URUGUAY (Mercado Interno)')) FROM movimientos) AS mercados,
        (SELECT COUNT(*) FROM dim_productos) AS productos;
"""

QUERY_FECHA_ULTIMA_ACTUALIZACION = """
    SELECT MAX(fecha_movimiento) AS fecha_ultima
    FROM movimientos;
"""

# ─── Filtros Disponibles ─────────────────────────────────────────────────────

QUERY_FILTRO_ANOS = """
    SELECT DISTINCT anio FROM dim_calendario
    WHERE anio IN (SELECT DISTINCT anio FROM movimientos m JOIN dim_calendario cal ON m.fecha_id = cal.id_fecha)
    ORDER BY anio DESC;
"""

QUERY_FILTRO_MESES = """
    SELECT DISTINCT mes, nombre_mes FROM dim_calendario ORDER BY mes;
"""

QUERY_FILTRO_PRODUCTORES = """
    SELECT DISTINCT nro_productor, nombre_productor
    FROM (
        SELECT nro_productor, nombre_productor FROM movimientos WHERE nro_productor IS NOT NULL AND nro_productor != ''
        UNION
        SELECT nro_productor, nombre_productor FROM movimientos WHERE nombre_productor IS NOT NULL AND nombre_productor != ''
    )
    ORDER BY nombre_productor;
"""

QUERY_FILTRO_CERTIFICADORES = """
    SELECT DISTINCT id_empresa, nombre_unif
    FROM dim_empresas
    WHERE es_certificador = 1 AND activo = 1
    ORDER BY nombre_unif;
"""

QUERY_FILTRO_DEPOSITOS = """
    SELECT DISTINCT id_empresa, nombre_unif
    FROM dim_empresas
    WHERE es_deposito = 1 AND activo = 1
    ORDER BY nombre_unif;
"""

QUERY_FILTRO_MERCADOS = """
    SELECT DISTINCT COALESCE(NULLIF(TRIM(destino), ''), 'URUGUAY (Mercado Interno)') AS mercado
    FROM movimientos
    ORDER BY mercado;
"""

QUERY_FILTRO_PRODUCTOS = """
    SELECT id_producto, nombre_producto, categoria
    FROM dim_productos
    ORDER BY nombre_producto;
"""

QUERY_FILTRO_TEMPERATURAS = """
    SELECT DISTINCT temperatura FROM movimientos WHERE temperatura IS NOT NULL ORDER BY temperatura;
"""

QUERY_FILTRO_TIPOS_MOVIMIENTO = """
    SELECT DISTINCT tipo_movimiento FROM movimientos ORDER BY tipo_movimiento;
"""

# ─── Alertas del Día ─────────────────────────────────────────────────────────

QUERY_CLIENTES_NUEVOS = """
    SELECT DISTINCT
        destino AS nombre,
        MIN(fecha_movimiento) AS primera_fecha,
        SUM(kilos_netos) AS kg_total
    FROM movimientos
    WHERE empresa_id = ?
      AND destino IS NOT NULL AND TRIM(destino) != ''
    GROUP BY destino
    HAVING primera_fecha >= date('now', '-' || ? || ' days')
    ORDER BY kg_total DESC;
"""

QUERY_CLIENTES_PERDIDOS = """
    SELECT DISTINCT
        destino AS nombre,
        MAX(fecha_movimiento) AS ultima_fecha,
        SUM(kilos_netos) AS kg_total
    FROM movimientos
    WHERE empresa_id = ?
      AND destino IS NOT NULL AND TRIM(destino) != ''
    GROUP BY destino
    HAVING ultima_fecha < date('now', '-' || ? || ' days')
    ORDER BY kg_total DESC;
"""

QUERY_MERCADOS_NUEVOS = """
    SELECT DISTINCT
        COALESCE(NULLIF(TRIM(destino), ''), 'URUGUAY (Mercado Interno)') AS mercado,
        MIN(fecha_movimiento) AS primera_fecha,
        SUM(kilos_netos) AS kg_total
    FROM movimientos
    WHERE empresa_id = ?
    GROUP BY mercado
    HAVING primera_fecha >= date('now', '-' || ? || ' days')
    ORDER BY kg_total DESC;
"""

QUERY_MERCADOS_PERDIDOS = """
    SELECT DISTINCT
        COALESCE(NULLIF(TRIM(destino), ''), 'URUGUAY (Mercado Interno)') AS mercado,
        MAX(fecha_movimiento) AS ultima_fecha,
        SUM(kilos_netos) AS kg_total
    FROM movimientos
    WHERE empresa_id = ?
    GROUP BY mercado
    HAVING ultima_fecha < date('now', '-' || ? || ' days')
    ORDER BY kg_total DESC;
"""

QUERY_PRODUCTORES_NUEVOS = """
    SELECT DISTINCT
        nro_productor,
        nombre_productor,
        MIN(fecha_movimiento) AS primera_fecha,
        SUM(kilos_netos) AS kg_total
    FROM movimientos
    WHERE empresa_id = ?
      AND nro_productor IS NOT NULL AND nro_productor != ''
    GROUP BY nro_productor, nombre_productor
    HAVING primera_fecha >= date('now', '-' || ? || ' days')
    ORDER BY kg_total DESC;
"""

QUERY_PRODUCTORES_INACTIVOS = """
    SELECT DISTINCT
        nro_productor,
        nombre_productor,
        MAX(fecha_movimiento) AS ultima_fecha,
        SUM(kilos_netos) AS kg_total
    FROM movimientos
    WHERE empresa_id = ?
      AND nro_productor IS NOT NULL AND nro_productor != ''
    GROUP BY nro_productor, nombre_productor
    HAVING ultima_fecha < date('now', '-' || ? || ' days')
    ORDER BY kg_total DESC;
"""

# ─── Oportunidades ────────────────────────────────────────────────────────────

QUERY_TOP_20_PRODUCTORES_POTENCIALES = """
    -- Productores que NO trabajan con CALIRAL pero tienen volumen significativo
    SELECT
        m.nro_productor,
        m.nombre_productor,
        SUM(m.kilos_netos) AS kg_total,
        COUNT(DISTINCT m.empresa_id) AS empresas_count
    FROM movimientos m
    WHERE m.empresa_id != ?
      AND m.nro_productor NOT IN (
          SELECT DISTINCT nro_productor FROM movimientos
          WHERE empresa_id = ? AND nro_productor IS NOT NULL AND nro_productor != ''
      )
      AND m.nro_productor IS NOT NULL AND m.nro_productor != ''
    GROUP BY m.nro_productor, m.nombre_productor
    ORDER BY kg_total DESC
    LIMIT 20;
"""

QUERY_MERCADOS_NO_PARTICIPA = """
    -- Mercados donde hay volumen pero CALIRAL no participa
    SELECT
        COALESCE(NULLIF(TRIM(m.destino), ''), 'URUGUAY (Mercado Interno)') AS mercado,
        SUM(m.kilos_netos) AS kg_total
    FROM movimientos m
    WHERE m.empresa_id != ?
      AND COALESCE(NULLIF(TRIM(m.destino), ''), 'URUGUAY (Mercado Interno)')
          NOT IN (
              SELECT DISTINCT COALESCE(NULLIF(TRIM(mm.destino), ''), 'URUGUAY (Mercado Interno)')
              FROM movimientos mm
              WHERE mm.empresa_id = ?
          )
    GROUP BY mercado
    ORDER BY kg_total DESC
    LIMIT 20;
"""

QUERY_PRODUCTORES_COMPETENCIA = """
    -- Productores que trabajan con la competencia
    SELECT
        m.nro_productor,
        m.nombre_productor,
        SUM(m.kilos_netos) AS kg_total,
        COUNT(DISTINCT m.empresa_id) AS empresas_count
    FROM movimientos m
    WHERE m.empresa_id = ?
      AND m.nro_productor IN (
          SELECT DISTINCT nro_productor FROM movimientos
          WHERE empresa_id != ? AND nro_productor IS NOT NULL AND nro_productor != ''
      )
    GROUP BY m.nro_productor, m.nombre_productor
    ORDER BY kg_total DESC
    LIMIT 20;
"""

QUERY_PRODUCTORES_COMPARTIDOS = """
    -- Productores que trabajan con múltiples empresas
    SELECT
        m.nro_productor,
        m.nombre_productor,
        SUM(m.kilos_netos) AS kg_total,
        COUNT(DISTINCT m.empresa_id) AS empresas_count
    FROM movimientos m
    WHERE m.empresa_id = ?
      AND m.nro_productor IN (
          SELECT nro_productor FROM movimientos
          WHERE empresa_id != ? AND nro_productor IS NOT NULL AND nro_productor != ''
          GROUP BY nro_productor
          HAVING COUNT(DISTINCT empresa_id) >= 1
      )
    GROUP BY m.nro_productor, m.nombre_productor
    ORDER BY kg_total DESC
    LIMIT 20;
"""

QUERY_CLIENTES_POTENCIALES = """
    -- Clientes que tienen volumen con competidores pero no con CALIRAL
    SELECT
        m.destino AS nombre,
        SUM(m.kilos_netos) AS kg_total
    FROM movimientos m
    WHERE m.empresa_id != ?
      AND m.destino IS NOT NULL AND TRIM(m.destino) != ''
      AND m.destino NOT IN (
          SELECT DISTINCT destino FROM movimientos
          WHERE empresa_id = ? AND destino IS NOT NULL AND TRIM(destino) != ''
      )
    GROUP BY m.destino
    ORDER BY kg_total DESC
    LIMIT 20;
"""

# ─── Comparación Competitiva ───────────────────────────────────────────────────

QUERY_COMPARACION_KG = """
    SELECT
        e.id_empresa,
        e.nombre_unif,
        COALESCE(SUM(m.kilos_netos), 0) AS kg_total
    FROM dim_empresas e
    LEFT JOIN movimientos m ON e.id_empresa = m.empresa_id
    WHERE e.id_empresa IN (?, ?)
    GROUP BY e.id_empresa, e.nombre_unif;
"""

QUERY_PARTICIPACION_MERCADO = """
    WITH total_kg AS (
        SELECT SUM(kilos_netos) AS total FROM movimientos
    )
    SELECT
        COALESCE(NULLIF(TRIM(m.destino), ''), 'URUGUAY (Mercado Interno)') AS mercado,
        SUM(m.kilos_netos) AS kg_empresa,
        (SELECT total FROM total_kg) AS kg_total,
        ROUND(SUM(m.kilos_netos) * 100.0 / (SELECT total FROM total_kg), 2) AS participacion_pct
    FROM movimientos m
    WHERE m.empresa_id = ?
    GROUP BY mercado
    ORDER BY kg_empresa DESC;
"""

QUERY_COMPETIDORES_COMPARACION = """
    SELECT
        e.id_empresa,
        e.nombre_unif,
        COUNT(DISTINCT m.nro_productor) AS productores_count,
        COUNT(DISTINCT COALESCE(NULLIF(TRIM(m.destino), ''), 'URUGUAY (Mercado Interno)')) AS mercados_count,
        COUNT(DISTINCT m.destino) AS clientes_count,
        COUNT(DISTINCT m.producto_id) AS productos_count
    FROM dim_empresas e
    LEFT JOIN movimientos m ON e.id_empresa = m.empresa_id
    WHERE e.id_empresa = ?
    GROUP BY e.id_empresa, e.nombre_unif;
"""

# ─── Indicadores / KPIs ───────────────────────────────────────────────────────

QUERY_INDICADORES_PARTICIPACION = """
    WITH kg_total AS (
        SELECT SUM(kilos_netos) AS total FROM movimientos
    ),
    kg_empresa AS (
        SELECT SUM(kilos_netos) AS total FROM movimientos WHERE empresa_id = ?
    )
    SELECT
        (SELECT total FROM kg_empresa) AS kg_empresa,
        (SELECT total FROM kg_total) AS kg_total,
        ROUND((SELECT total FROM kg_empresa) * 100.0 / NULLIF((SELECT total FROM kg_total), 0), 2) AS participacion;
"""

QUERY_INDICADORES_DIVERSIFICACION = """
    -- Índice Herfindahl (inverso) - mayor diversificación = mayor índice
    WITH participaciones AS (
        SELECT
            empresa_id,
            SUM(kilos_netos) AS kg
        FROM movimientos
        GROUP BY empresa_id
    ),
    total AS (
        SELECT SUM(kg) AS total FROM participaciones
    ),
    hhi AS (
        SELECT SUM(POWER(p.kg * 100.0 / NULLIF(t.total, 0), 2)) AS hhi
        FROM participaciones p, total t
    )
    SELECT ROUND(10000 - hhi, 0) AS indice_diversificacion
    FROM hhi;
"""

QUERY_INDICADORES_CONCENTRACION = """
    -- Concentración de mercado de una empresa
    WITH mercado_principal AS (
        SELECT SUM(kilos_netos) AS kg
        FROM movimientos
        WHERE empresa_id = ?
        GROUP BY COALESCE(NULLIF(TRIM(destino), ''), 'URUGUAY (Mercado Interno)')
        ORDER BY kg DESC
        LIMIT 1
    ),
    total_empresa AS (
        SELECT SUM(kilos_netos) AS kg FROM movimientos WHERE empresa_id = ?
    )
    SELECT ROUND(
        (SELECT kg FROM mercado_principal) * 100.0 /
        NULLIF((SELECT kg FROM total_empresa), 0)
    , 2) AS concentracion;
"""

QUERY_INDICADORES_FIDELIDAD = """
    -- % de productores que solo trabajan con esta empresa
    WITH productores_empresa AS (
        SELECT nro_productor, SUM(kilos_netos) AS kg
        FROM movimientos
        WHERE empresa_id = ?
        GROUP BY nro_productor
    ),
    productores_totales AS (
        SELECT nro_productor, SUM(kilos_netos) AS kg
        FROM movimientos
        GROUP BY nro_productor
        HAVING COUNT(DISTINCT empresa_id) = 1
    )
    SELECT ROUND(
        COUNT(*) * 100.0 / NULLIF((SELECT COUNT(*) FROM productores_totales), 0)
    , 2) AS indice_fidelidad
    FROM productores_totales
    WHERE nro_productor IN (SELECT nro_productor FROM productores_empresa);
"""

QUERY_INDICADORES_CRECIMIENTO = """
    -- Crecimiento vs mes anterior
    WITH kg_mes_actual AS (
        SELECT COALESCE(SUM(kilos_netos), 0) AS kg
        FROM movimientos m
        JOIN dim_calendario cal ON m.fecha_id = cal.id_fecha
        WHERE m.empresa_id = ?
          AND cal.anio = (SELECT MAX(anio) FROM dim_calendario WHERE id_fecha IN (SELECT fecha_id FROM movimientos WHERE empresa_id = ?))
          AND cal.mes = (SELECT MAX(mes) FROM dim_calendario WHERE id_fecha IN (SELECT fecha_id FROM movimientos WHERE empresa_id = ?))
    ),
    kg_mes_anterior AS (
        SELECT COALESCE(SUM(kilos_netos), 0) AS kg
        FROM movimientos m
        JOIN dim_calendario cal ON m.fecha_id = cal.id_fecha
        WHERE m.empresa_id = ?
          AND cal.anio = (SELECT MAX(anio) FROM dim_calendario WHERE id_fecha IN (SELECT fecha_id FROM movimientos WHERE empresa_id = ?))
          AND cal.mes = (SELECT MAX(mes) - 1 FROM dim_calendario WHERE id_fecha IN (SELECT fecha_id FROM movimientos WHERE empresa_id = ?))
    )
    SELECT
        (SELECT kg FROM kg_mes_actual) AS kg_actual,
        (SELECT kg FROM kg_mes_anterior) AS kg_anterior,
        CASE WHEN (SELECT kg FROM kg_mes_anterior) > 0
             THEN ROUND(((SELECT kg FROM kg_mes_actual) - (SELECT kg FROM kg_mes_anterior)) * 100.0 / (SELECT kg FROM kg_mes_anterior), 2)
             ELSE 0 END AS crecimiento_pct;
"""

QUERY_CAMBIO_DEPOSITO = """
    -- Productores que cambiaron de depósito (diferente empresa como establecimiento)
    WITH primeros_depositos AS (
        SELECT nro_productor, nombre_establecimiento, MIN(fecha_movimiento) as fecha
        FROM movimientos
        WHERE empresa_id = ? AND solo_deposito = 1
        GROUP BY nro_productor
    ),
    ultimos_depositos AS (
        SELECT nro_productor, nombre_establecimiento, MAX(fecha_movimiento) as fecha
        FROM movimientos
        WHERE empresa_id = ? AND solo_deposito = 1
        GROUP BY nro_productor
    )
    SELECT
        p.nro_productor,
        p.nombre_productor,
        p.nombre_establecimiento AS deposito_actual
    FROM (
        SELECT u.nro_productor, u.nombre_establecimiento, m.nombre_productor
        FROM ultimos_depositos u
        JOIN movimientos m ON u.nro_productor = m.nro_productor AND m.empresa_id = ?
        WHERE u.nombre_establecimiento != (SELECT nombre_establecimiento FROM primeros_depositos WHERE nro_productor = u.nro_productor)
    ) p
    LIMIT 10;
"""

# ─── Mapa Comercial ────────────────────────────────────────────────────────────

QUERY_MAPA_PAISES = """
    SELECT
        COALESCE(NULLIF(TRIM(m.destino), ''), 'URUGUAY (Mercado Interno)') AS pais,
        SUM(m.kilos_netos) AS kg_total
    FROM movimientos m
    GROUP BY pais
    ORDER BY kg_total DESC;
"""

QUERY_MAPA_CRECIMIENTO = """
    -- Crecimiento por país vs período anterior
    WITH kg_actual AS (
        SELECT
            COALESCE(NULLIF(TRIM(m.destino), ''), 'URUGUAY (Mercado Interno)') AS pais,
            SUM(m.kilos_netos) AS kg
        FROM movimientos m
        JOIN dim_calendario cal ON m.fecha_id = cal.id_fecha
        WHERE cal.anio = (SELECT MAX(anio) FROM dim_calendario WHERE id_fecha IN (SELECT fecha_id FROM movimientos))
        GROUP BY pais
    ),
    kg_anterior AS (
        SELECT
            COALESCE(NULLIF(TRIM(m.destino), ''), 'URUGUAY (Mercado Interno)') AS pais,
            SUM(m.kilos_netos) AS kg
        FROM movimientos m
        JOIN dim_calendario cal ON m.fecha_id = cal.id_fecha
        WHERE cal.anio = (SELECT MAX(anio) - 1 FROM dim_calendario WHERE id_fecha IN (SELECT fecha_id FROM movimientos))
        GROUP BY pais
    )
    SELECT
        a.pais,
        a.kg AS kg_actual,
        COALESCE(b.kg, 0) AS kg_anterior,
        CASE WHEN COALESCE(b.kg, 0) > 0
             THEN ROUND((a.kg - b.kg) * 100.0 / b.kg, 2)
             ELSE 0 END AS crecimiento_pct
    FROM kg_actual a
    LEFT JOIN kg_anterior b ON a.pais = b.pais
    ORDER BY a.kg DESC;
"""

# ─── Evolución ────────────────────────────────────────────────────────────────

QUERY_EVOLUCION_MENSUAL = """
    SELECT
        cal.anio,
        cal.mes,
        cal.nombre_mes,
        SUM(m.kilos_netos) AS kg,
        COUNT(DISTINCT m.destino) AS clientes_count,
        COUNT(DISTINCT COALESCE(NULLIF(TRIM(m.destino), ''), 'URUGUAY (Mercado Interno)')) AS mercados_count,
        COUNT(DISTINCT m.nro_productor) AS productores_count
    FROM movimientos m
    JOIN dim_calendario cal ON m.fecha_id = cal.id_fecha
    GROUP BY cal.anio, cal.mes
    ORDER BY cal.anio ASC, cal.mes ASC;
"""

# ─── Rankings ────────────────────────────────────────────────────────────────

QUERY_RANKING_PRODUCTORES = """
    SELECT
        nro_productor,
        nombre_productor,
        SUM(kilos_netos) AS kg_total,
        COUNT(*) AS cantidad_movimientos
    FROM movimientos
    WHERE nro_productor IS NOT NULL AND nro_productor != ''
    GROUP BY nro_productor, nombre_productor
    ORDER BY kg_total DESC
    LIMIT 10;
"""

QUERY_RANKING_DEPOSITOS = """
    SELECT
        nombre_establecimiento AS nombre,
        SUM(kilos_netos) AS kg_total,
        COUNT(*) AS cantidad_movimientos
    FROM movimientos
    WHERE solo_deposito = 1 AND nombre_establecimiento IS NOT NULL
    GROUP BY nombre_establecimiento
    ORDER BY kg_total DESC
    LIMIT 10;
"""

QUERY_RANKING_CERTIFICADORES = """
    SELECT
        nombre_establecimiento AS nombre,
        SUM(kilos_netos) AS kg_total,
        COUNT(*) AS cantidad_movimientos
    FROM movimientos
    WHERE nro_certificado IS NOT NULL AND nro_certificado != ''
    GROUP BY nombre_establecimiento
    ORDER BY kg_total DESC
    LIMIT 10;
"""

QUERY_RANKING_MERCADOS = """
    SELECT
        COALESCE(NULLIF(TRIM(destino), ''), 'URUGUAY (Mercado Interno)') AS nombre,
        SUM(kilos_netos) AS kg_total,
        COUNT(*) AS cantidad_movimientos
    FROM movimientos
    GROUP BY nombre
    ORDER BY kg_total DESC
    LIMIT 10;
"""

QUERY_RANKING_PRODUCTOS = """
    SELECT
        p.nombre_producto AS nombre,
        SUM(m.kilos_netos) AS kg_total,
        COUNT(*) AS cantidad_movimientos
    FROM movimientos m
    JOIN dim_productos p ON m.producto_id = p.id_producto
    GROUP BY p.nombre_producto
    ORDER BY kg_total DESC
    LIMIT 10;
"""

# ─── Variación de KG ─────────────────────────────────────────────────────────

QUERY_AUMENTOS_IMPORTANTES = """
    WITH mes_actual AS (
        SELECT
            COALESCE(NULLIF(TRIM(m.destino), ''), 'URUGUAY (Mercado Interno)') AS entidad,
            SUM(m.kilos_netos) AS kg
        FROM movimientos m
        JOIN dim_calendario cal ON m.fecha_id = cal.id_fecha
        WHERE m.empresa_id = ?
          AND cal.anio = (SELECT MAX(anio) FROM dim_calendario WHERE id_fecha IN (SELECT fecha_id FROM movimientos WHERE empresa_id = ?))
          AND cal.mes = (SELECT MAX(mes) FROM dim_calendario WHERE id_fecha IN (SELECT fecha_id FROM movimientos WHERE empresa_id = ?))
        GROUP BY entidad
    ),
    mes_anterior AS (
        SELECT
            COALESCE(NULLIF(TRIM(m.destino), ''), 'URUGUAY (Mercado Interno)') AS entidad,
            SUM(m.kilos_netos) AS kg
        FROM movimientos m
        JOIN dim_calendario cal ON m.fecha_id = cal.id_fecha
        WHERE m.empresa_id = ?
          AND cal.anio = (SELECT MAX(anio) FROM dim_calendario WHERE id_fecha IN (SELECT fecha_id FROM movimientos WHERE empresa_id = ?))
          AND cal.mes = (SELECT MAX(mes) - 1 FROM dim_calendario WHERE id_fecha IN (SELECT fecha_id FROM movimientos WHERE empresa_id = ?))
        GROUP BY entidad
    )
    SELECT
        a.entidad,
        a.kg AS kg_actual,
        COALESCE(b.kg, 0) AS kg_anterior,
        CASE WHEN COALESCE(b.kg, 0) > 0
             THEN ROUND((a.kg - b.kg) * 100.0 / b.kg, 2)
             ELSE 0 END AS variacion_pct
    FROM mes_actual a
    LEFT JOIN mes_anterior b ON a.entidad = b.entidad
    WHERE variacion_pct > ?
    ORDER BY variacion_pct DESC
    LIMIT 10;
"""

QUERY_DISMINUCIONES_IMPORTANTES = """
    WITH mes_actual AS (
        SELECT
            COALESCE(NULLIF(TRIM(m.destino), ''), 'URUGUAY (Mercado Interno)') AS entidad,
            SUM(m.kilos_netos) AS kg
        FROM movimientos m
        JOIN dim_calendario cal ON m.fecha_id = cal.id_fecha
        WHERE m.empresa_id = ?
          AND cal.anio = (SELECT MAX(anio) FROM dim_calendario WHERE id_fecha IN (SELECT fecha_id FROM movimientos WHERE empresa_id = ?))
          AND cal.mes = (SELECT MAX(mes) FROM dim_calendario WHERE id_fecha IN (SELECT fecha_id FROM movimientos WHERE empresa_id = ?))
        GROUP BY entidad
    ),
    mes_anterior AS (
        SELECT
            COALESCE(NULLIF(TRIM(m.destino), ''), 'URUGUAY (Mercado Interno)') AS entidad,
            SUM(m.kilos_netos) AS kg
        FROM movimientos m
        JOIN dim_calendario cal ON m.fecha_id = cal.id_fecha
        WHERE m.empresa_id = ?
          AND cal.anio = (SELECT MAX(anio) FROM dim_calendario WHERE id_fecha IN (SELECT fecha_id FROM movimientos WHERE empresa_id = ?))
          AND cal.mes = (SELECT MAX(mes) - 1 FROM dim_calendario WHERE id_fecha IN (SELECT fecha_id FROM movimientos WHERE empresa_id = ?))
        GROUP BY entidad
    )
    SELECT
        a.entidad,
        a.kg AS kg_actual,
        COALESCE(b.kg, 0) AS kg_anterior,
        CASE WHEN COALESCE(b.kg, 0) > 0
             THEN ROUND((a.kg - b.kg) * 100.0 / b.kg, 2)
             ELSE 0 END AS variacion_pct
    FROM mes_actual a
    LEFT JOIN mes_anterior b ON a.entidad = b.entidad
    WHERE variacion_pct < ?
    ORDER BY variacion_pct ASC
    LIMIT 10;
"""

# ─── Empresa Principal (CALIRAL) ─────────────────────────────────────────────

QUERY_EMPRESA_CALIRAL = """
    SELECT id_empresa, nombre_unif
    FROM dim_empresas
    WHERE nombre_unif LIKE '%CALIRAL%'
       OR nombre_unif LIKE '%FRIMARAL%'
    LIMIT 1;
"""

QUERY_LISTAR_EMPRESAS = """
    SELECT id_empresa, nombre_unif
    FROM dim_empresas
    WHERE activo = 1
    ORDER BY nombre_unif;
"""
