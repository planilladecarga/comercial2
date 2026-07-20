"""
=================================================================================
repositorio.py — Capa de datos centralizada para Empresa360
=================================================================================

Define TODAS las consultas SQL en un solo lugar, organizadas por dominio.
Ningún servicio debe escribir SQL directamente — todo pasa por aquí.

Esto garantiza:
    • DRY: cada consulta existe una sola vez
    • Mantenibilidad: un cambio de schema se refleja en un solo lugar
    • Testabilidad: se pueden mockear las consultas fácilmente
    • Rendimiento: queries optimizadas con índices cubiertos

Uso:
    repo = Repositorio(db_path)
    empresas = repo.listar_empresas()
    movimientos = repo.movimientos_por_empresa(empresa_id)
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Optional, Any
from dataclasses import dataclass, field
from contextlib import contextmanager

# ─────────────────────────────────────────────────────────────────────────────
# QUERIES — SQL strings centralizados
# ─────────────────────────────────────────────────────────────────────────────

QUERY_EMPRESA_POR_NOMBRE = """
    SELECT id_empresa, nombre_original, nombre_norm, nombre_unif,
           ruc, tipo_principal, activo,
           fecha_primera, fecha_ultima, cant_movimientos,
           es_productor, es_certificador, es_deposito, es_puerto,
           es_competidor
    FROM dim_empresas
    WHERE nombre_unif = ?
       OR nombre_norm LIKE ?
       OR nombre_original LIKE ?
    LIMIT 1;
"""

QUERY_LISTAR_EMPRESAS = """
    SELECT id_empresa, nombre_original, nombre_unif,
           tipo_principal, activo,
           fecha_primera, fecha_ultima, cant_movimientos
    FROM dim_empresas
    WHERE activo = 1
    ORDER BY nombre_unif ASC;
"""

QUERY_BUSCAR_EMPRESA_ID = """
    SELECT id_empresa FROM dim_empresas WHERE id_empresa = ? LIMIT 1;
"""

QUERY_MOVIMIENTOS_POR_EMPRESA = """
    SELECT
        m.id_movimiento,
        m.fecha_movimiento,
        m.tipo_movimiento,
        m.categoria_movimiento,
        m.kilos_netos,
        m.nro_gre,
        m.nro_certificado,
        m.nombre_productor,
        m.departamento,
        e.nombre_unif          AS empresa,
        p.nombre_producto      AS producto,
        m.destino               AS mercado
    FROM movimientos m
    LEFT JOIN dim_empresas   e ON m.empresa_id   = e.id_empresa
    LEFT JOIN dim_productos  p ON m.producto_id  = p.id_producto
    WHERE m.empresa_id = ?
    ORDER BY m.fecha_movimiento DESC;
"""

QUERY_MOVIMIENTOS_POR_PRODUCTOR = """
    SELECT
        m.id_movimiento,
        m.fecha_movimiento,
        m.tipo_movimiento,
        m.kilos_netos,
        m.empresa_id,
        e.nombre_unif  AS empresa,
        p.nombre_producto AS producto
    FROM movimientos m
    LEFT JOIN dim_empresas  e ON m.empresa_id = e.id_empresa
    LEFT JOIN dim_productos p ON m.producto_id = p.id_producto
    WHERE m.nro_productor = ?
    ORDER BY m.fecha_movimiento DESC;
"""

QUERY_KG_TOTALES_EMPRESA = """
    SELECT COALESCE(SUM(m.kilos_netos), 0) AS kg_totales
    FROM movimientos m
    WHERE m.empresa_id = ?;
"""

QUERY_CANTIDAD_MOVIMIENTOS_EMPRESA = """
    SELECT COUNT(*) AS cant_movimientos
    FROM movimientos
    WHERE empresa_id = ?;
