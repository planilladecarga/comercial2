"""
=================================================================================
repositorio.py — Consultas SQL compartidas para Inteligencia Competitiva
=================================================================================

Consulta y reutiliza TODAS las queries del repositorio de empresa360.
Aquí se agregan únicamente las queries específicas de inteligencia competitiva
que no existen en empresa360.

Responsabilidad:
    • Queries de comparación entre empresas
    • Queries de detección de cambios (nuevos/perdidos)
    • Queries de ranking de oportunidades
    • Queries de riesgos comerciales

No repite ninguna query ya definida en empresa360/repositorio.py.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Optional, Any
from contextlib import contextmanager

# ─────────────────────────────────────────────────────────────────────────────
# QUERIES SQL — Inteligencia Competitiva
# ─────────────────────────────────────────────────────────────────────────────

# ── Productores ────────────────────────────────────────────────────────────

QUERY_PRODUCTORES_EMPRESA = """
    SELECT DISTINCT
        m.nro_productor,
        m.nombre_productor,
        SUM(m.kilos_netos)  AS kg_total,
        COUNT(*)             AS cantidad_movimientos,
        MIN(m.fecha_movimiento) AS primera_fecha,
        MAX(m.fecha_movimiento) AS ultima_fecha
    FROM movimientos m
    WHERE m.empresa_id = ?
    GROUP BY m.nro_productor, m.nombre_productor
    ORDER BY kg_total DESC;
"""

QUERY_PRODUCTORES_COMPARTIDOS = """
    SELECT
        m1.nro_productor,
        m1.nombre_productor,
        SUM(m1.kilos_netos) AS kg_a,
        SUM(m2.kilos_netos) AS kg_b,
        COUNT(DISTINCT m1.empresa_id) AS empresas_compartidas
    FROM movimientos m1
    JOIN movimientos m2
      ON m1.nro_productor = m2.nro_productor
     AND m2.empresa_id = ?
    WHERE m1.empresa_id = ?
    GROUP BY m1.nro_productor, m1.nombre_productor;
"""

QUERY_PRODUCTORES_EXCLUSIVOS_A = """
    SELECT
        m.nro_productor,
        m.nombre_productor,
        SUM(m.kilos_netos) AS kg_total,
        COUNT(*) AS cantidad_movimientos
    FROM movimientos m
    WHERE m.empresa_id = ?
      AND m.nro_productor NOT IN (
          SELECT DISTINCT nro_productor FROM movimientos
          WHERE empresa_id = ? AND nro_productor IS NOT NULL
      )
    GROUP BY m.nro_productor, m.nombre_productor
    ORDER BY kg_total DESC;
"""

QUERY_PRODUCTORES_NO_USAN_EMPRESA = """
    SELECT DISTINCT
        m.nro_productor,
        m.nombre_productor,
        SUM(m.kilos_netos) AS kg_total,
        MIN(m.fecha_movimiento) AS primera_fecha
    FROM movimientos m
    WHERE m.empresa_id != ?
      AND m.nro_productor NOT IN (
          SELECT DISTINCT nro_productor FROM movimientos
          WHERE empresa_id = ? AND nro_productor IS NOT NULL
      )
    GROUP BY m.nro_productor, m.nombre_productor
    ORDER BY kg_total DESC;
"""

QUERY_PRODUCTORES_NUEVOS = """
    -- Productores que aparecen por primera vez con esta empresa en los últimos N días
    SELECT
        m.nro_productor,
        m.nombre_productor,
        MIN(m.fecha_movimiento) AS primera_fecha,
        SUM(m.kilos_netos) AS kg_total,
        COUNT(*) AS movimientos
    FROM movimientos m
    WHERE m.empresa_id = ?
    GROUP BY m.nro_productor, m.nombre_productor
    HAVING primera_fecha >= date('now', ?)
    ORDER BY kg_total DESC;
