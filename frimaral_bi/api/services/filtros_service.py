"""
Servicio de Filtros - Datos para los filtros globales.
"""
from ..database import db
from ..queries.comando_queries import (
    QUERY_FILTRO_ANOS,
    QUERY_FILTRO_MESES,
    QUERY_FILTRO_PRODUCTORES,
    QUERY_FILTRO_CERTIFICADORES,
    QUERY_FILTRO_DEPOSITOS,
    QUERY_FILTRO_MERCADOS,
    QUERY_FILTRO_PRODUCTOS,
    QUERY_FILTRO_TEMPERATURAS,
    QUERY_FILTRO_TIPOS_MOVIMIENTO,
)


class FiltrosService:
    """Provee las opciones disponibles para los filtros globales."""

    def obtener_filtros(self) -> dict:
        """Retorna todas las opciones de filtro."""
        return {
            "anos": [r["anio"] for r in db.execute(QUERY_FILTRO_ANOS)],
            "meses": [{"mes": r["mes"], "nombre": r["nombre_mes"]} for r in db.execute(QUERY_FILTRO_MESES)],
            "productores": [
                {"nro": r["nro_productor"], "nombre": r["nombre_productor"]}
                for r in db.execute(QUERY_FILTRO_PRODUCTORES)[:100]  # Limitar a 100
            ],
            "certificadores": [
                {"id": r["id_empresa"], "nombre": r["nombre_unif"]}
                for r in db.execute(QUERY_FILTRO_CERTIFICADORES)
            ],
            "depositos": [
                {"id": r["id_empresa"], "nombre": r["nombre_unif"]}
                for r in db.execute(QUERY_FILTRO_DEPOSITOS)
            ],
            "mercados": [r["mercado"] for r in db.execute(QUERY_FILTRO_MERCADOS)],
            "productos": [
                {"id": r["id_producto"], "nombre": r["nombre_producto"], "categoria": r["categoria"]}
                for r in db.execute(QUERY_FILTRO_PRODUCTOS)
            ],
            "temperaturas": [r["temperatura"] for r in db.execute(QUERY_FILTRO_TEMPERATURAS)],
            "tipos_movimiento": [r["tipo_movimiento"] for r in db.execute(QUERY_FILTRO_TIPOS_MOVIMIENTO)],
        }


filtros_service = FiltrosService()
