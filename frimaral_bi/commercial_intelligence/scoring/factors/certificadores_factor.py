"""
=================================================================================
certificadores_factor.py — Factor: Cantidad de Certificadores
=================================================================================
Calculates certifier usage score.
"""

from __future__ import annotations

from typing import Any
from .factor_base import FactorBase


class CertificadoresFactor(FactorBase):
    """Factor de Certificadores: Compara cantidad de certificadores únicos."""

    def calculate(self, id_empresa: int, periodo: str = "ultimos_6_meses") -> Any:
        """
        Calculate certifier factor (0-100).

        Multiple certifiers = higher score (quality indicator).
        """
        meses = self._periodo_a_meses(periodo)

        query = """
            SELECT DISTINCT
                m.nro_certificado,
                m.nombre_establecimiento as certificador
            FROM movimientos m
            WHERE m.empresa_id = ?
              AND m.fecha_movimiento >= date('now', ?)
              AND m.nro_certificado IS NOT NULL
              AND m.nro_certificado != ''
        """
        results = self.repo.execute(query, (id_empresa, f"-{meses} months"))
        cant_certificadores = len(results)

        # Score based on certifier count
        if cant_certificadores == 0:
            score = 50  # Sin certificadores (puede ser válido)
        elif cant_certificadores == 1:
            score = 60
        elif cant_certificadores == 2:
            score = 80
        else:
            score = 100

        peso = self.config.peso if self.config else 5
        contribucion = score * peso / 100

        return self._create_result(
            factor_key="certificadores",
            factor_nombre="Cantidad de Certificadores",
            valor=score,
            peso=peso,
            contribucion=contribucion,
            comparacion_periodo=f"{cant_certificadores} certificadores",
            detalle=f"{cant_certificadores} certificadores ({periodo})",
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