"""

QUERY_PRODUCTORES_QUE_ABANDONARON = """
    -- Productores que trabajó esta empresa pero ya no tienen movimientos con ella
    -- en los últimos N días (comparado con fecha anterior)
    SELECT
        m.nro_productor,
        m.nombre_productor,
        MAX(m.fecha_movimiento) AS ultima_fecha,
        SUM(m.kilos_netos) AS kg_total
    FROM movimientos m
    WHERE m.empresa_id = ?
    GROUP BY m.nro_productor, m.nombre_productor
    HAVING ultima_fecha < date('now', ?);
"""

QUERY_PRODUCTORES_MULTI_DEPOSITO = """
    -- Productores que trabajan con más de una empresa
    SELECT
        m.nro_productor,
        m.nombre_productor,
        COUNT(DISTINCT m.empresa_id) AS cantidad_empresas,
        SUM(m.kilos_netos) AS kg_total
    FROM movimientos m
    GROUP BY m.nro_productor, m.nombre_productor
    HAVING cantidad_empresas > 1
    ORDER BY kg_total DESC;
"""

QUERY_TOP_PRODUCTORES_EMPRESA = """
    SELECT
        m.nro_productor,
        m.nombre_productor,
        SUM(m.kilos_netos) AS kg_total,
        COUNT(*) AS cantidad_movimientos
    FROM movimientos m
    WHERE m.empresa_id = ?
    GROUP BY m.nro_productor, m.nombre_productor
    ORDER BY kg_total DESC
    LIMIT ?;
"""

# ── Mercados ──────────────────────────────────────────────────────────────

QUERY_MERCADOS_EMPRESA = """
    SELECT
        COALESCE(NULLIF(TRIM(m.destino), ''), 'URUGUAY (Mercado Interno)') AS mercado,
        SUM(m.kilos_netos)  AS kg_total,
        COUNT(*)             AS cantidad_movimientos
    FROM movimientos m
    WHERE m.empresa_id = ?
    GROUP BY mercado
    ORDER BY kg_total DESC;
"""

QUERY_MERCADOS_COMPARTIDOS = """
    SELECT
        COALESCE(NULLIF(TRIM(m1.destino), ''), 'URUGUAY (Mercado Interno)') AS mercado,
        SUM(m1.kilos_netos) AS kg_a,
        SUM(m2.kilos_netos) AS kg_b
    FROM movimientos m1
    JOIN movimientos m2
      ON COALESCE(NULLIF(TRIM(m1.destino), ''), 'URUGUAY (Mercado Interno)')
      = COALESCE(NULLIF(TRIM(m2.destino), ''), 'URUGUAY (Mercado Interno)')
     AND m2.empresa_id = ?
    WHERE m1.empresa_id = ?
    GROUP BY mercado;
"""

QUERY_MERCADOS_EXCLUSIVOS_A = """
    SELECT
        COALESCE(NULLIF(TRIM(m.destino), ''), 'URUGUAY (Mercado Interno)') AS mercado,
        SUM(m.kilos_netos) AS kg_total
    FROM movimientos m
    WHERE m.empresa_id = ?
      AND COALESCE(NULLIF(TRIM(m.destino), ''), 'URUGUAY (Mercado Interno)')
          NOT IN (
              SELECT DISTINCT COALESCE(NULLIF(TRIM(mm.destino), ''), 'URUGUAY (Mercado Interno)')
              FROM movimientos mm
              WHERE mm.empresa_id = ?
          )
    GROUP BY mercado
    ORDER BY kg_total DESC;
"""

QUERY_MERCADOS_NO_PARTICIPA = """
    -- Mercados donde opera la competencia pero NO esta empresa
    SELECT DISTINCT
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
    ORDER BY kg_total DESC;
"""

# ── Clientes ───────────────────────────────────────────────────────────────

QUERY_CLIENTES_EMPRESA = """
    SELECT
        m.destino AS cliente,
        SUM(m.kilos_netos)  AS kg_total,
        COUNT(*)             AS cantidad_movimientos
    FROM movimientos m
    WHERE m.empresa_id = ?
      AND m.destino IS NOT NULL
      AND TRIM(m.destino) != ''
    GROUP BY m.destino
    ORDER BY kg_total DESC;
