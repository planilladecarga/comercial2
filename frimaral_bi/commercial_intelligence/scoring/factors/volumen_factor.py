"""
=================================================================================
volumen_factor.py — Factor: Volumen Total
=================================================================================
Calculates volume score based on total kg vs sector average.
"""

from __future__ import annotations

from typing import Any, Optional
from .factor_base import FactorBase


class VolumenFactor(FactorBase):
    """Factor de Volumen Total: Compara kg totales vs promedio del sector."""

    def calculate(self, id_empresa: int, periodo: str = "ultimos_6_meses") -> Any:
        """
        Calculate volume factor (0-100).

        Compares empresa's total volume against sector average.
        """
        meses = self._periodo_a_meses(periodo)
        movs = self._query_movimientos(id_empresa, meses)
        kg_empresa = self._kg_total(movs)

        # Get sector average
        kg_promedio = self._get_sector_promedio(id_empresa, meses)

        # Calculate score
        if kg_promedio > 0:
            ratio = kg_empresa / kg_promedio
            # Score: 50 = promedio, 100 = 2x promedio, 0 = mínimo
            score = min(100, max(0, 50 + (ratio - 1) * 50))
        else:
            score = 50 if kg_empresa > 0 else 0

        peso = self.config.peso if self.config else 20
        contribucion = score * peso / 100

        return self._create_result(
            factor_key="volumen",
            factor_nombre="Volumen Total",
            valor=score,
            peso=peso,
            contribucion=contribucion,
            comparacion_periodo=f"{kg_empresa:,.0f} kg vs {kg_promedio:,.0f} kg promedio",
            detalle=f"{kg_empresa:,.0f} kg ({periodo})",
        )

    def _get_sector_promedio(self, id_empresa: int, meses: int) -> float:
        """Get average volume for empresas of same type."""
        emp = self.repo.empresa_por_id(id_empresa)
        if not emp:
            return 0

        tipo = emp.get("tipo_principal", "PRODUCTOR")

        query = """
            WITH empresa_tipo AS (
                SELECT DISTINCT id_empresa
                FROM dim_empresas
                WHERE tipo_principal = ? AND activo = 1
            )
            SELECT AVG(kg_tipo) as promedio
            FROM (
                SELECT SUM(m.kilos_netos) as kg_tipo
                FROM movimientos m
                JOIN empresa_tipo e ON m.empresa_id = e.id_empresa
                WHERE m.fecha_movimiento >= date('now', ?)
                GROUP BY m.empresa_id
            )
        """
        result = self.repo.execute_one(query, (tipo, f"-{meses} months"))
        return result["promedio"] if result and result["promedio"] else 0

    def detectar_dependencia(self, id_empresa: int) -> str:
        """Detect if empresa has excessive dependence on a single client."""
        query = """
            WITH clientes AS (
                SELECT
                    COALESCE(NULLIF(TRIM(m.destino), ''), 'MERCADO INTERNO') as cliente,
                    SUM(m.kilos_netos) as kg
                FROM movimientos m
                WHERE m.empresa_id = ?
                GROUP BY cliente
            ),
            total AS (
                SELECT SUM(kg) as total_kg FROM clientes
            )
            SELECT
                c.cliente,
                c.kg,
                ROUND(c.kg * 100.0 / NULLIF(t.total_kg, 0), 2) as porcentaje
            FROM clientes c, total t
            ORDER BY porcentaje DESC
            LIMIT 1
        """
        result = self.repo.execute_one(query, (id_empresa,))

        if result and result["porcentaje"]:
            pct = result["porcentaje"]
            if pct >= 70:
                return "ALTA"
            elif pct >= 40:
                return "MEDIA"
            else:
                return "BAJA"
        return "BAJA"

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
