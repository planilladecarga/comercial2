"""
=================================================================================
Commercial Intelligence Engine — FRIMARAL BI Sprint 8
=================================================================================

Sistema de apoyo a la decisión comercial que analiza automáticamente los datos
de cada empresa y genera scores, riesgos, oportunidades y recomendaciones.

Módulos:
    - scoring: Motor de Score Comercial (0-100)
    - rules: Motor de reglas configurables
    - recommendations: Generador de recomendaciones
    - risk: Motor de riesgo
    - opportunity: Motor de oportunidad
    - configuration: Repositorio de configuración
    - rankings: Generador de rankings
    - indicators: Calculador de indicadores

Uso:
    from commercial_intelligence import MotorComercial
    motor = MotorComercial("data/frimaral_bi.db")
    scores = motor.calcular_scores()
    resultado = motor.analisis_completo("CALIRAL")
"""

from .motor_comercial import MotorComercial

__all__ = ["MotorComercial"]