"""

QUERY_CLIENTES_COMPARTIDOS = """
    SELECT
        m1.destino AS cliente,
        SUM(m1.kilos_netos) AS kg_a,
        SUM(m2.kilos_netos) AS kg_b
    FROM movimientos m1
    JOIN movimientos m2
      ON COALESCE(NULLIF(TRIM(m1.destino), ''), 'N/D')
     = COALESCE(NULLIF(TRIM(m2.destino), ''), 'N/D')
     AND m2.empresa_id = ?
    WHERE m1.empresa_id = ?
      AND m1.destino IS NOT NULL AND TRIM(m1.destino) != ''
    GROUP BY m1.destino;
"""

QUERY_CLIENTES_EXCLUSIVOS_A = """
    SELECT
        m.destino AS cliente,
        SUM(m.kilos_netos) AS kg_total
    FROM movimientos m
    WHERE m.empresa_id = ?
      AND m.destino IS NOT NULL
      AND TRIM(m.destino) != ''
      AND COALESCE(NULLIF(TRIM(m.destino), ''), 'N/D')
          NOT IN (
              SELECT DISTINCT COALESCE(NULLIF(TRIM(mm.destino), ''), 'N/D')
              FROM movimientos mm
              WHERE mm.empresa_id = ?
                AND mm.destino IS NOT NULL AND TRIM(mm.destino) != ''
          )
    GROUP BY m.destino
    ORDER BY kg_total DESC;
"""

QUERY_CLIENTES_NUEVOS = """
    SELECT
        m.destino AS cliente,
        MIN(m.fecha_movimiento) AS primera_fecha,
        SUM(m.kilos_netos) AS kg_total
    FROM movimientos m
    WHERE m.empresa_id = ?
      AND m.destino IS NOT NULL
      AND TRIM(m.destino) != ''
    GROUP BY m.destino
    HAVING primera_fecha >= date('now', ?)
    ORDER BY kg_total DESC;
"""

QUERY_CLIENTES_PERDIDOS = """
    SELECT
        m.destino AS cliente,
        MAX(m.fecha_movimiento) AS ultima_fecha,
        SUM(m.kilos_netos) AS kg_total
    FROM movimientos m
    WHERE m.empresa_id = ?
      AND m.destino IS NOT NULL
      AND TRIM(m.destino) != ''
    GROUP BY m.destino
    HAVING ultima_fecha < date('now', ?)
    ORDER BY kg_total DESC;
"""

QUERY_CLIENTES_DECRECIENDO = """
    -- Clientes cuya participación kg cayó más del 20% de un período a otro
    WITH cliente_periodo AS (
        SELECT
            m.destino,
            cal.anio,
            cal.mes,
            SUM(m.kilos_netos) AS kg
        FROM movimientos m
        JOIN dim_calendario cal ON m.fecha_id = cal.id_fecha
        WHERE m.empresa_id = ?
          AND m.destino IS NOT NULL AND TRIM(m.destino) != ''
        GROUP BY m.destino, cal.anio, cal.mes
    ),
    cliente_variacion AS (
        SELECT
            a.destino,
            a.anio  AS anio_actual,
            a.mes   AS mes_actual,
            a.kg    AS kg_actual,
            b.kg    AS kg_anterior,
            ROUND((a.kg - b.kg) * 100.0 / NULLIF(b.kg, 0), 2) AS variacion_pct
        FROM cliente_periodo a
        JOIN cliente_periodo b
          ON a.destino = b.destino
         AND a.mes = CASE WHEN b.mes = 12 THEN 1 ELSE b.mes + 1 END
         AND a.anio = CASE WHEN b.mes = 12 THEN b.anio + 1 ELSE b.anio END
        WHERE a.anio = (SELECT MAX(anio) FROM cliente_periodo)
          AND a.mes  = (SELECT MAX(mes)  FROM cliente_periodo WHERE anio = a.anio)
    )
    SELECT * FROM cliente_variacion
    WHERE variacion_pct < -20
    ORDER BY variacion_pct ASC;
