"""
=================================================================================
mercado_div_factor.py — Factor: Diversificación de Mercados
=================================================================================
Calculates market diversification score.
"""

from __future__ import annotations

from typing import Any
from .factor_base import FactorBase


class MercadoDivFactor(FactorBase):
    """Factor de Diversificación de Mercados: Compara cantidad de mercados únicos."""

    def calculate(self, id_empresa: int, periodo: str = "ultimos_6_meses") -> Any:
        """
        Calculate market diversification factor (0-100).

        More markets = higher score.
        """
        meses = self._periodo_a_meses(periodo)
        movs = self._query_movimientos(id_empresa, meses)

        cant_mercados = self._unique_count(movs, "destino")

        # Score based on market count
        # 1 market = 20, 2-3 = 40-60, 4-5 = 70-85, 6+ = 90-100
        if cant_mercados == 0:
            score = 10
        elif cant_mercados == 1:
            score = 30
        elif cant_mercados == 2:
            score = 50
        elif cant_mercados == 3:
            score = 65
        elif cant_mercados == 4:
            score = 80
        elif cant_mercados == 5:
            score = 90
        else:
            score = 100

        peso = self.config.peso if self.config else 10
        contribucion = score * peso / 100

        return self._create_result(
            factor_key="mercado_div",
            factor_nombre="Diversificación de Mercados",
            valor=score,
            peso=peso,
            contribucion=contribucion,
            comparacion_periodo=f"{cant_mercados} mercados",
            detalle=f"{cant_mercados} mercados diferentes ({periodo})",
        )
