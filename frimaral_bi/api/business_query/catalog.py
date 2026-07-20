"""
BusinessQueryCatalog - Catálogo de consultas predefinidas
Sprint 7 - FRIMARAL BI
"""
from .dto import QueryDefinicion, QueryParametro


def _empresa_param(label="Empresa", required=True):
    return QueryParametro(
        nombre="empresa", tipo="select", label=label,
        requerido=required, opciones=[],  # Se llena dinámicamente
        descripcion="Empresa sobre la que se ejecuta la consulta"
    )


def _periodo_params():
    return [
        QueryParametro(
            nombre="fecha_desde", tipo="date", label="Desde",
            requerido=False, default="",
            descripcion="Fecha inicial del período"
        ),
        QueryParametro(
            nombre="fecha_hasta", tipo="date", label="Hasta",
            requerido=False, default="",
            descripcion="Fecha final del período"
        ),
    ]


def _mercado_param():
    return QueryParametro(
        nombre="mercado", tipo="select", label="Mercado",
        requerido=False, opciones=[],
        descripcion="Filtrar por mercado/destino"
    )


def _producto_param():
    return QueryParametro(
        nombre="producto", tipo="select", label="Producto",
        requerido=False, opciones=[],
        descripcion="Filtrar por producto"
    )


def _temperatura_param():
    return QueryParametro(
        nombre="temperatura", tipo="select", label="Temperatura",
        requerido=False, opciones=[
            {"value": "", "label": "Todos"},
            {"value": "REFRIGERADO", "label": "Refrigerado"},
            {"value": "CONGELADO", "label": "Congelado"},
        ],
        descripcion="Filtrar por temperatura"
    )


def _certificador_param():
    return QueryParametro(
        nombre="certificador", tipo="select", label="Certificador",
        requerido=False, opciones=[],
        descripcion="Filtrar por certificador"
    )


def _deposito_param():
    return QueryParametro(
        nombre="deposito", tipo="select", label="Depósito",
        requerido=False, opciones=[],
        descripcion="Filtrar por depósito"
    )


def _tipo_movimiento_param():
    return QueryParametro(
        nombre="tipo_movimiento", tipo="select", label="Tipo Movimiento",
        requerido=False, opciones=[
            {"value": "", "label": "Todos"},
            {"value": "EXPORTACION", "label": "Exportación"},
            {"value": "DEPOSITO", "label": "Depósito"},
            {"value": "INTERNO", "label": "Interno"},
        ],
        descripcion="Filtrar por tipo de movimiento"
    )


def _limit_param(default=100):
    return QueryParametro(
        nombre="limite", tipo="int", label="Límite",
        requerido=False, default=default,
        descripcion="Cantidad máxima de resultados"
    )