"""

# ── Productos ─────────────────────────────────────────────────────────────

QUERY_PRODUCTOS_EMPRESA = """
    SELECT
        p.nombre_producto AS producto,
        p.categoria,
        SUM(m.kilos_netos) AS kg_total,
        COUNT(*) AS cantidad_movimientos
    FROM movimientos m
    JOIN dim_productos p ON m.producto_id = p.id_producto
    WHERE m.empresa_id = ?
    GROUP BY p.nombre_producto, p.categoria
    ORDER BY kg_total DESC;
"""

QUERY_PRODUCTOS_COMPARTIDOS = """
    SELECT
        p.nombre_producto AS producto,
        SUM(m1.kilos_netos) AS kg_a,
        SUM(m2.kilos_netos) AS kg_b
    FROM movimientos m1
    JOIN movimientos m2
      ON m1.producto_id = m2.producto_id
     AND m2.empresa_id = ?
    JOIN dim_productos p ON m1.producto_id = p.id_producto
    WHERE m1.empresa_id = ?
    GROUP BY p.nombre_producto;
"""

# ── Volúmenes ──────────────────────────────────────────────────────────────

QUERY_KG_EMPRESA_POR_MES = """
    SELECT
        cal.anio,
        cal.mes,
        SUM(m.kilos_netos) AS kg_total
    FROM movimientos m
    JOIN dim_calendario cal ON m.fecha_id = cal.id_fecha
    WHERE m.empresa_id = ?
    GROUP BY cal.anio, cal.mes
    ORDER BY cal.anio ASC, cal.mes ASC;
"""

QUERY_KG_TOTAL_EMPRESA = """
    SELECT COALESCE(SUM(kilos_netos), 0) AS kg_total
    FROM movimientos
    WHERE empresa_id = ?;
"""

QUERY_PORCENTAJE_PASO_POR_EMPRESA = """
    -- Kg de empresa B que pasaron por empresa A
    WITH paso_b_por_a AS (
        SELECT SUM(m.kilos_netos) AS kg
        FROM movimientos m
        WHERE m.empresa_id = ?
          AND m.nro_productor IN (
              SELECT DISTINCT nro_productor FROM movimientos
              WHERE empresa_id = ?
          )
    ),
    total_b AS (
        SELECT SUM(m.kilos_netos) AS kg
        FROM movimientos m
        WHERE m.empresa_id = ?
    )
    SELECT
        ROUND((SELECT kg FROM paso_b_por_a) * 100.0 /
              NULLIF((SELECT kg FROM total_b), 0), 2) AS porcentaje;
"""

QUERY_EXPORTACION_SIN_PASAR = """
    -- Kg exportados por B que NO pasaron por A
    SELECT COALESCE(SUM(m.kilos_netos), 0) AS kg_exportacion_sin_a
    FROM movimientos m
    WHERE m.empresa_id = ?
      AND m.tipo_movimiento LIKE '%EXPORT%'
      AND m.nro_productor NOT IN (
          SELECT DISTINCT nro_productor FROM movimientos
          WHERE empresa_id = ?
      );
"""

QUERY_RANKING_PRODUCTORES_GLOBAL = """
    SELECT
        m.nro_productor,
        m.nombre_productor,
        SUM(m.kilos_netos) AS kg_total,
        COUNT(DISTINCT m.empresa_id) AS empresas_activas,
        MAX(m.fecha_movimiento) AS ultima_fecha
    FROM movimientos m
    GROUP BY m.nro_productor, m.nombre_productor
    ORDER BY kg_total DESC
    LIMIT ?;
"""

QUERY_PRODUCTORES_USAN_ARBIZA = """
    SELECT DISTINCT
        m.nro_productor,
        m.nombre_productor,
        SUM(m.kilos_netos) AS kg_total
    FROM movimientos m
    WHERE m.empresa_id = ?
    GROUP BY m.nro_productor, m.nombre_productor
    ORDER BY kg_total DESC;
