"""
Servicio de Rankings - Módulo 8.
Genera rankings de los mejores elementos.
"""
from ..database import db
from ..queries.comando_queries import (
    QUERY_RANKING_PRODUCTORES,
    QUERY_RANKING_DEPOSITOS,
    QUERY_RANKING_CERTIFICADORES,
    QUERY_RANKING_MERCADOS,
    QUERY_RANKING_PRODUCTOS,
)


class RankingsService:
    """Genera rankings de top elementos."""

    def obtener_rankings(self) -> dict:
        """Retorna todos los rankings."""
        return {
            "top_productores": self._ranking_productores(),
            "top_depositos": self._ranking_depositos(),
            "top_certificadores": self._ranking_certificadores(),
            "top_mercados": self._ranking_mercados(),
            "top_productos": self._ranking_productos(),
        }

    def _ranking_productores(self) -> list[dict]:
        rows = db.execute(QUERY_RANKING_PRODUCTORES)
        return [
            {"ranking": i + 1, "nombre": r["nombre_productor"], "kg": r["kg_total"] or 0.0, "cantidad": r["cantidad_movimientos"]}
            for i, r in enumerate(rows)
        ]

    def _ranking_depositos(self) -> list[dict]:
        rows = db.execute(QUERY_RANKING_DEPOSITOS)
        return [
            {"ranking": i + 1, "nombre": r["nombre"], "kg": r["kg_total"] or 0.0, "cantidad": r["cantidad_movimientos"]}
            for i, r in enumerate(rows)
        ]

    def _ranking_certificadores(self) -> list[dict]:
        rows = db.execute(QUERY_RANKING_CERTIFICADORES)
        return [
            {"ranking": i + 1, "nombre": r["nombre"], "kg": r["kg_total"] or 0.0, "cantidad": r["cantidad_movimientos"]}
            for i, r in enumerate(rows)
        ]

    def _ranking_mercados(self) -> list[dict]:
        rows = db.execute(QUERY_RANKING_MERCADOS)
        return [
            {"ranking": i + 1, "nombre": r["nombre"], "kg": r["kg_total"] or 0.0, "cantidad": r["cantidad_movimientos"]}
            for i, r in enumerate(rows)
        ]

    def _ranking_productos(self) -> list[dict]:
        rows = db.execute(QUERY_RANKING_PRODUCTOS)
        return [
            {"ranking": i + 1, "nombre": r["nombre"], "kg": r["kg_total"] or 0.0, "cantidad": r["cantidad_movimientos"]}
            for i, r in enumerate(rows)
        ]


rankings_service = RankingsService()
