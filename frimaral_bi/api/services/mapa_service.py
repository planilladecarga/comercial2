"""
Servicio de Mapa Comercial - Módulo 6.
Muestra la distribución geográfica del negocio.
"""
from ..database import db
from ..queries.comando_queries import (
    QUERY_MAPA_PAISES,
    QUERY_MAPA_CRECIMIENTO,
)


class MapaService:
    """Genera datos del mapa comercial."""

    def obtener_mapa(self) -> dict:
        """Retorna datos de países para el mapa."""
        paises_raw = db.execute(QUERY_MAPA_PAISES)
        crecimiento_raw = db.execute(QUERY_MAPA_CRECIMIENTO)

        # Mapear crecimiento por país
        crecimiento_map = {r["pais"]: r["crecimiento_pct"] for r in crecimiento_raw}

        # Total para calcular participación
        total_kg = sum(r["kg_total"] or 0 for r in paises_raw)
        if total_kg == 0:
            total_kg = 1

        paises = []
        for r in paises_raw:
            kg = r["kg_total"] or 0.0
            paises.append({
                "pais": r["pais"],
                "kg": kg,
                "participacion_pct": round(kg / total_kg * 100, 2),
                "crecimiento_pct": crecimiento_map.get(r["pais"], 0.0),
            })

        return {
            "paises": paises,
            "total_kg": total_kg,
        }


mapa_service = MapaService()