"""

QUERY_PRODUCTORES_EXPORTAN_MERCADO_NO_A = """
    -- Productores que exportan a mercados donde A no participa
    SELECT DISTINCT
        m.nro_productor,
        m.nombre_productor,
        SUM(m.kilos_netos) AS kg_total,
        m.destino AS mercado
    FROM movimientos m
    WHERE m.empresa_id = ?
      AND m.tipo_movimiento LIKE '%EXPORT%'
      AND m.destino NOT IN (
          SELECT DISTINCT COALESCE(NULLIF(TRIM(mm.destino), ''), 'URUGUAY (Mercado Interno)')
          FROM movimientos mm
          WHERE mm.empresa_id = ?
            AND mm.tipo_movimiento LIKE '%EXPORT%'
      )
    GROUP BY m.nro_productor, m.nombre_productor, m.destino
    ORDER BY kg_total DESC;
"""

QUERY_CRECIMIENTO_PRODUCTORES = """
    WITH prod_mes AS (
        SELECT
            m.nro_productor,
            cal.anio,
            cal.mes,
            SUM(m.kilos_netos) AS kg
        FROM movimientos m
        JOIN dim_calendario cal ON m.fecha_id = cal.id_fecha
        WHERE m.empresa_id = ?
        GROUP BY m.nro_productor, cal.anio, cal.mes
    ),
    crecimiento AS (
        SELECT
            a.nro_productor,
            a.kg    AS kg_actual,
            b.kg    AS kg_anterior,
            ROUND((a.kg - b.kg) * 100.0 / NULLIF(b.kg, 0), 2) AS crecimiento_pct
        FROM prod_mes a
        JOIN prod_mes b
          ON a.nro_productor = b.nro_productor
         AND a.mes  = CASE WHEN b.mes  = 12 THEN 1  ELSE b.mes  + 1 END
         AND a.anio = CASE WHEN b.mes  = 12 THEN b.anio + 1 ELSE b.anio END
        WHERE a.anio = (SELECT MAX(anio) FROM prod_mes)
          AND a.mes  = (SELECT MAX(mes)  FROM prod_mes WHERE anio = a.anio)
    )
    SELECT * FROM crecimiento
    WHERE crecimiento_pct > 30
    ORDER BY crecimiento_pct DESC
    LIMIT 10;
"""

QUERY_MERCADOS_NUEVOS = """
    SELECT
        COALESCE(NULLIF(TRIM(m.destino), ''), 'URUGUAY (Mercado Interno)') AS mercado,
        MIN(m.fecha_movimiento) AS primera_fecha,
        SUM(m.kilos_netos) AS kg_total
    FROM movimientos m
    WHERE m.empresa_id = ?
    GROUP BY mercado
    HAVING primera_fecha >= date('now', ?)
    ORDER BY kg_total DESC;
"""

QUERY_MERCADOS_PERDIDOS = """
    SELECT
        COALESCE(NULLIF(TRIM(m.destino), ''), 'URUGUAY (Mercado Interno)') AS mercado,
        MAX(m.fecha_movimiento) AS ultima_fecha,
        SUM(m.kilos_netos) AS kg_total
    FROM movimientos m
    WHERE m.empresa_id = ?
    GROUP BY mercado
    HAVING ultima_fecha < date('now', ?)
    ORDER BY kg_total DESC;
"""

QUERY_EMPRESAS_SIN_DATOS = """
    -- Empresas con movimientos que no han tenido actividad reciente
    SELECT
        e.id_empresa,
        e.nombre_unif,
        MAX(m.fecha_movimiento) AS ultima_fecha,
        SUM(m.kilos_netos) AS kg_total
    FROM movimientos m
    JOIN dim_empresas e ON m.empresa_id = e.id_empresa
    GROUP BY e.id_empresa, e.nombre_unif
    HAVING ultima_fecha < date('now', ?)
    ORDER BY kg_total DESC;
"""

QUERY_TODOS_LOS_MERCADOS = """
    SELECT DISTINCT
        COALESCE(NULLIF(TRIM(destino), ''), 'URUGUAY (Mercado Interno)') AS mercado,
        SUM(kilos_netos) AS kg_total
    FROM movimientos
    GROUP BY mercado
    ORDER BY kg_total DESC;
