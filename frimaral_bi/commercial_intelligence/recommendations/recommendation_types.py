"""
=================================================================================
recommendation_types.py — Tipos de Recomendación
=================================================================================
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from enum import Enum


class RecommendationStatus(str, Enum):
    """Estados de una recomendación."""
    PENDIENTE = "PENDIENTE"
    EN_PROGRESO = "EN_PROGRESO"
    COMPLETADA = "COMPLETADA"
    DESCARTADA = "DESCARTADA"


class RecommendationCategory(str, Enum):
    """Categorías de recomendación."""
    CAPTACION = "CAPTACION"
    RETENCION = "RETENCION"
    RECUPERACION = "RECUPERACION"
    SEGUIMIENTO = "SEGUIMIENTO"
    ANALISIS = "ANALISIS"
    ALERTA = "ALERTA"


@dataclass
class Recommendation:
    """Representa una recomendación generada."""
    id: int = 0
    regla_id: str = ""
    recomendacion: str = ""
    prioridad: int = 50
    categoria: str = "SEGUIMIENTO"
    estado: str = "PENDIENTE"
    fecha_generacion: str = ""
    detalle: str = ""

    def __post_init__(self):
        if not self.fecha_generacion:
            from datetime import datetime
            self.fecha_generacion = datetime.now().isoformat()

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "regla_id": self.regla_id,
            "recomendacion": self.recomendacion,
            "prioridad": self.prioridad,
            "categoria": self.categoria,
            "estado": self.estado,
            "fecha_generacion": self.fecha_generacion,
            "detalle": self.detalle,
        }
