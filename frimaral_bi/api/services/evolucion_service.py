"""
Servicio de Evolución - Módulo 7.
Muestra la evolución temporal del negocio.
"""
from ..database import db
from ..queries.comando_queries import QUERY_EVOLUCION_MENSUAL


class EvolucionService:
    """Genera datos de evolución mensual."""

    def obtener_evolucion(self) -> dict:
        """Retorna datos de evolución por mes."""
        rows = db.execute(QUERY_EVOLUCION_MENSUAL)

        meses = [
            {
                "anio": r["anio"],
                "mes": r["mes"],
                "nombre_mes": r["nombre_mes"],
                "kg": r["kg"] or 0.0,
                "clientes_count": r["clientes_count"] or 0,
                "mercados_count": r["mercados_count"] or 0,
                "productores_count": r["productores_count"] or 0,
            }
            for r in rows
        ]

        return {"meses": meses}


evolucion_service = EvolucionService()
