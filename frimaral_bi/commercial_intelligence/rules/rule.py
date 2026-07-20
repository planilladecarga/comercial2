"""
=================================================================================
rule.py — Modelo de Regla
=================================================================================
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional
from enum import Enum


class RuleCategory(str, Enum):
    """Categorías de reglas."""
    CAPTACION = "CAPTACION"
    RETENCION = "RETENCION"
    RECUPERACION = "RECUPERACION"
    SEGUIMIENTO = "SEGUIMIENTO"
    ANALISIS = "ANALISIS"
    ALERTA = "ALERTA"


class RuleType(str, Enum):
    """Tipos de evaluación de reglas."""
    SCORE = "SCORE"
    RIESGO = "RIESGO"
    CRECIMIENTO = "CRECIMIENTO"
    FRECUENCIA = "FRECUENCIA"
    VOLUMEN = "VOLUMEN"
    DIVERSIFICACION = "DIVERSIFICACION"
    FIDELIDAD = "FIDELIDAD"


@dataclass
class Rule:
    """Representa una regla de negocio."""
    regla_id: str
    nombre: str
    descripcion: str = ""
    prioridad: int = 50  # 1-100
    tipo_evaluacion: str = "SCORE"
    condicion: dict[str, Any] = None  # JSON condition
    recomendacion: dict[str, Any] = None  # JSON recommendation
    estado: bool = True  # Activo/Inactivo
    categoria: str = "SEGUIMIENTO"

    def __post_init__(self):
        if self.condicion is None:
            self.condicion = {}
        if self.recomendacion is None:
            self.recomendacion = {}

    def is_active(self) -> bool:
        """Verifica si la regla está activa."""
        return self.estado

    def to_dict(self) -> dict[str, Any]:
        return {
            "regla_id": self.regla_id,
            "nombre": self.nombre,
            "descripcion": self.descripcion or "",
            "prioridad": self.prioridad,
            "tipo_evaluacion": self.tipo_evaluacion,
            "condicion": self.condicion or {},
            "recomendacion": self.recomendacion or {},
            "estado": "ACTIVA" if self.estado else "INACTIVA",
            "categoria": self.categoria,
        }