"""

QUERY_PRODUCTORES_RELACIONADOS = """
    SELECT
        m.nro_productor,
        m.nombre_productor,
        COUNT(*)            AS cantidad_movimientos,
        SUM(m.kilos_netos) AS kg_total,
        MIN(m.fecha_movimiento) AS primera_fecha,
        MAX(m.fecha_movimiento) AS ultima_fecha
    FROM movimientos m
    WHERE m.empresa_id = ?
    GROUP BY m.nro_productor, m.nombre_productor
    ORDER BY kg_total DESC;
"""

QUERY_CERTIFICADORES_RELACIONADOS = """
    SELECT
        m.nro_certificado,
        m.nombre_establecimiento  AS certificador,
        COUNT(*)            AS cantidad_movimientos,
        SUM(m.kilos_netos) AS kg_total,
        MIN(m.fecha_movimiento) AS primera_fecha,
        MAX(m.fecha_movimiento) AS ultima_fecha
    FROM movimientos m
    WHERE m.empresa_id = ?
      AND m.nro_certificado IS NOT NULL
      AND m.nro_certificado != ''
    GROUP BY m.nro_certificado, m.nombre_establecimiento
    ORDER BY kg_total DESC;
"""

QUERY_DEPOSITOS_UTILIZADOS = """
    SELECT
        m.nombre_establecimiento AS deposito,
        m.departamento,
        COUNT(*)            AS cantidad_movimientos,
        SUM(m.kilos_netos)  AS kg_total,
        ROUND(SUM(m.kilos_netos) * 100.0 /
              (SELECT SUM(mm.kilos_netos) FROM movimientos mm WHERE mm.empresa_id = ?), 2
        ) AS porcentaje
    FROM movimientos m
    WHERE m.empresa_id = ?
      AND m.solo_deposito = 1
    GROUP BY m.nombre_establecimiento, m.departamento
    ORDER BY kg_total DESC;
"""

QUERY_DEPOSITOS_POR_EMPRESA = """
    SELECT
        m.nombre_establecimiento AS deposito,
        m.departamento,
        COUNT(*)            AS cantidad_movimientos,
        SUM(m.kilos_netos)  AS kg_total,
        ROUND(SUM(m.kilos_netos) * 100.0 /
              NULLIF(
                  (SELECT SUM(mm.kilos_netos) FROM movimientos mm
                   WHERE mm.empresa_id = ? AND mm.nombre_establecimiento = m.nombre_establecimiento), 0
              ), 2) AS porcentaje
    FROM movimientos m
    WHERE m.empresa_id = ?
    GROUP BY m.nombre_establecimiento, m.departamento
    ORDER BY kg_total DESC;
"""

QUERY_MERCADOS_EMPRESA = """
    SELECT
        COALESCE(NULLIF(TRIM(m.destino), ''), 'URUGUAY (Mercado Interno)') AS mercado,
        COUNT(*)            AS cantidad_movimientos,
        SUM(m.kilos_netos)  AS kg_total
    FROM movimientos m
    WHERE m.empresa_id = ?
    GROUP BY mercado
    ORDER BY kg_total DESC;
"""

QUERY_PRODUCTOS_EMPRESA = """
    SELECT
        p.nombre_producto    AS producto,
        p.categoria,
        COUNT(*)             AS cantidad_movimientos,
        SUM(m.kilos_netos)   AS kg_total
    FROM movimientos m
    JOIN dim_productos p ON m.producto_id = p.id_producto
    WHERE m.empresa_id = ?
    GROUP BY p.nombre_producto, p.categoria
    ORDER BY kg_total DESC;
"""

QUERY_CORTES_EMPRESA = """
    SELECT
        c.nombre_corte,
        c.codigo_corte,
        c.categoria_corte,
        COUNT(*)            AS cantidad_movimientos,
        SUM(m.kilos_netos)  AS kg_total
    FROM movimientos m
    JOIN dim_productos p ON m.producto_id = p.id_producto
    LEFT JOIN dim_cortes c ON c.producto_id = p.id_producto
    WHERE m.empresa_id = ?
    GROUP BY c.nombre_corte, c.codigo_corte, c.categoria_corte
    ORDER BY kg_total DESC;
