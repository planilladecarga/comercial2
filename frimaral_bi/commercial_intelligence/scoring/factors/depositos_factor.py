"""
=================================================================================
depositos_factor.py — Factor: Cantidad de Depósitos
=================================================================================
Calculates deposit usage score.
"""

from __future__ import annotations

from typing import Any
from .factor_base import FactorBase


class DepositosFactor(FactorBase):
    """Factor de Depósitos: Compara cantidad de depósitos utilizados."""

    def calculate(self, id_empresa: int, periodo: str = "ultimos_6_meses") -> Any:
        """
        Calculate deposit factor (0-100).

        Multiple deposits = higher score (flexibility indicator).
        """
        meses = self._periodo_a_meses(periodo)
        movs = self._query_movimientos(id_empresa, meses)

        cant_depositos = self._unique_count(movs, "nombre_establecimiento")

        # Score based on deposit count
        # 1 = 30 (dependent), 2-3 = 60-80, 4+ = 90-100
        if cant_depositos == 0:
            score = 10
        elif cant_depositos == 1:
            score = 30  # Single deposit - dependency risk
        elif cant_depositos == 2:
            score = 60
        elif cant_depositos == 3:
            score = 80
        else:
            score = 100

        peso = self.config.peso if self.config else 5
        contribucion = score * peso / 100

        detalle = f"{cant_depositos} depósitos ({periodo})"
        if cant_depositos == 1:
            detalle += " ⚠️ UN SOLO DEPÓSITO"

        return self._create_result(
            factor_key="depositos",
            factor_nombre="Cantidad de Depósitos",
            valor=score,
            peso=peso,
            contribucion=contribucion,
            comparacion_periodo=f"{cant_depositos} depósitos",
            detalle=detalle,
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
