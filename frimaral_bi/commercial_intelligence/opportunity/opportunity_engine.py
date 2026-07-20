"""
=================================================================================
opportunity_engine.py — Motor de Oportunidad
=================================================================================
"""

from __future__ import annotations

from typing import Any
from dataclasses import dataclass
from enum import Enum

from ..scoring.models import ScoreResult


class PotentialLevel(str, Enum):
    """Niveles de potencial."""
    MUY_ALTO = "MUY_ALTO"
    ALTO = "ALTO"
    MEDIO = "MEDIO"
    BAJO = "BAJO"


@dataclass
class OpportunityAnalysis:
    """Resultado del análisis de oportunidad."""
    nivel: PotentialLevel
    score: float
    factores_oportunidad: list[str]
    detalles: list[str]

    def __str__(self) -> str:
        return f"{self.nivel.value} ({self.score:.1f})"


class OpportunityEngine:
    """
    Motor de cálculo de potencial comercial.

    Analiza múltiples factores para determinar el nivel de potencial
    de una empresa.
    """

    def __init__(self, scoring_service: Any):
        """
        Inicializa el motor de oportunidad.

        Args:
            scoring_service: Servicio de scoring
        """
        self.scoring_service = scoring_service

    def calcular_potencial(
        self,
        id_empresa: int,
        score_result: ScoreResult
    ) -> OpportunityAnalysis:
        """
        Calcula el nivel de potencial para una empresa.

        Args:
            id_empresa: ID de la empresa
            score_result: Resultado del scoring

        Returns:
            OpportunityAnalysis con el nivel de potencial y detalles
        """
        score = score_result.score_total if score_result else 0

        factores_oportunidad = []
        detalles = []

        if score_result and score_result.breakdown:
            for factor in score_result.breakdown.factores:
                # Strong growth
                if factor.factor_key == "crecimiento" and factor.valor > 70:
                    factores_oportunidad.append("Alto crecimiento")
                    detalles.append(f"📈 Crecimiento fuerte: {factor.valor:.0f}/100")

                # High diversification
                if factor.factor_key == "mercado_div" and factor.valor > 70:
                    factores_oportunidad.append("Alta diversificación mercados")
                    detalles.append(f"🌍 Diversificación de mercados: {factor.valor:.0f}/100")

                if factor.factor_key == "producto_div" and factor.valor > 70:
                    factores_oportunidad.append("Alta diversificación productos")
                    detalles.append(f"📦 Diversificación de productos: {factor.valor:.0f}/100")

                # Multiple deposits (flexibility)
                if factor.factor_key == "depositos" and factor.valor > 70:
                    factores_oportunidad.append("Múltiples depósitos")
                    detalles.append(f"🏭 Usa múltiples depósitos: {factor.valor:.0f}/100")

        # Determine level based on score and factors
        if score >= 80 and len(factores_oportunidad) >= 2:
            nivel = PotentialLevel.MUY_ALTO
        elif score >= 70 or len(factores_oportunidad) >= 1:
            nivel = PotentialLevel.ALTO
        elif score >= 50:
            nivel = PotentialLevel.MEDIO
        else:
            nivel = PotentialLevel.BAJO

        return OpportunityAnalysis(
            nivel=nivel,
            score=score,
            factores_oportunidad=factores_oportunidad,
            detalles=detalles,
        )
