"""
=================================================================================
risk_levels.py — Niveles de Riesgo
=================================================================================
"""

from __future__ import annotations

from enum import Enum


class RiskLevel(str, Enum):
    """Niveles de riesgo comercial."""
    BAJO = "BAJO"
    MEDIO = "MEDIO"
    ALTO = "ALTO"
    CRITICO = "CRITICO"

    @classmethod
    def from_score(cls, score: float) -> "RiskLevel":
        """Determina el nivel de riesgo basándose en el score."""
        if score >= 70:
            return cls.BAJO
        elif score >= 50:
            return cls.MEDIO
        elif score >= 30:
            return cls.ALTO
        else:
            return cls.CRITICO

    @classmethod
    def from_factors(
        cls,
        score: float,
        caida_pct: float,
        meses_inactivo: int,
        cambios_deposito: float
    ) -> "RiskLevel":
        """Determina el nivel basándose en múltiples factores."""
        # Check for critical conditions
        if score < 30:
            return cls.CRITICO
        if caida_pct < -40:
            return cls.CRITICO
        if meses_inactivo >= 3:
            return cls.CRITICO

        # High risk conditions
        if score < 50:
            return cls.ALTO
        if caida_pct < -20:
            return cls.ALTO
        if cambios_deposito > 0.5:
            return cls.ALTO

        # Medium risk
        if score < 70:
            return cls.MEDIO

        return cls.BAJO
