"""
=================================================================================
indicators_calculator.py — Calculador de Indicadores
=================================================================================
"""

from __future__ import annotations

from typing import Any, Optional
from dataclasses import dataclass

from ..scoring.models import ScoreResult, IndicatorResult


@dataclass
class IndicatorsBundle:
    """Bundle de indicadores calculados."""
    opportunity_score: float
    risk_score: float
    loyalty_score: float
    growth_score: float
    diversification_score: float
    competitiveness_score: float

    def to_dict(self) -> dict[str, float]:
        return {
            "OPPORTUNITY_SCORE": self.opportunity_score,
            "RISK_SCORE": self.risk_score,
            "LOYALTY_SCORE": self.loyalty_score,
            "GROWTH_SCORE": self.growth_score,
            "DIVERSIFICATION_SCORE": self.diversification_score,
            "COMPETITIVENESS_SCORE": self.competitiveness_score,
        }


class IndicatorsCalculator:
    """
    Calculador de indicadores comerciales.

    Calcula los 6 indicadores principales:
    - Opportunity Score
    - Risk Score
    - Loyalty Score
    - Growth Score
    - Diversification Score
    - Competitiveness Score
    """

    def __init__(self, repo_emp360: Any):
        """
        Inicializa el calculador.

        Args:
            repo_emp360: Repositorio de empresa360
        """
        self.repo_emp360 = repo_emp360

    def calcular_todos(
        self,
        id_empresa: int,
        score_result: Optional[ScoreResult] = None
    ) -> dict[str, Any]:
        """
        Calcula todos los indicadores para una empresa.

        Args:
            id_empresa: ID de la empresa
            score_result: Resultado del scoring (opcional)

        Returns:
            Diccionario con todos los indicadores
        """
        if score_result is None:
            # Create empty result if not provided
            score_result = ScoreResult(
                id_empresa=id_empresa,
                nombre_empresa="",
                score_total=50,
            )

        # Extract factor values
        factores = {}
        if score_result and score_result.breakdown:
            for f in score_result.breakdown.factores:
                factores[f.factor_key] = f.valor

        # Calculate each indicator
        indicators = IndicatorsBundle(
            opportunity_score=self._calc_opportunity_score(factores, score_result),
            risk_score=self._calc_risk_score(factores, score_result),
            loyalty_score=self._calc_loyalty_score(factores, score_result),
            growth_score=self._calc_growth_score(factores),
            diversification_score=self._calc_diversification_score(factores),
            competitiveness_score=self._calc_competitiveness_score(id_empresa, factores),
        )

        return {
            **indicators.to_dict(),
            "details": {
                "OPPORTUNITY_SCORE": self._get_opportunity_detail(factores),
                "RISK_SCORE": self._get_risk_detail(factores),
                "LOYALTY_SCORE": self._get_loyalty_detail(factores),
                "GROWTH_SCORE": self._get_growth_detail(factores),
                "DIVERSIFICATION_SCORE": self._get_diversification_detail(factores),
                "COMPETITIVENESS_SCORE": self._get_competitiveness_detail(id_empresa),
            }
        }

    def _calc_opportunity_score(
        self,
        factores: dict[str, float],
        score_result: ScoreResult
    ) -> float:
        """Calcula Opportunity Score (0-100)."""
        crecimiento = factores.get("crecimiento", 50)
        mercado_div = factores.get("mercado_div", 50)
        producto_div = factores.get("producto_div", 50)

        # Opportunity = combination of growth and diversification
        opportunity = (crecimiento * 0.5) + (mercado_div * 0.25) + (producto_div * 0.25)
        return min(100, max(0, opportunity))

    def _calc_risk_score(
        self,
        factores: dict[str, float],
        score_result: ScoreResult
    ) -> float:
        """Calcula Risk Score (0-100, lower is better)."""
        score_total = score_result.score_total if score_result else 50
        caida = factores.get("caida", 50)
        volumen = factores.get("volumen", 50)

        # Risk = inverse of score, adjusted by decline
        risk = (100 - score_total) * 0.6 + (100 - caida) * 0.2 + (100 - volumen) * 0.2
        return min(100, max(0, risk))

    def _calc_loyalty_score(
        self,
        factores: dict[str, float],
        score_result: ScoreResult
    ) -> float:
        """Calcula Loyalty Score (0-100)."""
        historial = factores.get("historial", 50)
        frecuencia = factores.get("frecuencia", 50)
        depositos = factores.get("depositos", 50)

        # Loyalty = stability and history
        loyalty = (historial * 0.4) + (frecuencia * 0.3) + (depositos * 0.3)
        return min(100, max(0, loyalty))

    def _calc_growth_score(self, factores: dict[str, float]) -> float:
        """Calcula Growth Score (0-100)."""
        return factores.get("crecimiento", 50)

    def _calc_diversification_score(self, factores: dict[str, float]) -> float:
        """Calcula Diversification Score (0-100)."""
        mercado_div = factores.get("mercado_div", 50)
        producto_div = factores.get("producto_div", 50)
        certificadores = factores.get("certificadores", 50)

        diversification = (mercado_div * 0.5) + (producto_div * 0.3) + (certificadores * 0.2)
        return min(100, max(0, diversification))

    def _calc_competitiveness_score(
        self,
        id_empresa: int,
        factores: dict[str, float]
    ) -> float:
        """Calcula Competitiveness Score (0-100)."""
        # Competitiveness = volume + diversification + frequency
        volumen = factores.get("volumen", 50)
        producto_div = factores.get("producto_div", 50)
        frecuencia = factores.get("frecuencia", 50)

        competitiveness = (volumen * 0.5) + (producto_div * 0.25) + (frecuencia * 0.25)
        return min(100, max(0, competitiveness))

    # Detail methods
    def _get_opportunity_detail(self, factores: dict[str, float]) -> dict[str, Any]:
        score = factores.get("crecimiento", 50)
        if score >= 80:
            nivel = "MUY_ALTO"
            desc = "Alto potencial de crecimiento"
        elif score >= 60:
            nivel = "ALTO"
            desc = "Buen potencial"
        elif score >= 40:
            nivel = "MEDIO"
            desc = "Potencial moderado"
        else:
            nivel = "BAJO"
            desc = "Bajo potencial"

        return {"nivel": nivel, "descripcion": desc}

    def _get_risk_detail(self, factores: dict[str, float]) -> dict[str, Any]:
        score = factores.get("caida", 50)
        if score >= 70:
            nivel = "BAJO"
            desc = "Estable"
        elif score >= 50:
            nivel = "MEDIO"
            desc = "Requiere monitoreo"
        elif score >= 30:
            nivel = "ALTO"
            desc = "Factores de riesgo presentes"
        else:
            nivel = "CRITICO"
            desc = "Riesgo inminente"

        return {"nivel": nivel, "descripcion": desc}

    def _get_loyalty_detail(self, factores: dict[str, float]) -> dict[str, Any]:
        score = factores.get("historial", 50)
        if score >= 80:
            nivel = "MUY_ALTA"
            desc = "Cliente estratégico"
        elif score >= 60:
            nivel = "ALTA"
            desc = "Buena relación"
        elif score >= 40:
            nivel = "MEDIA"
            desc = "Relación en desarrollo"
        else:
            nivel = "BAJA"
            desc = "Relación nueva o inestable"

        return {"nivel": nivel, "descripcion": desc}

    def _get_growth_detail(self, factores: dict[str, float]) -> dict[str, Any]:
        score = factores.get("crecimiento", 50)
        if score >= 80:
            nivel = "MUY_ALTO"
            desc = "Crecimiento acelerado"
        elif score >= 60:
            nivel = "ALTO"
            desc = "Crecimiento sostenido"
        elif score >= 40:
            nivel = "MEDIO"
            desc = "Estable"
        else:
            nivel = "BAJO"
            desc = "Sin crecimiento"

        return {"nivel": nivel, "descripcion": desc}

    def _get_diversification_detail(self, factores: dict[str, float]) -> dict[str, Any]:
        mercado = factores.get("mercado_div", 50)
        producto = factores.get("producto_div", 50)
        score = (mercado + producto) / 2

        if score >= 80:
            nivel = "MUY_ALTO"
            desc = "Altamente diversificado"
        elif score >= 60:
            nivel = "ALTO"
            desc = "Bien diversificado"
        elif score >= 40:
            nivel = "MEDIO"
            desc = "Parcialmente diversificado"
        else:
            nivel = "BAJO"
            desc = "Baja diversificación"

        return {"nivel": nivel, "descripcion": desc}

    def _get_competitiveness_detail(self, id_empresa: int) -> dict[str, Any]:
        emp = self.repo_emp360.empresa_por_id(id_empresa)
        if not emp:
            return {"nivel": "BAJO", "descripcion": "Sin datos"}

        kg = self.repo_emp360.kg_totales(id_empresa)

        if kg >= 1000000:
            nivel = "MUY_ALTO"
            desc = "Líder del sector"
        elif kg >= 500000:
            nivel = "ALTO"
            desc = "Actor principal"
        elif kg >= 100000:
            nivel = "MEDIO"
            desc = "Mediano competidor"
        else:
            nivel = "BAJO"
            desc = "Pequeño actor"

        return {"nivel": nivel, "descripcion": desc}
