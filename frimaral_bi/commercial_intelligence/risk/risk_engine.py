"""
=================================================================================
risk_engine.py — Motor de Riesgo
=================================================================================
"""

from __future__ import annotations

from typing import Any, Optional
from dataclasses import dataclass

from .risk_levels import RiskLevel
from ..scoring.models import ScoreResult


@dataclass
class RiskAnalysis:
    """Resultado del análisis de riesgo."""
    nivel: RiskLevel
    score: float
    factores_riesgo: list[str]
    alertas: list[str]
    nivel_verbose: str

    def __str__(self) -> str:
        return f"{self.nivel.value} ({self.score:.1f})"


class RiskEngine:
    """
    Motor de cálculo de riesgo comercial.

    Analiza múltiples factores para determinar el nivel de riesgo
    de una empresa.
    """

    def __init__(self, scoring_service: Any):
        """
        Inicializa el motor de riesgo.

        Args:
            scoring_service: Servicio de scoring
        """
        self.scoring_service = scoring_service

    def calcular_riesgo(
        self,
        id_empresa: int,
        score_result: ScoreResult
    ) -> RiskAnalysis:
        """
        Calcula el nivel de riesgo para una empresa.

        Args:
            id_empresa: ID de la empresa
            score_result: Resultado del scoring

        Returns:
            RiskAnalysis con el nivel de riesgo y detalles
        """
        score = score_result.score_total if score_result else 0

        # Get factor details
        factores_riesgo = []
        alertas = []

        if score_result and score_result.breakdown:
            for factor in score_result.breakdown.factores:
                # Low volume factor
                if factor.factor_key == "volumen" and factor.valor < 30:
                    factores_riesgo.append("Volumen bajo")
                    alertas.append(f"⚠️ Volumen muy bajo: {factor.valor:.0f}/100")

                # Negative growth
                if factor.factor_key == "crecimiento" and factor.valor < 30:
                    factores_riesgo.append("Crecimiento negativo")
                    alertas.append(f"⚠️ Crecimiento en declive: {factor.valor:.0f}/100")

                # High decline
                if factor.factor_key == "caida" and factor.valor < 30:
                    factores_riesgo.append("Caída sostenida")
                    alertas.append(f"⚠️ Caída detectada: {factor.valor:.0f}/100")

                # Low diversification
                if factor.factor_key == "mercado_div" and factor.valor < 30:
                    factores_riesgo.append("Baja diversificación")
                    alertas.append(f"⚠️ Mercados poco diversificados: {factor.valor:.0f}/100")

        # Check for inactivity
        meses_inactivo = self._verificar_inactividad(id_empresa)
        if meses_inactivo >= 2:
            factores_riesgo.append(f"Inactivo {meses_inactivo} meses")
            alertas.append(f"⚠️ Empresa inactiva por {meses_inactivo} meses")

        # Determine level
        nivel = RiskLevel.from_score(score)

        # Map to verbose level
        nivel_verbose = {
            RiskLevel.BAJO: "Riesgo Bajo - Empresa estable",
            RiskLevel.MEDIO: "Riesgo Medio - Requiere seguimiento",
            RiskLevel.ALTO: "Riesgo Alto - Intervención recomendada",
            RiskLevel.CRITICO: "Riesgo Crítico - Acción inmediata",
        }.get(nivel, "Desconocido")

        return RiskAnalysis(
            nivel=nivel,
            score=score,
            factores_riesgo=factores_riesgo,
            alertas=alertas,
            nivel_verbose=nivel_verbose,
        )

    def _verificar_inactividad(self, id_empresa: int) -> int:
        """Verifica meses de inactividad."""
        from ...api.database import db

        query = """
            SELECT MAX(m.fecha_movimiento) as ultima_fecha
            FROM movimientos m
            WHERE m.empresa_id = ?
        """
        result = db.execute_one(query, (id_empresa,))

        if not result or not result["ultima_fecha"]:
            return 99  # Never been active

        # Calculate months since last movement
        meses_query = """
            SELECT
                (strftime('%Y', 'now') - strftime('%Y', ?)) * 12 +
                (strftime('%m', 'now') - strftime('%m', ?)) as meses
        """
        meses_result = db.execute_one(meses_query, (result["ultima_fecha"], result["ultima_fecha"]))
        return meses_result["meses"] if meses_result else 0