"""

QUERY_EVOLUCION_MENSUAL = """
    SELECT
        cal.anio,
        cal.mes,
        cal.nombre_mes,
        cal.trimestre,
        COUNT(*)            AS cantidad_movimientos,
        SUM(m.kilos_netos)  AS kg_total
    FROM movimientos m
    JOIN dim_calendario cal ON m.fecha_id = cal.id_fecha
    WHERE m.empresa_id = ?
    GROUP BY cal.anio, cal.mes
    ORDER BY cal.anio ASC, cal.mes ASC;
"""

QUERY_RANKING_EMPRESAS_KG = """
    SELECT
        e.id_empresa,
        e.nombre_unif,
        COUNT(*)            AS cantidad_movimientos,
        SUM(m.kilos_netos)  AS kg_total
    FROM movimientos m
    JOIN dim_empresas e ON m.empresa_id = e.id_empresa
    WHERE e.activo = 1
    GROUP BY e.id_empresa, e.nombre_unif
    ORDER BY kg_total DESC
    LIMIT ?;
"""

QUERY_COMPETIDORES_COMUN_PRODUCTORES = """
    SELECT DISTINCT
        e.id_empresa,
        e.nombre_unif,
        COUNT(DISTINCT m.nro_productor) AS productores_compartidos
    FROM movimientos m
    JOIN dim_empresas e ON m.empresa_id = e.id_empresa
    WHERE m.nro_productor IN (
        SELECT DISTINCT nro_productor
        FROM movimientos mm
        WHERE mm.empresa_id = ?
    )
      AND m.empresa_id != ?
      AND e.activo = 1
    GROUP BY e.id_empresa, e.nombre_unif
    ORDER BY productores_compartidos DESC;
"""

QUERY_COMPETIDORES_COMUN_MERCADOS = """
    SELECT DISTINCT
        e.id_empresa,
        e.nombre_unif,
        COUNT(DISTINCT COALESCE(NULLIF(TRIM(m.destino), ''), 'URUGUAY (Mercado Interno)'))
            AS mercados_compartidos
    FROM movimientos m
    JOIN dim_empresas e ON m.empresa_id = e.id_empresa
    WHERE COALESCE(NULLIF(TRIM(m.destino), ''), 'URUGUAY (Mercado Interno)')
          IN (
              SELECT DISTINCT COALESCE(NULLIF(TRIM(mm.destino), ''), 'URUGUAY (Mercado Interno)')
              FROM movimientos mm
              WHERE mm.empresa_id = ?
          )
      AND m.empresa_id != ?
      AND e.activo = 1
    GROUP BY e.id_empresa, e.nombre_unif
    ORDER BY mercados_compartidos DESC;
"""

QUERY_COMPETIDORES_COMUN_PRODUCTOS = """
    SELECT DISTINCT
        e.id_empresa,
        e.nombre_unif,
        COUNT(DISTINCT p.id_producto) AS productos_compartidos
    FROM movimientos m
    JOIN dim_empresas  e ON m.empresa_id  = e.id_empresa
    JOIN dim_productos  p ON m.producto_id = p.id_producto
    WHERE p.id_producto IN (
        SELECT DISTINCT pp.id_producto
        FROM movimientos mm
        JOIN dim_productos pp ON mm.producto_id = pp.id_producto
        WHERE mm.empresa_id = ?
    )
      AND m.empresa_id != ?
      AND e.activo = 1
    GROUP BY e.id_empresa, e.nombre_unif
    ORDER BY productos_compartidos DESC;
