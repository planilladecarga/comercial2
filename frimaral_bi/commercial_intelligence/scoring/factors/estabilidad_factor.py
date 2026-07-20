"""
=================================================================================
estabilidad_factor.py — Factor: Estabilidad Comercial
=================================================================================
Calculates commercial stability score.
"""

from __future__ import annotations

from typing import Any
from .factor_base import FactorBase


class EstabilidadFactor(FactorBase):
    """Factor de Estabilidad: Evalúa consistencia de patrones comerciales."""

    def calculate(self, id_empresa: int, periodo: str = "ultimos_6_meses") -> Any:
        """
        Calculate stability factor (0-100).

        Based on consistency of monthly volumes.
        """
        meses = self._periodo_a_meses(periodo)

        query = """
            SELECT
                strftime('%Y-%m', m.fecha_movimiento) as mes,
                SUM(m.kilos_netos) as kg
            FROM movimientos m
            WHERE m.empresa_id = ?
              AND m.fecha_movimiento >= date('now', ?)
            GROUP BY mes
            ORDER BY mes DESC
        """
        results = self.repo.execute(query, (id_empresa, f"-{meses} months"))

        if not results or len(results) < 2:
            score = 70  # No enough data
            detalle = "Datos insuficientes para evaluar estabilidad"
        else:
            # Calculate coefficient of variation
            kgs = [r["kg"] for r in results if r["kg"]]
            if not kgs:
                score = 50
            else:
                avg = sum(kgs) / len(kgs)
                if avg > 0:
                    variance = sum((k - avg) ** 2 for k in kgs) / len(kgs)
                    std_dev = variance ** 0.5
                    cv = std_dev / avg  # Coefficient of variation

                    # Lower CV = more stable = higher score
                    # CV 0 = perfect stability = 100
                    # CV 1+ = high variability = 0
                    score = max(0, min(100, 100 - (cv * 100)))
                else:
                    score = 50

            detalle = f"Coeficiente de variación: {score:.0f}/100"

        peso = self.config.peso if self.config else 0  # No tiene peso fijo
        if peso == 0:
            peso = 0  # Se calcula dinámicamente

        contribucion = score * peso / 100 if peso > 0 else 0

        return self._create_result(
            factor_key="estabilidad",
            factor_nombre="Estabilidad Comercial",
            valor=score,
            peso=peso,
            contribucion=contribucion,
            comparacion_periodo="vs_mes_anterior",
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