"""


# ─────────────────────────────────────────────────────────────────────────────
# REPOSITORIO CIE — Capa de datos
# ─────────────────────────────────────────────────────────────────────────────

class RepositorioCIE:
    """
    Capa de acceso a datos para Competitive Intelligence.
    Reutiliza conexiones y patrones de empresa360/repositorio.py.
    """

    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)

    @contextmanager
    def connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON;")
        try:
            yield conn
        finally:
            conn.close()

    # ── Helpers genéricos ─────────────────────────────────────────────────

    def _fetchall(
        self, sql: str, params: tuple = ()
    ) -> list[dict[str, Any]]:
        with self.connect() as conn:
            cur = conn.execute(sql, params)
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]

    def _fetchone(
        self, sql: str, params: tuple = ()
    ) -> Optional[dict[str, Any]]:
        with self.connect() as conn:
            cur = conn.execute(sql, params)
            row = cur.fetchone()
            if not row:
                return None
            cols = [d[0] for d in cur.description]
            return dict(zip(cols, row))

    # ── Productores ───────────────────────────────────────────────────────

    def productores_empresa(self, id_empresa: int) -> list[dict[str, Any]]:
        return self._fetchall(QUERY_PRODUCTORES_EMPRESA, (id_empresa,))

    def productores_compartidos(
        self, id_a: int, id_b: int
    ) -> list[dict[str, Any]]:
        return self._fetchall(
            QUERY_PRODUCTORES_COMPARTIDOS, (id_b, id_a)
        )

    def productores_exclusivos_a(
        self, id_a: int, id_b: int
    ) -> list[dict[str, Any]]:
        return self._fetchall(
            QUERY_PRODUCTORES_EXCLUSIVOS_A, (id_a, id_b)
        )

    def productores_no_usan(
        self, id_empresa: int, id_excluir: int
    ) -> list[dict[str, Any]]:
        return self._fetchall(
            QUERY_PRODUCTORES_NO_USAN_EMPRESA, (id_excluir, id_empresa)
        )

    def productores_nuevos(
        self, id_empresa: int, dias: int = 90
    ) -> list[dict[str, Any]]:
        return self._fetchall(
            QUERY_PRODUCTORES_NUEVOS, (id_empresa, f"-{dias} days")
        )

    def productores_que_abandonaron(
        self, id_empresa: int, dias: int = 90
    ) -> list[dict[str, Any]]:
        return self._fetchall(
            QUERY_PRODUCTORES_QUE_ABANDONARON, (id_empresa, f"-{dias} days")
        )

    def productores_multi_deposito(self) -> list[dict[str, Any]]:
        return self._fetchall(QUERY_PRODUCTORES_MULTI_DEPOSITO)

    def top_productores_empresa(
        self, id_empresa: int, limite: int = 20
    ) -> list[dict[str, Any]]:
        return self._fetchall(
            QUERY_TOP_PRODUCTORES_EMPRESA, (id_empresa, limite)
        )

    def ranking_global_productores(
        self, limite: int = 50
    ) -> list[dict[str, Any]]:
        return self._fetchall(QUERY_RANKING_PRODUCTORES_GLOBAL, (limite,))

    def productores_exportan_mercado_no_a(
        self, id_empresa: int, id_excluir: int
    ) -> list[dict[str, Any]]:
        return self._fetchall(
            QUERY_PRODUCTORES_EXPORTAN_MERCADO_NO_A, (id_empresa, id_excluir)
        )

    def crecimiento_productores(
        self, id_empresa: int
    ) -> list[dict[str, Any]]:
        return self._fetchall(QUERY_CRECIMIENTO_PRODUCTORES, (id_empresa,))

    # ── Mercados ─────────────────────────────────────────────────────────

    def mercados_empresa(self, id_empresa: int) -> list[dict[str, Any]]:
        return self._fetchall(QUERY_MERCADOS_EMPRESA, (id_empresa,))

    def mercados_compartidos(
        self, id_a: int, id_b: int
    ) -> list[dict[str, Any]]:
        return self._fetchall(
            QUERY_MERCADOS_COMPARTIDOS, (id_b, id_a)
        )

    def mercados_exclusivos_a(
        self, id_a: int, id_b: int
    ) -> list[dict[str, Any]]:
        return self._fetchall(
            QUERY_MERCADOS_EXCLUSIVOS_A, (id_a, id_b)
        )

    def mercados_no_participa(
        self, id_empresa: int
    ) -> list[dict[str, Any]]:
        return self._fetchall(
            QUERY_MERCADOS_NO_PARTICIPA, (id_empresa, id_empresa)
        )

    def mercados_nuevos(
        self, id_empresa: int, dias: int = 90
    ) -> list[dict[str, Any]]:
        return self._fetchall(
            QUERY_MERCADOS_NUEVOS, (id_empresa, f"-{dias} days")
        )

    def mercados_perdidos(
        self, id_empresa: int, dias: int = 90
    ) -> list[dict[str, Any]]:
        return self._fetchall(
            QUERY_MERCADOS_PERDIDOS, (id_empresa, f"-{dias} days")
        )

    def todos_los_mercados(self) -> list[dict[str, Any]]:
        return self._fetchall(QUERY_TODOS_LOS_MERCADOS)

    # ── Clientes ───────────────────────────────────────────────────────────

    def clientes_empresa(self, id_empresa: int) -> list[dict[str, Any]]:
        return self._fetchall(QUERY_CLIENTES_EMPRESA, (id_empresa,))

    def clientes_compartidos(
        self, id_a: int, id_b: int
    ) -> list[dict[str, Any]]:
        return self._fetchall(
            QUERY_CLIENTES_COMPARTIDOS, (id_b, id_a)
        )

    def clientes_exclusivos_a(
        self, id_a: int, id_b: int
    ) -> list[dict[str, Any]]:
        return self._fetchall(
            QUERY_CLIENTES_EXCLUSIVOS_A, (id_a, id_b)
        )

    def clientes_nuevos(
        self, id_empresa: int, dias: int = 90
    ) -> list[dict[str, Any]]:
        return self._fetchall(
            QUERY_CLIENTES_NUEVOS, (id_empresa, f"-{dias} days")
        )

    def clientes_perdidos(
        self, id_empresa: int, dias: int = 90
    ) -> list[dict[str, Any]]:
        return self._fetchall(
            QUERY_CLIENTES_PERDIDOS, (id_empresa, f"-{dias} days")
        )

    def clientes_decreciendo(
        self, id_empresa: int
    ) -> list[dict[str, Any]]:
        return self._fetchall(QUERY_CLIENTES_DECRECIENDO, (id_empresa,))

    # ── Productos ────────────────────────────────────────────────────────

    def productos_empresa(self, id_empresa: int) -> list[dict[str, Any]]:
        return self._fetchall(QUERY_PRODUCTOS_EMPRESA, (id_empresa,))

    def productos_compartidos(
        self, id_a: int, id_b: int
    ) -> list[dict[str, Any]]:
        return self._fetchall(
            QUERY_PRODUCTOS_COMPARTIDOS, (id_b, id_a)
        )

    # ── Volúmenes ────────────────────────────────────────────────────────

    def kg_empresa_por_mes(
        self, id_empresa: int
    ) -> list[dict[str, Any]]:
        return self._fetchall(QUERY_KG_EMPRESA_POR_MES, (id_empresa,))

    def kg_total_empresa(self, id_empresa: int) -> float:
        row = self._fetchone(QUERY_KG_TOTAL_EMPRESA, (id_empresa,))
        return row["kg_total"] if row else 0.0

    def porcentaje_paso_por(
        self, id_a: int, id_b: int
    ) -> float:
        row = self._fetchone(
            QUERY_PORCENTAJE_PASO_POR_EMPRESA, (id_b, id_a, id_b)
        )
        return row["porcentaje"] if row and row.get("porcentaje") is not None else 0.0

    def exportacion_sin_pasar(
        self, id_a: int, id_b: int
    ) -> float:
        row = self._fetchone(
            QUERY_EXPORTACION_SIN_PASAR, (id_b, id_a)
        )
        return row["kg_exportacion_sin_a"] if row else 0.0

    # ── Generales ────────────────────────────────────────────────────────

    def empresas_sin_actividad_reciente(
        self, dias: int = 60
    ) -> list[dict[str, Any]]:
        return self._fetchall(
            QUERY_EMPRESAS_SIN_DATOS, (f"-{dias} days",)
        )
