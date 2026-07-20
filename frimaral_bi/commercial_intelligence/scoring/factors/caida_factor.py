"""
=================================================================================
caida_factor.py — Factor: Caída
=================================================================================
Calculates decline score - detects sustained decrease (inverse factor).
"""

from __future__ import annotations

from typing import Any
from .factor_base import FactorBase


class CaidaFactor(FactorBase):
    """Factor de Caída: Detecta disminución sostenida (factor inverso)."""

    def calculate(self, id_empresa: int, periodo: str = "ultimos_6_meses") -> Any:
        """
        Calculate decline factor (0-100).

        This is an INVERSE factor - lower decline = higher score.
        100 = no decline, 0 = severe decline.
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
            pct_change = 0

        # Inverse score: decline reduces score
        # -50% or worse = 0
        # 0% = 50
        # +50% or better = 100
        score = min(100, max(0, 50 + pct_change))

        peso = self.config.peso if self.config else 15
        contribucion = score * peso / 100

        tendencia = "↓ CAÍDA" if pct_change < -10 else "↑ ALZA" if pct_change > 10 else "→ ESTABLE"

        return self._create_result(
            factor_key="caida",
            factor_nombre="Caída / Estabilidad",
            valor=score,
            peso=peso,
            contribucion=contribucion,
            comparacion_periodo=tendencia,
            detalle=f"Variación: {pct_change:+.1f}% ({periodo})",
        )

    def detectar_sostenida(self, id_empresa: int) -> bool:
        """Detect if decline is sustained over 3+ consecutive months."""
        query = """
            WITH monthly_kg AS (
                SELECT
                    strftime('%Y-%m', m.fecha_movimiento) as mes,
                    SUM(m.kilos_netos) as kg
                FROM movimientos m
                WHERE m.empresa_id = ?
                GROUP BY mes
                ORDER BY mes DESC
                LIMIT 6
            )
            SELECT
                mes,
                kg,
                LAG(kg) OVER (ORDER BY mes) as kg_anterior,
                kg - LAG(kg) OVER (ORDER BY mes) as variacion
            FROM monthly_kg
            ORDER BY mes DESC
        """
        results = self.repo.execute(query, (id_empresa,))

        if not results or len(results) < 3:
            return False

        # Check last 3 months for continuous decline
        decline_count = 0
        for r in results[:3]:
            if r.get("variacion", 0) < 0:
                decline_count += 1

        return decline_count >= 3
