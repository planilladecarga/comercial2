"""
=================================================================================
empresa360 — Motor de Inteligencia Comercial FRIMARAL BI
=================================================================================

Arquitectura modular para generar fichas inteligentes 360° de cualquier
empresa del ecosistema MGAP Uruguay.

Módulos:
    repositorio      — Consultas SQL centralizadas y reutilizables
    servicio_info    — Información general de la empresa
    servicio_roles   — Detección automática de roles
    servicio_indicadores — Indicadores clave de rendimiento
    servicio_relaciones — Productores, Certificadores, Depósitos relacionados
    servicio_evolucion  — Evolución mensual de volúmenes
    servicio_competidores — Detección de competidores y similitud
    servicio_alertas     — Sistema de alertas inteligentes
    servicio_movimientos — Detalle completo de movimientos
    vista360         — Motor unificado que orquesta todos los servicios

Uso:
    from empresa360.vista360 import Vista360

    motor = Vista360(db_path="data/frimaral_bi.db")
    ficha = motor.generar_ficha("CALIRAL")
    print(ficha)

    # CLI
    python -m empresa360.vista360 "CALIRAL"
"""

from empresa360.vista360 import Vista360

__all__ = [
    "Vista360",
    "Repositorio",
    "ServicioInfo",
    "ServicioRoles",
    "ServicioIndicadores",
    "ServicioRelaciones",
    "ServicioEvolucion",
    "ServicioCompetidores",
    "ServicioAlertas",
    "ServicioMovimientos",
]
__version__ = "1.0.0"