"""

QUERY_CLIENTES_EMPRESA = """
    SELECT
        m.destino  AS cliente,
        COUNT(*)            AS cantidad_movimientos,
        SUM(m.kilos_netos)  AS kg_total
    FROM movimientos m
    WHERE m.empresa_id = ?
      AND m.destino IS NOT NULL
      AND TRIM(m.destino) != ''
    GROUP BY m.destino
    ORDER BY kg_total DESC;
"""

QUERY_NUEVOS_PRODUCTORES = """
    SELECT DISTINCT
        m.nro_productor,
        m.nombre_productor,
        MIN(m.fecha_movimiento) AS primera_fecha
    FROM movimientos m
    WHERE m.empresa_id = ?
    GROUP BY m.nro_productor, m.nombre_productor
    HAVING primera_fecha >= date('now', '-90 days')
    ORDER BY primera_fecha DESC;
"""

QUERY_TODAS_EMPRESAS_ID = """
    SELECT id_empresa, nombre_unif FROM dim_empresas WHERE activo = 1;
"""

QUERY_ULTIMO_MES_DISPONIBLE = """
    SELECT cal.anio, cal.mes
    FROM movimientos m
    JOIN dim_calendario cal ON m.fecha_id = cal.id_fecha
    GROUP BY cal.anio, cal.mes
    ORDER BY cal.anio DESC, cal.mes DESC
    LIMIT 1;
"""

QUERY_PORCENTAJE_VOLUMEN_MENSUAL = """
    WITH empresa_mes AS (
        SELECT SUM(m.kilos_netos) AS kg
        FROM movimientos m
        WHERE m.empresa_id = ?
          AND cal.anio  = ?
          AND cal.mes   = ?
    ),
    total_mes AS (
        SELECT SUM(m.kilos_netos) AS kg
        FROM movimientos m
        JOIN dim_calendario cal ON m.fecha_id = cal.id_fecha
        WHERE cal.anio = ? AND cal.mes = ?
    )
    SELECT
        ROUND(
            (SELECT kg FROM empresa_mes) * 100.0 /
            NULLIF((SELECT kg FROM total_mes), 0)
        , 2) AS participacion_pct;
