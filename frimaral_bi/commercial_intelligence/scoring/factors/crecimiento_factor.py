"""
=================================================================================
crecimiento_factor.py — Factor: Crecimiento
=================================================================================
Calculates growth score based on volume change vs previous period.
"""

from __future__ import annotations

from typing import Any
from .factor_base import FactorBase


class CrecimientoFactor(FactorBase):
    """Factor de Crecimiento: Variación % de volumen vs período anterior."""

    def calculate(self, id_empresa: int, periodo: str = "ultimos_6_meses") -> Any:
        """
        Calculate growth factor (0-100).

        Positive growth = higher score.
        """
        meses = self._periodo_a_meses(periodo)
        movs_act = self._query_movimientos(id_empresa, meses)
        movs_ant = self._query_movimientos_anterior(id_empresa, meses)

        kg_act = self._kg_total(movs_act)
        kg_ant = self._kg_total(movs_ant)

        # Calculate percentage change
        if kg_ant > 0:
            pct_change = ((kg_act - kg_ant) / kg_ant) * 100
        else:
            pct_change = 100 if kg_act > 0 else 0

        # Score mapping:
        # -50% or less = 0
        # 0% = 50
        # +50% or more = 100
        score = min(100, max(0, 50 + pct_change))

        peso = self.config.peso if self.config else 20
        contribucion = score * peso / 100

        return self._create_result(
            factor_key="crecimiento",
            factor_nombre="Crecimiento",
            valor=score,
            peso=peso,
            contribucion=contribucion,
            comparacion_periodo=f"{pct_change:+.1f}%",
            detalle=f"{kg_act:,.0f} kg vs {kg_ant:,.0f} kg anterior ({pct_change:+.1f}%)",
        )

    def _periodo_a_meses(self, periodo: str) -> int:
        """Convert period string to months."""
        mapping = {
            "ultimo_mes": 1,
            "ultimos_3_meses": 3,
            "ultimos_6_meses": 6,
            "ultimo_anio": 12,
            "ultimos_2_anios": 24,
        }
        return mapping.get(periodo, 6)
