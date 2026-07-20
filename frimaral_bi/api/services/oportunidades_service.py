"""
Servicio de Oportunidades - Módulo 3.
Identifica oportunidades de crecimiento comercial.
"""
from ..database import db
from ..queries.comando_queries import (
    QUERY_TOP_20_PRODUCTORES_POTENCIALES,
    QUERY_MERCADOS_NO_PARTICIPA,
    QUERY_PRODUCTORES_COMPETENCIA,
    QUERY_PRODUCTORES_COMPARTIDOS,
    QUERY_CLIENTES_POTENCIALES,
)


class Oportunidad:
    def __init__(self, tipo: str, ranking: int, nombre: str, kg: float, detalle: str):
        self.tipo = tipo
        self.ranking = ranking
        self.nombre = nombre
        self.kg = kg
        self.detalle = detalle

    def to_dict(self) -> dict:
        return {
            "tipo": self.tipo,
            "ranking": self.ranking,
            "nombre": self.nombre,
            "kg": self.kg,
            "detalle": self.detalle,
        }


class OportunidadesService:
    """Identifica oportunidades de negocio para CALIRAL."""

    def obtener_oportunidades(self, id_empresa: int) -> dict:
        """Retorna todas las oportunidades."""
        return {
            "top_20_productores_potenciales": self._productores_potenciales(id_empresa),
            "mercados_no_participa": self._mercados_no_participa(id_empresa),
            "productores_competencia": self._productores_competencia(id_empresa),
            "productores_compartidos": self._productores_compartidos(id_empresa),
            "clientes_potenciales": self._clientes_potenciales(id_empresa),
        }

    def _productores_potenciales(self, id_empresa: int) -> list[dict]:
        rows = db.execute(QUERY_TOP_20_PRODUCTORES_POTENCIALES, (id_empresa, id_empresa))
        return [
            Oportunidad(
                tipo="potencial_caliral",
                ranking=i + 1,
                nombre=r["nombre_productor"],
                kg=r["kg_total"] or 0.0,
                detalle=f"{r['empresas_count']} empresa(s) — {r['kg_total']:,.0f} kg",
            ).to_dict()
            for i, r in enumerate(rows)
        ]

    def _mercados_no_participa(self, id_empresa: int) -> list[dict]:
        rows = db.execute(QUERY_MERCADOS_NO_PARTICIPA, (id_empresa, id_empresa))
        return [
            Oportunidad(
                tipo="mercado_no_participa",
                ranking=i + 1,
                nombre=r["mercado"],
                kg=r["kg_total"] or 0.0,
                detalle=f"{r['kg_total']:,.0f} kg de oportunidad",
            ).to_dict()
            for i, r in enumerate(rows)
        ]

    def _productores_competencia(self, id_empresa: int) -> list[dict]:
        rows = db.execute(QUERY_PRODUCTORES_COMPETENCIA, (id_empresa, id_empresa))
        return [
            Oportunidad(
                tipo="competencia",
                ranking=i + 1,
                nombre=r["nombre_productor"],
                kg=r["kg_total"] or 0.0,
                detalle=f"También trabaja con {r['empresas_count']} empresa(s)",
            ).to_dict()
            for i, r in enumerate(rows)
        ]

    def _productores_compartidos(self, id_empresa: int) -> list[dict]:
        rows = db.execute(QUERY_PRODUCTORES_COMPARTIDOS, (id_empresa, id_empresa))
        return [
            Oportunidad(
                tipo="compartido",
                ranking=i + 1,
                nombre=r["nombre_productor"],
                kg=r["kg_total"] or 0.0,
                detalle=f"{r['empresas_count']} empresa(s) — {r['kg_total']:,.0f} kg",
            ).to_dict()
            for i, r in enumerate(rows)
        ]

    def _clientes_potenciales(self, id_empresa: int) -> list[dict]:
        rows = db.execute(QUERY_CLIENTES_POTENCIALES, (id_empresa, id_empresa))
        return [
            Oportunidad(
                tipo="cliente_potencial",
                ranking=i + 1,
                nombre=r["nombre"],
                kg=r["kg_total"] or 0.0,
                detalle=f"{r['kg_total']:,.0f} kg con la competencia",
            ).to_dict()
            for i, r in enumerate(rows)
        ]


oportunidades_service = OportunidadesService()
