"""
Servicio de Comparación Competitiva - Módulo 4.
Compara CALIRAL vs empresa seleccionada.
"""
from typing import Optional
from ..database import db
from ..queries.comando_queries import (
    QUERY_COMPARACION_KG,
    QUERY_PARTICIPACION_MERCADO,
    QUERY_COMPETIDORES_COMPARACION,
    QUERY_LISTAR_EMPRESAS,
)


class CompetenciaService:
    """Genera comparaciones competitivas entre empresas."""

    def listar_empresas(self) -> list[dict]:
        """Lista todas las empresas disponibles para comparar."""
        return db.execute(QUERY_LISTAR_EMPRESAS)

    def comparar(self, id_a: int, id_b: int) -> Optional[dict]:
        """Compara empresa A vs empresa B."""
        # Obtener kg de ambas
        kg_data = db.execute(QUERY_COMPARACION_KG, (id_a, id_b))
        if not kg_data:
            return None

        kg_a = next((r["kg_total"] for r in kg_data if r["id_empresa"] == id_a), 0.0)
        kg_b = next((r["kg_total"] for r in kg_data if r["id_empresa"] == id_b), 0.0)
        nombre_a = next((r["nombre_unif"] for r in kg_data if r["id_empresa"] == id_a), "")
        nombre_b = next((r["nombre_unif"] for r in kg_data if r["id_empresa"] == id_b), "")

        # Total para participación
        total_kg = kg_a + kg_b
        part_a = (kg_a / total_kg * 100) if total_kg > 0 else 0.0
        part_b = (kg_b / total_kg * 100) if total_kg > 0 else 0.0

        # Datos de cada empresa
        datos_a = db.execute_one(QUERY_COMPETIDORES_COMPARACION, (id_a,))
        datos_b = db.execute_one(QUERY_COMPETIDORES_COMPARACION, (id_b,))

        return {
            "empresa_a": nombre_a,
            "empresa_b": nombre_b,
            "kg_a": kg_a,
            "kg_b": kg_b,
            "participacion_a": round(part_a, 2),
            "participacion_b": round(part_b, 2),
            "comparacion": {
                "a": {
                    "kg": kg_a,
                    "participacion_pct": round(part_a, 2),
                    "mercados_count": datos_a["mercados_count"] if datos_a else 0,
                    "clientes_count": datos_a["clientes_count"] if datos_a else 0,
                    "productos_count": datos_a["productos_count"] if datos_a else 0,
                    "productores_count": datos_a["productores_count"] if datos_a else 0,
                },
                "b": {
                    "kg": kg_b,
                    "participacion_pct": round(part_b, 2),
                    "mercados_count": datos_b["mercados_count"] if datos_b else 0,
                    "clientes_count": datos_b["clientes_count"] if datos_b else 0,
                    "productos_count": datos_b["productos_count"] if datos_b else 0,
                    "productores_count": datos_b["productores_count"] if datos_b else 0,
                },
            },
        }


competencia_service = CompetenciaService()
