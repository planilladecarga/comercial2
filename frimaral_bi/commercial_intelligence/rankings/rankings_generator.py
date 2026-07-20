"""
=================================================================================
rankings_generator.py — Generador de Rankings
=================================================================================
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from ..database import db


class RankingsGenerator:
    """
    Generador de rankings automáticos.

    Genera rankings pre-calculados para:
    - Top Oportunidades
    - Top Riesgos
    - Top Crecimiento
    - Top Fidelidad
    - Top Productores
    - Top Mercados
    - Top Competidores
    """

    def __init__(
        self,
        scoring_service: Any,
        risk_engine: Any,
        opportunity_engine: Any,
        repo_emp360: Any
    ):
        """
        Inicializa el generador de rankings.

        Args:
            scoring_service: Servicio de scoring
            risk_engine: Motor de riesgo
            opportunity_engine: Motor de oportunidad
            repo_emp360: Repositorio de empresa360
        """
        self.scoring_service = scoring_service
        self.risk_engine = risk_engine
        self.opportunity_engine = opportunity_engine
        self.repo_emp360 = repo_emp360

    def generar_todos(self, periodo: str = "ultimos_6_meses") -> dict[str, list[dict]]:
        """
        Genera todos los rankings.

        Args:
            periodo: Período de evaluación

        Returns:
            Diccionario con rankings por tipo
        """
        rankings = {}

        rankings["TOP_OPORTUNIDADES"] = self.generar("TOP_OPORTUNIDADES", 20, periodo)
        rankings["TOP_RIESGOS"] = self.generar("TOP_RIESGOS", 20, periodo)
        rankings["TOP_CRECIMIENTO"] = self.generar("TOP_CRECIMIENTO", 20, periodo)
        rankings["TOP_FIDELIDAD"] = self.generar("TOP_FIDELIDAD", 20, periodo)
        rankings["TOP_PRODUCTORES"] = self.generar("TOP_PRODUCTORES", 20, periodo)
        rankings["TOP_MERCADOS"] = self.generar("TOP_MERCADOS", 20, periodo)

        # Guardar rankings en BD
        self._guardar_rankings(rankings, periodo)

        return rankings

    def generar(
        self,
        tipo_ranking: str,
        limite: int = 20,
        periodo: str = "ultimos_6_meses"
    ) -> list[dict]:
        """
        Genera un ranking específico.

        Args:
            tipo_ranking: Tipo de ranking
            limite: Cantidad de elementos
            periodo: Período de evaluación

        Returns:
            Lista de elementos del ranking
        """
        generators = {
            "TOP_OPORTUNIDADES": self._ranking_oportunidades,
            "TOP_RIESGOS": self._ranking_riesgos,
            "TOP_CRECIMIENTO": self._ranking_crecimiento,
            "TOP_FIDELIDAD": self._ranking_fidelidad,
            "TOP_PRODUCTORES": self._ranking_productores,
            "TOP_MERCADOS": self._ranking_mercados,
            "TOP_COMPETIDORES": self._ranking_competidores,
        }

        generator = generators.get(tipo_ranking)
        if not generator:
            return []

        return generator(limite, periodo)

    def _ranking_oportunidades(self, limite: int, periodo: str) -> list[dict]:
        """Ranking de Top Oportunidades."""
        query = """
            SELECT
                e.id_empresa,
                e.nombre_unif AS nombre,
                s.score_total AS score_parcial
            FROM dim_empresas e
            LEFT JOIN scores_empresa s ON e.id_empresa = s.id_empresa
            WHERE e.activo = 1
              AND e.es_productor = 1
            ORDER BY s.score_total DESC, e.cant_movimientos DESC
            LIMIT ?
        """
        results = db.execute(query, (limite,))
        return [
            {
                "nombre": r["nombre"],
                "id_empresa": r["id_empresa"],
                "score_parcial": r["score_parcial"] or 0,
            }
            for r in results
        ]

    def _ranking_riesgos(self, limite: int, periodo: str) -> list[dict]:
        """Ranking de Top Riesgos."""
        query = """
            SELECT
                e.id_empresa,
                e.nombre_unif AS nombre,
                s.nivel_riesgo,
                s.score_total AS score_parcial
            FROM dim_empresas e
            LEFT JOIN scores_empresa s ON e.id_empresa = s.id_empresa
            WHERE e.activo = 1
            ORDER BY
                CASE s.nivel_riesgo
                    WHEN 'CRITICO' THEN 1
                    WHEN 'ALTO' THEN 2
                    WHEN 'MEDIO' THEN 3
                    WHEN 'BAJO' THEN 4
                END,
                s.score_total ASC
            LIMIT ?
        """
        results = db.execute(query, (limite,))
        return [
            {
                "nombre": r["nombre"],
                "id_empresa": r["id_empresa"],
                "nivel_riesgo": r["nivel_riesgo"] or "BAJO",
                "score_parcial": r["score_parcial"] or 50,
            }
            for r in results
        ]

    def _ranking_crecimiento(self, limite: int, periodo: str) -> list[dict]:
        """Ranking de Top Crecimiento."""
        query = """
            SELECT
                e.id_empresa,
                e.nombre_unif AS nombre,
                s.breakdown_json
            FROM dim_empresas e
            LEFT JOIN scores_empresa s ON e.id_empresa = s.id_empresa
            WHERE e.activo = 1
            ORDER BY e.cant_movimientos DESC
            LIMIT ?
        """
        results = db.execute(query, (limite,))

        ranking = []
        for r in results:
            import json
            try:
                breakdown = json.loads(r["breakdown_json"]) if r["breakdown_json"] else {}
                crecimiento = 0
                for f in breakdown.get("factores", []):
                    if f.get("factor_key") == "crecimiento":
                        crecimiento = f.get("valor", 0)
                        break
                ranking.append({
                    "nombre": r["nombre"],
                    "id_empresa": r["id_empresa"],
                    "score_parcial": crecimiento,
                })
            except Exception:
                ranking.append({
                    "nombre": r["nombre"],
                    "id_empresa": r["id_empresa"],
                    "score_parcial": 0,
                })

        ranking.sort(key=lambda x: x["score_parcial"], reverse=True)
        return ranking[:limite]

    def _ranking_fidelidad(self, limite: int, periodo: str) -> list[dict]:
        """Ranking de Top Fidelidad."""
        query = """
            SELECT
                e.id_empresa,
                e.nombre_unif AS nombre,
                s.nivel_fidelidad,
                s.score_total AS score_parcial
            FROM dim_empresas e
            LEFT JOIN scores_empresa s ON e.id_empresa = s.id_empresa
            WHERE e.activo = 1
            ORDER BY
                CASE s.nivel_fidelidad
                    WHEN 'MUY_ALTA' THEN 1
                    WHEN 'ALTA' THEN 2
                    WHEN 'MEDIA' THEN 3
                    WHEN 'BAJA' THEN 4
                    WHEN 'MUY_BAJA' THEN 5
                END
            LIMIT ?
        """
        results = db.execute(query, (limite,))
        return [
            {
                "nombre": r["nombre"],
                "id_empresa": r["id_empresa"],
                "nivel_fidelidad": r["nivel_fidelidad"] or "MEDIA",
                "score_parcial": r["score_parcial"] or 50,
            }
            for r in results
        ]

    def _ranking_productores(self, limite: int, periodo: str) -> list[dict]:
        """Ranking de Top Productores."""
        query = """
            SELECT
                e.id_empresa,
                e.nombre_unif AS nombre,
                SUM(m.kilos_netos) AS kg_total
            FROM dim_empresas e
            JOIN movimientos m ON e.id_empresa = m.empresa_id
            WHERE e.activo = 1
              AND e.es_productor = 1
            GROUP BY e.id_empresa, e.nombre_unif
            ORDER BY kg_total DESC
            LIMIT ?
        """
        results = db.execute(query, (limite,))
        return [
            {
                "nombre": r["nombre"],
                "id_empresa": r["id_empresa"],
                "kg_total": r["kg_total"] or 0,
            }
            for r in results
        ]

    def _ranking_mercados(self, limite: int, periodo: str) -> list[dict]:
        """Ranking de Top Mercados."""
        query = """
            SELECT
                COALESCE(NULLIF(TRIM(m.destino), ''), 'URUGUAY (Mercado Interno)') AS mercado,
                SUM(m.kilos_netos) AS kg_total,
                COUNT(DISTINCT m.empresa_id) AS cant_empresas
            FROM movimientos m
            WHERE m.destino IS NOT NULL
            GROUP BY mercado
            ORDER BY kg_total DESC
            LIMIT ?
        """
        results = db.execute(query, (limite,))
        return [
            {
                "nombre": r["mercado"],
                "kg_total": r["kg_total"] or 0,
                "cant_empresas": r["cant_empresas"] or 0,
            }
            for r in results
        ]

    def _ranking_competidores(self, limite: int, periodo: str) -> list[dict]:
        """Ranking de Top Competidores."""
        query = """
            SELECT
                e.id_empresa,
                e.nombre_unif AS nombre,
                SUM(m.kilos_netos) AS kg_total,
                COUNT(DISTINCT m.nro_productor) AS productores_unicos
            FROM dim_empresas e
            JOIN movimientos m ON e.id_empresa = m.empresa_id
            WHERE e.activo = 1
              AND e.es_competidor = 1
            GROUP BY e.id_empresa, e.nombre_unif
            ORDER BY kg_total DESC
            LIMIT ?
        """
        results = db.execute(query, (limite,))
        return [
            {
                "nombre": r["nombre"],
                "id_empresa": r["id_empresa"],
                "kg_total": r["kg_total"] or 0,
                "productores_unicos": r["productores_unicos"] or 0,
            }
            for r in results
        ]

    def _guardar_rankings(
        self,
        rankings: dict[str, list[dict]],
        periodo: str
    ) -> None:
        """Guarda los rankings en la base de datos."""
        fecha = datetime.now().isoformat()

        for tipo_ranking, items in rankings.items():
            for posicion, item in enumerate(items, 1):
                db.execute(
                    """INSERT OR REPLACE INTO rankings
                       (tipo_ranking, id_empresa, posicion, score_parcial,
                        metricas_json, fecha_calculo, periodo_evaluado)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (
                        tipo_ranking,
                        item.get("id_empresa", 0),
                        posicion,
                        item.get("score_parcial", 0),
                        str(item),
                        fecha,
                        periodo,
                    )
                )
