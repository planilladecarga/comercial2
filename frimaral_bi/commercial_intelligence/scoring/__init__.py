"""Scoring module - Commercial Intelligence Engine."""

from .scoring_service import ScoringService
from .models import (
    ScoreResult,
    ScoreBreakdown,
    FactorResult,
    NivelRiesgo,
    NivelPotencial,
    NivelFidelidad,
)

__all__ = [
    "ScoringService",
    "ScoreResult",
    "ScoreBreakdown",
    "FactorResult",
    "NivelRiesgo",
    "NivelPotencial",
    "NivelFidelidad",
]
