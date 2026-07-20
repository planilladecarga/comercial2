"""
Servicio de Resumen Ejecutivo - Módulo 1.
"""
from ..database import db
from ..queries.comando_queries import (
    QUERY_RESUMEN_TOTALES,
    QUERY_RESUMEN_EXPORTACIONES,
    QUERY_RESUMEN_DEPOSITO,
    QUERY_RESUMEN_CANTIDADES,
    QUERY_FECHA_ULTIMA_ACTUALIZACION,
)


class ResumenService:
    """Genera el resumen ejecutivo general."""

    def obtener_resumen(self) -> dict:
        """Retorna el resumen ejecutivo completo."""
        totales = db.execute_one(QUERY_RESUMEN_TOTALES) or {}
        exportaciones = db.execute_one(QUERY_RESUMEN_EXPORTACIONES) or {}
        deposito = db.execute_one(QUERY_RESUMEN_DEPOSITO) or {}
        cantidades = db.execute_one(QUERY_RESUMEN_CANTIDADES) or {}
        fecha = db.execute_one(QUERY_FECHA_ULTIMA_ACTUALIZACION) or {}

        return {
            "fecha_actualizacion": fecha.get("fecha_ultima", "N/A"),
            "cantidad_movimientos": totales.get("cantidad_movimientos", 0),
            "kg_totales": totales.get("kg_totales", 0) or 0.0,
            "exportaciones_kg": exportaciones.get("kg_exportaciones", 0) or 0.0,
            "deposito_kg": deposito.get("kg_deposito", 0) or 0.0,
            "cantidad_empresas": cantidades.get("empresas", 0),
            "cantidad_productoras": cantidades.get("productoras", 0),
            "cantidad_certificadores": cantidades.get("certificadores", 0),
            "cantidad_depositos": cantidades.get("depositos", 0),
            "cantidad_mercados": cantidades.get("mercados", 0),
            "cantidad_productos": cantidades.get("productos", 0),
        }


resumen_service = ResumenService()