CONSULTAS_CATALOGO: list[QueryDefinicion] = [

    # ── CONS-001 ──────────────────────────────────────────
    QueryDefinicion(
        id="CONS-001",
        nombre="Exportaciones sin pasar por empresa",
        descripcion="Kg exportados por una empresa que NO pasaron por CALIRAL (u otra empresa de referencia). Útil para detectar fuga de volumen.",
        categoria="exportacion",
        parametros=[
            QueryParametro(
                nombre="empresa_origen", tipo="select", label="Empresa Origen",
                requerido=True, opciones=[],
                descripcion="Empresa que exporta"
            ),
            QueryParametro(
                nombre="empresa_referencia", tipo="select", label="Empresa Referencia",
                requerido=True, opciones=[],
                descripcion="Empresa de referencia (ej: CALIRAL)"
            ),
        ] + _periodo_params() + [_limit_param(50)],
        sql="""
            SELECT
                m.nro_gre AS "N° GRE",
                m.fecha_movimiento AS "Fecha",
                m.nombre_productor AS "Productor",
                m.nro_productor AS "RUC Productor",
                e_origen.nombre_unif AS "Empresa Origen",
                COALESCE(NULLIF(TRIM(m.destino), ''), 'URUGUAY (Mercado Interno)') AS "Mercado",
                m.tipo_movimiento AS "Tipo",
                p.nombre_producto AS "Producto",
                ROUND(m.kilos_netos, 2) AS "Kg",
                m.temperatura AS "Temperatura"
            FROM movimientos m
            JOIN dim_empresas e_origen ON m.empresa_id = e_origen.id_empresa
            LEFT JOIN dim_productos p ON m.producto_id = p.id_producto
            WHERE m.empresa_id = :empresa_origen
              AND m.tipo_movimiento LIKE '%EXPORT%'
              AND m.nro_productor NOT IN (
                  SELECT DISTINCT nro_productor
                  FROM movimientos
                  WHERE empresa_id = :empresa_referencia
                    AND nro_productor IS NOT NULL
                    AND nro_productor != ''
              )
              AND (:fecha_desde = '' OR m.fecha_movimiento >= :fecha_desde)
              AND (:fecha_hasta = '' OR m.fecha_movimiento <= :fecha_hasta)
            ORDER BY m.fecha_movimiento DESC
            LIMIT :limite;
        """,
        reglas_negocio=[
            "RN-001: Se consideran exportaciones los movimientos con tipo_movimiento LIKE '%EXPORT%'",
            "RN-002: Productor excluido si aparece al menos una vez con la empresa referencia",
            "RN-003: Solo se muestran productores que exportaron directamente desde la empresa origen",
        ],
    ),

    # ── CONS-002 ──────────────────────────────────────────
    QueryDefinicion(
        id="CONS-002",
        nombre="Depósitos utilizados por empresa",
        descripcion="Qué depósitos utiliza una empresa y cuántos kg pasaron por cada uno.",
        categoria="deposito",
        parametros=[
            _empresa_param(),
        ] + _periodo_params() + [_limit_param(50)],
        sql="""
            SELECT
                m.nombre_establecimiento AS "Depósito",
                m.departamento AS "Departamento",
                COUNT(*) AS "Movimientos",
                ROUND(SUM(m.kilos_netos), 2) AS "Kg Totales",
                ROUND(AVG(m.kilos_netos), 2) AS "Kg Promedio",
                MIN(m.fecha_movimiento) AS "Primera Fecha",
                MAX(m.fecha_movimiento) AS "Última Fecha"
            FROM movimientos m
            WHERE m.empresa_id = :empresa
              AND m.solo_deposito = 1
              AND (:fecha_desde = '' OR m.fecha_movimiento >= :fecha_desde)
              AND (:fecha_hasta = '' OR m.fecha_movimiento <= :fecha_hasta)
            GROUP BY m.nombre_establecimiento, m.departamento
            ORDER BY SUM(m.kilos_netos) DESC
            LIMIT :limite;
        """,
        reglas_negocio=[
            "RN-001: solo_deposito = 1 indica movimiento de depósito",
            "RN-002: Se agrupa por nombre de establecimiento y departamento",
        ],
    ),

    # ── CONS-003 ──────────────────────────────────────────
    QueryDefinicion(
        id="CONS-003",
        nombre="Productores que utilizan una empresa",
        descripcion="Lista de productores que trabajan con una empresa específica, con volumen y frecuencia.",
        categoria="productor",
        parametros=[
            _empresa_param("Empresa"),
        ] + _periodo_params() + [_limit_param(50)],
        sql="""
            SELECT
                m.nro_productor AS "N° Productor",
                m.nombre_productor AS "Nombre Productor",
                COUNT(*) AS "Movimientos",
                ROUND(SUM(m.kilos_netos), 2) AS "Kg Totales",
                ROUND(AVG(m.kilos_netos), 2) AS "Kg Promedio",
                MIN(m.fecha_movimiento) AS "Primera Fecha",
                MAX(m.fecha_movimiento) AS "Última Fecha",
                COUNT(DISTINCT m.empresa_id) AS "Empresas Concurrentes"
            FROM movimientos m
            WHERE m.empresa_id = :empresa
              AND m.nro_productor IS NOT NULL AND m.nro_productor != ''
              AND (:fecha_desde = '' OR m.fecha_movimiento >= :fecha_desde)
              AND (:fecha_hasta = '' OR m.fecha_movimiento <= :fecha_hasta)
            GROUP BY m.nro_productor, m.nombre_productor
            ORDER BY SUM(m.kilos_netos) DESC
            LIMIT :limite;
        """,
        reglas_negocio=[
            "RN-001: Se considera productor activo si tiene al menos un movimiento",
            "RN-002: Empresas Concurrentes = cantidad de empresas distintas con las que trabaja",
        ],
    ),

    # ── CONS-004 ──────────────────────────────────────────
    QueryDefinicion(
        id="CONS-004",
        nombre="Productores que utilizan CALIRAL",
        descripcion="Igual que CONS-003 pero preconfigurado para CALIRAL.",
        categoria="productor",
        parametros=[
            QueryParametro(
                nombre="empresa", tipo="select", label="Empresa",
                requerido=True, opciones=[],
                descripcion="Empresa a analizar"
            ),
        ] + _periodo_params() + [_limit_param(50)],
        sql="""
            SELECT
                m.nro_productor AS "N° Productor",
                m.nombre_productor AS "Nombre Productor",
                COUNT(*) AS "Movimientos",
                ROUND(SUM(m.kilos_netos), 2) AS "Kg Totales",
                ROUND(AVG(m.kilos_netos), 2) AS "Kg Promedio",
                MIN(m.fecha_movimiento) AS "Primera Fecha",
                MAX(m.fecha_movimiento) AS "Última Fecha"
            FROM movimientos m
            WHERE m.empresa_id = :empresa
              AND m.nro_productor IS NOT NULL AND m.nro_productor != ''
              AND (:fecha_desde = '' OR m.fecha_movimiento >= :fecha_desde)
              AND (:fecha_hasta = '' OR m.fecha_movimiento <= :fecha_hasta)
            GROUP BY m.nro_productor, m.nombre_productor
            ORDER BY SUM(m.kilos_netos) DESC
            LIMIT :limite;
        """,
        reglas_negocio=["RN-001: Lista productores ordenados por kg total descendente"],
    ),

    # ── CONS-005 ──────────────────────────────────────────
    QueryDefinicion(
        id="CONS-005",
        nombre="Mercados que trabaja una empresa",
        descripcion="Qué mercados (países/destinos) atiende una empresa y su participación en cada uno.",
        categoria="mercado",
        parametros=[
            _empresa_param(),
        ] + _periodo_params() + [_limit_param(50)],
        sql="""
            SELECT
                COALESCE(NULLIF(TRIM(m.destino), ''), 'URUGUAY (Mercado Interno)') AS "Mercado",
                COUNT(*) AS "Movimientos",
                ROUND(SUM(m.kilos_netos), 2) AS "Kg Totales",
                ROUND(AVG(m.kilos_netos), 2) AS "Kg Promedio",
                ROUND(SUM(m.kilos_netos) * 100.0 / NULLIF(
                    (SELECT SUM(kilos_netos) FROM movimientos WHERE empresa_id = :empresa), 0
                ), 2) AS "Participación %",
                MIN(m.fecha_movimiento) AS "Primera Fecha",
                MAX(m.fecha_movimiento) AS "Última Fecha"
            FROM movimientos m
            WHERE m.empresa_id = :empresa
              AND (:fecha_desde = '' OR m.fecha_movimiento >= :fecha_desde)
              AND (:fecha_hasta = '' OR m.fecha_movimiento <= :fecha_hasta)
            GROUP BY COALESCE(NULLIF(TRIM(m.destino), ''), 'URUGUAY (Mercado Interno)')
            ORDER BY SUM(m.kilos_netos) DESC
            LIMIT :limite;
        """,
        reglas_negocio=[
            "RN-001: destino vacío = 'URUGUAY (Mercado Interno)'",
            "RN-002: Participación % calculada sobre el total de kg de la empresa en el período",
        ],
    ),

    # ── CONS-006 ──────────────────────────────────────────
    QueryDefinicion(
        id="CONS-006",
        nombre="Mercados que trabaja ARBIZA (o empresa)",
        descripcion="Igual que CONS-005.",
        categoria="mercado",
        parametros=[
            _empresa_param(),
        ] + _periodo_params() + [_limit_param(50)],
        sql="""
            SELECT
                COALESCE(NULLIF(TRIM(m.destino), ''), 'URUGUAY (Mercado Interno)') AS "Mercado",
                COUNT(*) AS "Movimientos",
                ROUND(SUM(m.kilos_netos), 2) AS "Kg Totales",
                ROUND(AVG(m.kilos_netos), 2) AS "Kg Promedio",
                ROUND(SUM(m.kilos_netos) * 100.0 / NULLIF(
                    (SELECT SUM(kilos_netos) FROM movimientos WHERE empresa_id = :empresa), 0
                ), 2) AS "Participación %",
                MIN(m.fecha_movimiento) AS "Primera Fecha",
                MAX(m.fecha_movimiento) AS "Última Fecha"
            FROM movimientos m
            WHERE m.empresa_id = :empresa
              AND (:fecha_desde = '' OR m.fecha_movimiento >= :fecha_desde)
              AND (:fecha_hasta = '' OR m.fecha_movimiento <= :fecha_hasta)
            GROUP BY COALESCE(NULLIF(TRIM(m.destino), ''), 'URUGUAY (Mercado Interno)')
            ORDER BY SUM(m.kilos_netos) DESC
            LIMIT :limite;
        """,
        reglas_negocio=["RN-001: Mismos criterios que CONS-005"],
    ),

    # ── CONS-007 ──────────────────────────────────────────
    QueryDefinicion(
        id="CONS-007",
        nombre="Mercados donde competencia participa pero empresa no",
        descripcion="Mercados con volumen donde la empresa de referencia NO participa pero la competencia sí.",
        categoria="mercado",
        parametros=[
            _empresa_param("Empresa"),
            _empresa_param("Empresa Competencia"),
        ] + _periodo_params() + [_limit_param(50)],
        sql="""
            SELECT
                COALESCE(NULLIF(TRIM(m_comp.destino), ''), 'URUGUAY (Mercado Interno)') AS "Mercado",
                COUNT(DISTINCT m_comp.empresa_id) AS "Empresas que Participan",
                ROUND(SUM(m_comp.kilos_netos), 2) AS "Kg Total Competencia",
                ROUND(AVG(m_comp.kilos_netos), 2) AS "Kg Promedio"
            FROM movimientos m_comp
            WHERE m_comp.empresa_id != :empresa
              AND COALESCE(NULLIF(TRIM(m_comp.destino), ''), 'URUGUAY (Mercado Interno)')
                  NOT IN (
                      SELECT DISTINCT COALESCE(NULLIF(TRIM(mm.destino), ''), 'URUGUAY (Mercado Interno)')
                      FROM movimientos mm
                      WHERE mm.empresa_id = :empresa
                  )
              AND (:fecha_desde = '' OR m_comp.fecha_movimiento >= :fecha_desde)
              AND (:fecha_hasta = '' OR m_comp.fecha_movimiento <= :fecha_hasta)
            GROUP BY COALESCE(NULLIF(TRIM(m_comp.destino), ''), 'URUGUAY (Mercado Interno)')
            ORDER BY SUM(m_comp.kilos_netos) DESC
            LIMIT :limite;
        """,
        reglas_negocio=[
            "RN-001: Solo mercados donde la empresa NO tiene ningún movimiento",
            "RN-002: Ordenado por kg total de la competencia descendente",
        ],
    ),

    # ── CONS-008 ──────────────────────────────────────────
    QueryDefinicion(
        id="CONS-008",
        nombre="Productores compartidos entre dos empresas",
        descripcion="Productores que trabajan tanto con la empresa A como con la empresa B.",
        categoria="productor",
        parametros=[
            _empresa_param("Empresa A"),
            _empresa_param("Empresa B"),
        ] + _periodo_params() + [_limit_param(50)],
        sql="""
            SELECT
                m1.nro_productor AS "N° Productor",
                m1.nombre_productor AS "Nombre Productor",
                e_a.nombre_unif AS "Empresa A",
                e_b.nombre_unif AS "Empresa B",
                ROUND(SUM(CASE WHEN m1.empresa_id = :empresa_a THEN m1.kilos_netos ELSE 0 END), 2) AS "Kg Empresa A",
                ROUND(SUM(CASE WHEN m1.empresa_id = :empresa_b THEN m1.kilos_netos ELSE 0 END), 2) AS "Kg Empresa B",
                ROUND(SUM(m1.kilos_netos), 2) AS "Kg Total",
                COUNT(DISTINCT m1.empresa_id) AS "Empresas"
            FROM movimientos m1
            JOIN dim_empresas e_a ON m1.empresa_id = e_a.id_empresa
            JOIN dim_empresas e_b ON :empresa_b = e_b.id_empresa
            WHERE m1.nro_productor IN (
                  SELECT nro_productor FROM movimientos WHERE empresa_id = :empresa_a AND nro_productor IS NOT NULL AND nro_productor != ''
                  INTERSECT
                  SELECT nro_productor FROM movimientos WHERE empresa_id = :empresa_b AND nro_productor IS NOT NULL AND nro_productor != ''
            )
              AND m1.empresa_id IN (:empresa_a, :empresa_b)
              AND (:fecha_desde = '' OR m1.fecha_movimiento >= :fecha_desde)
              AND (:fecha_hasta = '' OR m1.fecha_movimiento <= :fecha_hasta)
            GROUP BY m1.nro_productor, m1.nombre_productor
            ORDER BY SUM(m1.kilos_netos) DESC
            LIMIT :limite;
        """,
        reglas_negocio=[
            "RN-001: Productor debe tener al menos 1 movimiento con cada empresa",
            "RN-002: Se muestra volumen separado por empresa",
        ],
    ),

    # ── CONS-009 ──────────────────────────────────────────
    QueryDefinicion(
        id="CONS-009",
        nombre="Productores que nunca utilizaron una empresa",
        descripcion="Productores con volumen significativo que nunca trabajaron con la empresa seleccionada.",
        categoria="productor",
        parametros=[
            _empresa_param("Empresa"),
        ] + _periodo_params() + [_limit_param(50)],
        sql="""
            SELECT
                m.nro_productor AS "N° Productor",
                m.nombre_productor AS "Nombre Productor",
                COUNT(DISTINCT m.empresa_id) AS "Empresas que Usan",
                ROUND(SUM(m.kilos_netos), 2) AS "Kg Total",
                COUNT(*) AS "Movimientos",
                MIN(m.fecha_movimiento) AS "Primera Fecha",
                MAX(m.fecha_movimiento) AS "Última Fecha"
            FROM movimientos m
            WHERE m.nro_productor NOT IN (
                  SELECT DISTINCT nro_productor FROM movimientos
                  WHERE empresa_id = :empresa AND nro_productor IS NOT NULL AND nro_productor != ''
            )
              AND m.nro_productor IS NOT NULL AND m.nro_productor != ''
              AND (:fecha_desde = '' OR m.fecha_movimiento >= :fecha_desde)
              AND (:fecha_hasta = '' OR m.fecha_movimiento <= :fecha_hasta)
            GROUP BY m.nro_productor, m.nombre_productor
            ORDER BY SUM(m.kilos_netos) DESC
            LIMIT :limite;
        """,
        reglas_negocio=[
            "RN-001: Productor nunca tuvo movimiento con la empresa",
            "RN-002: Ordenado por kg total descendente",
        ],
    ),

    # ── CONS-010 ──────────────────────────────────────────
    QueryDefinicion(
        id="CONS-010",
        nombre="Principales clientes de una empresa",
        descripcion="Top clientes (destinos) de una empresa ordenados por volumen.",
        categoria="empresa",
        parametros=[
            _empresa_param(),
        ] + _periodo_params() + [_limit_param(50)],
        sql="""
            SELECT
                m.destino AS "Cliente",
                COUNT(*) AS "Movimientos",
                ROUND(SUM(m.kilos_netos), 2) AS "Kg Totales",
                ROUND(AVG(m.kilos_netos), 2) AS "Kg Promedio",
                ROUND(SUM(m.kilos_netos) * 100.0 / NULLIF(
                    (SELECT SUM(kilos_netos) FROM movimientos WHERE empresa_id = :empresa), 0
                ), 2) AS "Participación %",
                MIN(m.fecha_movimiento) AS "Primera Fecha",
                MAX(m.fecha_movimiento) AS "Última Fecha"
            FROM movimientos m
            WHERE m.empresa_id = :empresa
              AND m.destino IS NOT NULL AND TRIM(m.destino) != ''
              AND (:fecha_desde = '' OR m.fecha_movimiento >= :fecha_desde)
              AND (:fecha_hasta = '' OR m.fecha_movimiento <= :fecha_hasta)
            GROUP BY m.destino
            ORDER BY SUM(m.kilos_netos) DESC
            LIMIT :limite;
        """,
        reglas_negocio=[
            "RN-001: Cliente = campo destino",
            "RN-002: Excluye destinos vacíos",
        ],
    ),

    # ── CONS-011 ──────────────────────────────────────────
    QueryDefinicion(
        id="CONS-011",
        nombre="Principales certificadores",
        descripcion="Ranking de certificadores por kg certificados.",
        categoria="certificador",
        parametros=[
            QueryParametro(
                nombre="empresa", tipo="select", label="Empresa",
                requerido=False, opciones=[],
                descripcion="Filtrar por empresa (opcional)"
            ),
        ] + _periodo_params() + [_limit_param(50)],
        sql="""
            SELECT
                m.nombre_establecimiento AS "Certificador",
                m.nro_certificado AS "N° Certificado",
                COUNT(*) AS "Movimientos",
                ROUND(SUM(m.kilos_netos), 2) AS "Kg Totales",
                ROUND(AVG(m.kilos_netos), 2) AS "Kg Promedio",
                COUNT(DISTINCT m.nro_productor) AS "Productores",
                MIN(m.fecha_movimiento) AS "Primera Fecha",
                MAX(m.fecha_movimiento) AS "Última Fecha"
            FROM movimientos m
            WHERE m.nro_certificado IS NOT NULL AND m.nro_certificado != ''
              AND (:empresa = 0 OR m.empresa_id = :empresa)
              AND (:fecha_desde = '' OR m.fecha_movimiento >= :fecha_desde)
              AND (:fecha_hasta = '' OR m.fecha_movimiento <= :fecha_hasta)
            GROUP BY m.nombre_establecimiento, m.nro_certificado
            ORDER BY SUM(m.kilos_netos) DESC
            LIMIT :limite;
        """,
        reglas_negocio=[
            "RN-001: Certificador = nombre_establecimiento del movimiento",
            "RN-002: Se requiere nro_certificado para considerar válido",
        ],
    ),

    # ── CONS-012 ──────────────────────────────────────────
    QueryDefinicion(
        id="CONS-012",
        nombre="Principales depósitos",
        descripcion="Ranking de depósitos por kg procesados.",
        categoria="deposito",
        parametros=[
            QueryParametro(
                nombre="empresa", tipo="select", label="Empresa",
                requerido=False, opciones=[],
                descripcion="Filtrar por empresa (opcional)"
            ),
        ] + _periodo_params() + [_limit_param(50)],
        sql="""
            SELECT
                m.nombre_establecimiento AS "Depósito",
                m.departamento AS "Departamento",
                COUNT(*) AS "Movimientos",
                ROUND(SUM(m.kilos_netos), 2) AS "Kg Totales",
                ROUND(AVG(m.kilos_netos), 2) AS "Kg Promedio",
                COUNT(DISTINCT m.nro_productor) AS "Productores",
                MIN(m.fecha_movimiento) AS "Primera Fecha",
                MAX(m.fecha_movimiento) AS "Última Fecha"
            FROM movimientos m
            WHERE m.solo_deposito = 1
              AND m.nombre_establecimiento IS NOT NULL
              AND (:empresa = 0 OR m.empresa_id = :empresa)
              AND (:fecha_desde = '' OR m.fecha_movimiento >= :fecha_desde)
              AND (:fecha_hasta = '' OR m.fecha_movimiento <= :fecha_hasta)
            GROUP BY m.nombre_establecimiento, m.departamento
            ORDER BY SUM(m.kilos_netos) DESC
            LIMIT :limite;
        """,
        reglas_negocio=[
            "RN-001: Depósito = establecimiento con solo_deposito = 1",
            "RN-002: Incluye departamento para distinguir depósitos con mismo nombre",
        ],
    ),

    # ── CONS-013 ──────────────────────────────────────────
    QueryDefinicion(
        id="CONS-013",
        nombre="Ranking de productores",
        descripcion="Top productores por volumen kg a nivel global o por empresa.",
        categoria="ranking",
        parametros=[
            QueryParametro(
                nombre="empresa", tipo="select", label="Empresa",
                requerido=False, opciones=[],
                descripcion="Filtrar por empresa (0 = todas)"
            ),
        ] + _periodo_params() + [_limit_param(50)],
        sql="""
            SELECT
                m.nro_productor AS "N° Productor",
                m.nombre_productor AS "Nombre Productor",
                COUNT(DISTINCT m.empresa_id) AS "Empresas",
                COUNT(*) AS "Movimientos",
                ROUND(SUM(m.kilos_netos), 2) AS "Kg Totales",
                ROUND(AVG(m.kilos_netos), 2) AS "Kg Promedio",
                MIN(m.fecha_movimiento) AS "Primera Fecha",
                MAX(m.fecha_movimiento) AS "Última Fecha"
            FROM movimientos m
            WHERE m.nro_productor IS NOT NULL AND m.nro_productor != ''
              AND (:empresa = 0 OR m.empresa_id = :empresa)
              AND (:fecha_desde = '' OR m.fecha_movimiento >= :fecha_desde)
              AND (:fecha_hasta = '' OR m.fecha_movimiento <= :fecha_hasta)
            GROUP BY m.nro_productor, m.nombre_productor
            ORDER BY SUM(m.kilos_netos) DESC
            LIMIT :limite;
        """,
        reglas_negocio=[
            "RN-001: Productor puede aparecer en múltiples empresas (columna Empresas)",
            "RN-002: Ordenado por kg_totales descendente",
        ],
    ),

    # ── CONS-014 ──────────────────────────────────────────
    QueryDefinicion(
        id="CONS-014",
        nombre="Ranking de mercados",
        descripcion="Top mercados por volumen kg.",
        categoria="ranking",
        parametros=[
            QueryParametro(
                nombre="empresa", tipo="select", label="Empresa",
                requerido=False, opciones=[],
                descripcion="Filtrar por empresa (0 = todas)"
            ),
        ] + _periodo_params() + [_limit_param(50)],
        sql="""
            SELECT
                COALESCE(NULLIF(TRIM(m.destino), ''), 'URUGUAY (Mercado Interno)') AS "Mercado",
                COUNT(*) AS "Movimientos",
                ROUND(SUM(m.kilos_netos), 2) AS "Kg Totales",
                ROUND(AVG(m.kilos_netos), 2) AS "Kg Promedio",
                COUNT(DISTINCT m.empresa_id) AS "Empresas",
                MIN(m.fecha_movimiento) AS "Primera Fecha",
                MAX(m.fecha_movimiento) AS "Última Fecha"
            FROM movimientos m
            WHERE (:empresa = 0 OR m.empresa_id = :empresa)
              AND (:fecha_desde = '' OR m.fecha_movimiento >= :fecha_desde)
              AND (:fecha_hasta = '' OR m.fecha_movimiento <= :fecha_hasta)
            GROUP BY COALESCE(NULLIF(TRIM(m.destino), ''), 'URUGUAY (Mercado Interno)')
            ORDER BY SUM(m.kilos_netos) DESC
            LIMIT :limite;
        """,
        reglas_negocio=["RN-001: Mercado = destino normalizado"],
    ),

    # ── CONS-015 ──────────────────────────────────────────
    QueryDefinicion(
        id="CONS-015",
        nombre="Ranking de productos",
        descripcion="Top productos por volumen kg.",
        categoria="ranking",
        parametros=[
            QueryParametro(
                nombre="empresa", tipo="select", label="Empresa",
                requerido=False, opciones=[],
                descripcion="Filtrar por empresa (0 = todas)"
            ),
        ] + _periodo_params() + [_limit_param(50)],
        sql="""
            SELECT
                p.nombre_producto AS "Producto",
                p.categoria AS "Categoría",
                COUNT(*) AS "Movimientos",
                ROUND(SUM(m.kilos_netos), 2) AS "Kg Totales",
                ROUND(AVG(m.kilos_netos), 2) AS "Kg Promedio",
                COUNT(DISTINCT m.empresa_id) AS "Empresas",
                MIN(m.fecha_movimiento) AS "Primera Fecha",
                MAX(m.fecha_movimiento) AS "Última Fecha"
            FROM movimientos m
            JOIN dim_productos p ON m.producto_id = p.id_producto
            WHERE (:empresa = 0 OR m.empresa_id = :empresa)
              AND (:fecha_desde = '' OR m.fecha_movimiento >= :fecha_desde)
              AND (:fecha_hasta = '' OR m.fecha_movimiento <= :fecha_hasta)
            GROUP BY p.nombre_producto, p.categoria
            ORDER BY SUM(m.kilos_netos) DESC
            LIMIT :limite;
        """,
        reglas_negocio=["RN-001: Producto = dim_productos.nombre_producto"],
    ),
]


def get_consulta_por_id(consulta_id: str) -> QueryDefinicion | None:
    for q in CONSULTAS_CATALOGO:
        if q.id == consulta_id:
            return q
    return None


def get_consultas_por_categoria(categoria: str) -> list[QueryDefinicion]:
    return [q for q in CONSULTAS_CATALOGO if q.categoria == categoria]


CATEGORIAS = ["exportacion", "productor", "mercado", "ranking", "deposito", "certificador", "empresa"]
