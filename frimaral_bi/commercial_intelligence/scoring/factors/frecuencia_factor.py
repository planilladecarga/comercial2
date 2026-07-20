"""
=================================================================================
frecuencia_factor.py — Factor: Frecuencia de Movimientos
=================================================================================
Calculates frequency score based on movement count vs previous period.
"""

from __future__ import annotations

from typing import Any
from .factor_base import FactorBase


class FrecuenciaFactor(FactorBase):
    """Factor de Frecuencia: Compara cantidad de movimientos vs período anterior."""

    def calculate(self, id_empresa: int, periodo: str = "ultimos_6_meses") -> Any:
        """
        Calculate frequency factor (0-100).

        Compares movement count vs previous period.
        """
        meses = self._periodo_a_meses(periodo)
        movs_act = self._query_movimientos(id_empresa, meses)
        movs_ant = self._query_movimientos_anterior(id_empresa, meses)

        cant_act = len(movs_act)
        cant_ant = len(movs_ant)

        # Calculate score based on trend
        if cant_ant > 0:
            ratio = cant_act / cant_ant
            # Score: 50 = igual, 100 = doble, 0 = cero
            score = min(100, max(0, ratio * 50))
        else:
            score = 80 if cant_act > 0 else 20  # New empresa bonus

        peso = self.config.peso if self.config else 15
        contribucion = score * peso / 100

        return self._create_result(
            factor_key="frecuencia",
            factor_nombre="Frecuencia de Movimientos",
            valor=score,
            peso=peso,
            contribucion=contribucion,
            comparacion_periodo=f"{cant_act} vs {cant_ant} anterior",
            detalle=f"{cant_act} movimientos ({periodo})",
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