"""


# ─────────────────────────────────────────────────────────────────────────────
# DATACLASSES DE RESULTADO
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class EmpresaBasica:
    """Información básica de una empresa."""
    id_empresa: int
    nombre_original: str
    nombre_unif: str
    ruc: Optional[str]
    tipo_principal: Optional[str]
    activo: int
    fecha_primera: Optional[str]
    fecha_ultima: Optional[str]
    cant_movimientos: int
    es_productor: int
    es_certificador: int
    es_deposito: int
    es_puerto: int
    es_competidor: int


@dataclass
class MovimientoResumen:
    """Resumen de un movimiento."""
    id_movimiento: int
    fecha_movimiento: str
    tipo_movimiento: str
    categoria_movimiento: Optional[str]
    kilos_netos: float
    nro_gre: Optional[str]
    nro_certificado: Optional[str]
    nombre_productor: Optional[str]
    departamento: Optional[str]
    empresa: Optional[str]
    producto: Optional[str]
    mercado: Optional[str]


# ─────────────────────────────────────────────────────────────────────────────
# REPOSITORIO
# ─────────────────────────────────────────────────────────────────────────────

class Repositorio:
    """
    Capa de acceso a datos para Empresa360.

    Uso:
        repo = Repositorio("data/frimaral_bi.db")
        movs = repo.movimientos_por_empresa(5)
        prod = repo.productores_relacionados(5)
    """

    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)

    # ─── Connection ─────────────────────────────────────────────────────────

    @contextmanager
    def connect(self):
        """Gestor de contexto para la conexión."""
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON;")
        try:
            yield conn
        finally:
            conn.close()

    # ─── Empresa ─────────────────────────────────────────────────────────────

    def empresa_por_nombre(self, nombre: str) -> Optional[dict[str, Any]]:
        """Busca una empresa por nombre (búsqueda flexible)."""
        like = f"%{nombre}%"
        with self.connect() as conn:
            cur = conn.execute(
                QUERY_EMPRESA_POR_NOMBRE, (nombre.upper(), like, like)
            )
            row = cur.fetchone()
            if not row:
                return None
            cols = [d[0] for d in cur.description]
            return dict(zip(cols, row))

    def empresa_por_id(self, id_empresa: int) -> Optional[dict[str, Any]]:
        """Busca empresa por ID."""
        with self.connect() as conn:
            cur = conn.execute(
                "SELECT * FROM dim_empresas WHERE id_empresa = ? LIMIT 1;",
                (id_empresa,)
            )
            row = cur.fetchone()
            if not row:
                return None
            cols = [d[0] for d in cur.description]
            return dict(zip(cols, row))

    def listar_empresas(self) -> list[dict[str, Any]]:
        """Lista todas las empresas activas."""
        with self.connect() as conn:
            cur = conn.execute(QUERY_LISTAR_EMPRESAS)
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]

    def todas_empresas_id(self) -> list[tuple[int, str]]:
        """Retorna lista de (id, nombre_unif) de todas las empresas."""
        with self.connect() as conn:
            cur = conn.execute(QUERY_TODAS_EMPRESAS_ID)
            return [(row[0], row[1]) for row in cur.fetchall()]

    # ─── Movimientos ────────────────────────────────────────────────────────

    def movimientos_por_empresa(
        self, id_empresa: int, limite: int = 1000
    ) -> list[dict[str, Any]]:
        """Movimientos de una empresa."""
        sql = QUERY_MOVIMIENTOS_POR_EMPRESA + f" LIMIT {limite};"
        with self.connect() as conn:
            cur = conn.execute(sql, (id_empresa,))
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]

    def movimientos_por_productor(
        self, nro_productor: str, limite: int = 500
    ) -> list[dict[str, Any]]:
        """Todos los movimientos de un productor."""
        sql = QUERY_MOVIMIENTOS_POR_PRODUCTOR + f" LIMIT {limite};"
        with self.connect() as conn:
            cur = conn.execute(sql, (nro_productor,))
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]

    # ─── Totales / KPIs ─────────────────────────────────────────────────────

    def kg_totales(self, id_empresa: int) -> float:
        with self.connect() as conn:
            cur = conn.execute(QUERY_KG_TOTALES_EMPRESA, (id_empresa,))
            return cur.fetchone()[0] or 0.0

    def cantidad_movimientos(self, id_empresa: int) -> int:
        with self.connect() as conn:
            cur = conn.execute(QUERY_CANTIDAD_MOVIMIENTOS_EMPRESA, (id_empresa,))
            return cur.fetchone()[0] or 0

    def ranking_empresas(self, limite: int = 20) -> list[dict[str, Any]]:
        """Ranking de empresas por kg totales."""
        with self.connect() as conn:
            cur = conn.execute(QUERY_RANKING_EMPRESAS_KG, (limite,))
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]

    def ultimo_mes_disponible(self) -> tuple[int, int] | None:
        """Retorna (anio, mes) del último mes con datos."""
        with self.connect() as conn:
            cur = conn.execute(QUERY_ULTIMO_MES_DISPONIBLE)
            row = cur.fetchone()
            return (row[0], row[1]) if row else None

    # ─── Relaciones ──────────────────────────────────────────────────────────

    def productores_relacionados(
        self, id_empresa: int
    ) -> list[dict[str, Any]]:
        """Productores relacionados con una empresa."""
        with self.connect() as conn:
            cur = conn.execute(QUERY_PRODUCTORES_RELACIONADOS, (id_empresa,))
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]

    def certificadores_relacionados(
        self, id_empresa: int
    ) -> list[dict[str, Any]]:
        """Certificadores únicos utilizados por una empresa."""
        with self.connect() as conn:
            cur = conn.execute(QUERY_CERTIFICADORES_RELACIONADOS, (id_empresa,))
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]

    def depositos_utilizados(
        self, id_empresa: int
    ) -> list[dict[str, Any]]:
        """Depósitos utilizados por una empresa (solo_deposito=1)."""
        with self.connect() as conn:
            cur = conn.execute(QUERY_DEPOSITOS_UTILIZADOS, (id_empresa, id_empresa))
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]

    def depositos_por_empresa(
        self, id_empresa: int
    ) -> list[dict[str, Any]]:
        """Todos los establecimientos usados por una empresa como operador."""
        with self.connect() as conn:
            cur = conn.execute(QUERY_DEPOSITOS_POR_EMPRESA, (id_empresa, id_empresa))
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]

    def mercados_empresa(self, id_empresa: int) -> list[dict[str, Any]]:
        """Mercados (destinos) de una empresa."""
        with self.connect() as conn:
            cur = conn.execute(QUERY_MERCADOS_EMPRESA, (id_empresa,))
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]

    def productos_empresa(self, id_empresa: int) -> list[dict[str, Any]]:
        """Productos de una empresa."""
        with self.connect() as conn:
            cur = conn.execute(QUERY_PRODUCTOS_EMPRESA, (id_empresa,))
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]

    def cortes_empresa(self, id_empresa: int) -> list[dict[str, Any]]:
        """Cortes procesados por una empresa."""
        with self.connect() as conn:
            cur = conn.execute(QUERY_CORTES_EMPRESA, (id_empresa,))
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]

    def evolucion_mensual(
        self, id_empresa: int
    ) -> list[dict[str, Any]]:
        """Evolución mensual de kg y movimientos."""
        with self.connect() as conn:
            cur = conn.execute(QUERY_EVOLUCION_MENSUAL, (id_empresa,))
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]

    def clientes_empresa(self, id_empresa: int) -> list[dict[str, Any]]:
        """Clientes (destinos) de una empresa."""
        with self.connect() as conn:
            cur = conn.execute(QUERY_CLIENTES_EMPRESA, (id_empresa,))
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]

    # ─── Competidores ───────────────────────────────────────────────────────

    def competidores_por_productores(
        self, id_empresa: int
    ) -> list[dict[str, Any]]:
        """Empresas que comparten productores."""
        with self.connect() as conn:
            cur = conn.execute(
                QUERY_COMPETIDORES_COMUN_PRODUCTORES, (id_empresa, id_empresa)
            )
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]

    def competidores_por_mercados(
        self, id_empresa: int
    ) -> list[dict[str, Any]]:
        """Empresas que comparten mercados."""
        with self.connect() as conn:
            cur = conn.execute(
                QUERY_COMPETIDORES_COMUN_MERCADOS, (id_empresa, id_empresa)
            )
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]

    def competidores_por_productos(
        self, id_empresa: int
    ) -> list[dict[str, Any]]:
        """Empresas que comparten productos."""
        with self.connect() as conn:
            cur = conn.execute(
                QUERY_COMPETIDORES_COMUN_PRODUCTOS, (id_empresa, id_empresa)
            )
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]

    # ─── Alertas ────────────────────────────────────────────────────────────

    def nuevos_productores(self, id_empresa: int) -> list[dict[str, Any]]:
        """Productores que trabajan con esta empresa por primera vez (últimos 90 días)."""
        with self.connect() as conn:
            cur = conn.execute(QUERY_NUEVOS_PRODUCTORES, (id_empresa,))
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]

    # ─── Participación ──────────────────────────────────────────────────────

    def participacion_mensual(
        self, id_empresa: int, anio: int, mes: int
    ) -> float | None:
        """Porcentaje de participación de una empresa en un mes dado."""
        with self.connect() as conn:
            cur = conn.execute(
                QUERY_PORCENTAJE_VOLUMEN_MENSUAL,
                (id_empresa, anio, mes, anio, mes)
            )
            row = cur.fetchone()
            return row[0] if row and row[0] is not None else None
