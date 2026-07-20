"""
=================================================================================
competitive_intelligence — Motor de Inteligencia Competitiva FRIMARAL BI
=================================================================================

Módulo para el área comercial que detecta automáticamente oportunidades,
riesgos y ventajas competitivas usando exclusivamente los datos del MGAP.

Servicios:
    ComparadorService      — Compara cualquier par de empresas
    IndicadoresService    — 5 índices: diversificación, fidelidad, competencia,
                            riesgo, oportunidad
    RadarService          — Detecta cambios: nuevos/perdidos productores,
                            mercados, clientes
    OportunidadesService   — Ranking de oportunidades comerciales
    RiesgosService         — Detección de riesgos comerciales
    MotorCompetitivo       — Motor unificado + CLI

Uso:
    from competitive_intelligence import MotorCompetitivo

    motor = MotorCompetitivo("data/frimaral_bi.db")
    resultado = motor.analisis_completo("CALIRAL")
    oportunidades = motor.oportunidades("CALIRAL")
    comp = motor.comparar("CALIRAL", "ARBIZA")

CLI:
    python -m competitive_intelligence.motor_competitivo "CALIRAL"
    python -m competitive_intelligence.motor_competitivo "CALIRAL" --vs "ARBIZA"
    python -m competitive_intelligence.motor_competitivo --oportunidades "CALIRAL"
    python -m competitive_intelligence.motor_competitivo --radar "CALIRAL"
    python -m competitive_intelligence.motor_competitivo --riesgos "CALIRAL"
    python -m competitive_intelligence.motor_competitivo --indices "CALIRAL"
"""

from competitive_intelligence.motor_competitivo import MotorCompetitivo

__all__ = [
    "MotorCompetitivo",
    "RepositorioCIE",
    "ComparadorService",
    "IndicadoresService",
    "RadarService",
    "OportunidadesService",
    "RiesgosService",
]
__version__ = "1.0.0"
