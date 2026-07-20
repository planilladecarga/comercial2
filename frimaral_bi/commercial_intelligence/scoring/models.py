"""
=================================================================================
models.py — Modelos de datos para el Scoring
=================================================================================
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional
from datetime import datetime
from enum import Enum


class NivelRiesgo(str, Enum):
    """Niveles de riesgo comercial."""
    BAJO = "BAJO"
    MEDIO = "MEDIO"
    ALTO = "ALTO"
    CRITICO = "CRITICO"


class NivelPotencial(str, Enum):
    """Niveles de potencial comercial."""
    MUY_ALTO = "MUY_ALTO"
    ALTO = "ALTO"
    MEDIO = "MEDIO"
    BAJO = "BAJO"


class NivelFidelidad(str, Enum):
    """Niveles de fidelidad."""
    MUY_ALTA = "MUY_ALTA"
    ALTA = "ALTA"
    MEDIA = "MEDIA"
    BAJA = "BAJA"
    MUY_BAJA = "MUY_BAJA"


class NivelDependencia(str, Enum):
    """Niveles de dependencia."""
    ALTA = "ALTA"
    MEDIA = "MEDIA"
    BAJA = "BAJA"


# ─────────────────────────────────────────────────────────────────────────────
# FACTOR RESULT
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class FactorResult:
    """Resultado individual de un factor."""
    factor_key: str
    factor_nombre: str
    valor: float = 0.0           # 0-100
    peso: float = 0.0           # Peso configurado
    contribucion: float = 0.0   # valor × peso / total
    comparacion_periodo: str = ""  # 'vs_mes_anterior', 'vs_promedio_sector'
    detalle: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "factor_key": self.factor_key,
            "factor_nombre": self.factor_nombre,
            "valor": round(self.valor, 2),
            "peso": round(self.peso, 2),
            "contribucion": round(self.contribucion, 2),
            "comparacion_periodo": self.comparacion_periodo,
            "detalle": self.detalle,
        }


# ─────────────────────────────────────────────────────────────────────────────
# SCORE BREAKDOWN
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class ScoreBreakdown:
    """Desglose completo del score."""
    score_total: float = 0.0
    nivel: str = ""
    factores: list[FactorResult] = field(default_factory=list)
    fecha_calculo: str = ""
    periodo_evaluado: str = ""
    metrics_raw: dict[str, Any] = field(default_factory=dict)  # Métricas originales

    def to_dict(self) -> dict[str, Any]:
        return {
            "score_total": round(self.score_total, 2),
            "nivel": self.nivel,
            "factores": [f.to_dict() for f in self.factores],
            "fecha_calculo": self.fecha_calculo,
            "periodo_evaluado": self.periodo_evaluado,
        }


# ─────────────────────────────────────────────────────────────────────────────
# SCORE RESULT
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class ScoreResult:
    """Resultado completo del scoring de una empresa."""
    id_empresa: int
    nombre_empresa: str
    tipo_empresa: str = ""
    score_total: float = 0.0
    breakdown: Optional[ScoreBreakdown] = None
    nivel_riesgo: str = ""
    nivel_potencial: str = ""
    nivel_fidelidad: str = ""
    nivel_dependencia: str = ""

    def to_dict(self) -> dict[str, Any]:
        result = {
            "id_empresa": self.id_empresa,
            "nombre_empresa": self.nombre_empresa,
            "tipo_empresa": self.tipo_empresa,
            "score_total": round(self.score_total, 2),
            "nivel_riesgo": self.nivel_riesgo,
            "nivel_potencial": self.nivel_potencial,
            "nivel_fidelidad": self.nivel_fidelidad,
            "nivel_dependencia": self.nivel_dependencia,
        }
        if self.breakdown:
            result["breakdown"] = self.breakdown.to_dict()
        return result


# ─────────────────────────────────────────────────────────────────────────────
# INDICATOR RESULT
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class IndicatorResult:
    """Resultado de un indicador individual."""
    indicator_key: str
    indicator_nombre: str
    valor: float = 0.0
    unidad: str = ""
    estado: str = "NORMAL"  # NORMAL, ALERTA, CRITICO
    tendencia: str = "STABLE"  # UP, DOWN, STABLE
    detalle: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "indicator_key": self.indicator_key,
            "indicator_nombre": self.indicator_nombre,
            "valor": round(self.valor, 2),
            "unidad": self.unidad,
            "estado": self.estado,
            "tendencia": self.tendencia,
            "detalle": self.detalle,
        }
