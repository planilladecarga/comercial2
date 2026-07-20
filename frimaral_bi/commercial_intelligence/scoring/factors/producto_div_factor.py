"""
=================================================================================
producto_div_factor.py — Factor: Diversificación de Productos
=================================================================================
Calculates product diversification score.
"""

from __future__ import annotations

from typing import Any
from .factor_base import FactorBase


class ProductoDivFactor(FactorBase):
    """Factor de Diversificación de Productos: Compara cantidad de productos únicos."""

    def calculate(self, id_empresa: int, periodo: str = "ultimos_6_meses") -> Any:
        """
        Calculate product diversification factor (0-100).

        More products = higher score.
        """
        meses = self._periodo_a_meses(periodo)
        movs = self._query_movimientos(id_empresa, meses)

        cant_productos = self._unique_count(movs, "producto")

        # Score based on product count
        # More products = more diversified = higher score
        if cant_productos == 0:
            score = 10
        elif cant_productos == 1:
            score = 25  # Monoproducto - risk
        elif cant_productos == 2:
            score = 50
        elif cant_productos == 3:
            score = 70
        elif cant_productos == 4:
            score = 85
        else:
            score = 100

        peso = self.config.peso if self.config else 10
        contribucion = score * peso / 100

        detalle = f"{cant_productos} productos diferentes ({periodo})"
        if cant_productos == 1:
            detalle += " ⚠️ MONOPRODUCTO"

        return self._create_result(
            factor_key="producto_div",
            factor_nombre="Diversificación de Productos",
            valor=score,
            peso=peso,
            contribucion=contribucion,
            comparacion_periodo=f"{cant_productos} productos",
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
