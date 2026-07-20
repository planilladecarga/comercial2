"""
Modelos de respuesta (dataclasses) para el Centro de Comando Comercial.
"""
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ResumenEjecutivo:
    """Datos del módulo 1 - Resumen Ejecutivo."""
    fecha_actualizacion: str
    cantidad_movimientos: int
    kg_totales: float
    exportaciones_kg: float
    deposito_kg: float
    cantidad_empresas: int
    cantidad_productoras: int
    cantidad_certificadores: int
    cantidad_depositos: int
    cantidad_mercados: int
    cantidad_productos: int


@dataclass
class Alerta:
    """Una alerta individual del día."""
    tipo: str  # "nuevo" | "perdido" | "aumento" | "disminucion" | "cambio"
    entidad: str  # "cliente" | "productor" | "mercado"
    nombre: str
    detalle: str
    magnitud: Optional[float] = None


@dataclass
class AlertasDia:
    """Módulo 2 - Alertas del Día."""
    clientes_perdidos: list[Alerta] = field(default_factory=list)
    clientes_nuevos: list[Alerta] = field(default_factory=list)
    mercados_nuevos: list[Alerta] = field(default_factory=list)
    mercados_perdidos: list[Alerta] = field(default_factory=list)
    productores_nuevos: list[Alerta] = field(default_factory=list)
    productores_inactivos: list[Alerta] = field(default_factory=list)
    aumentos_importantes: list[Alerta] = field(default_factory=list)
    disminuciones_importantes: list[Alerta] = field(default_factory=list)
    cambios_deposito: list[Alerta] = field(default_factory=list)


@dataclass
class Oportunidad:
    """Una oportunidad de negocio."""
    tipo: str  # "potencial_caliral" | "mercado_no_participa" | "competencia" | "compartido" | "cliente_potencial"
    ranking: int
    nombre: str
    kg: float
    detalle: str


@dataclass
class Oportunidades:
    """Módulo 3 - Oportunidades."""
    top_20_productores_potenciales: list[Oportunidad] = field(default_factory=list)
    mercados_no_participa: list[Oportunidad] = field(default_factory=list)
    productores_competencia: list[Oportunidad] = field(default_factory=list)
    productores_compartidos: list[Oportunidad] = field(default_factory=list)
    clientes_potenciales: list[Oportunidad] = field(default_factory=list)


@dataclass
class ComparacionEmpresa:
    """Datos de comparación para módulo 4."""
    kg: float
    participacion_pct: float
    mercados_count: int
    clientes_count: int
    productos_count: int
    productores_count: int


@dataclass
class Competencia:
    """Módulo 4 - Comparación Competitiva."""
    empresa_a: str
    empresa_b: str
    kg_a: float
    kg_b: float
    participacion_a: float
    participacion_b: float
    comparacion: dict[str, ComparacionEmpresa]


@dataclass
class KPI:
    """Un indicador clave de rendimiento."""
    codigo: str
    nombre: str
    valor: float
    unidad: str  # "%" | "indice" | "kg"
    estado: str  # "critico" | "advertencia" | "ok"
    tendencia: str  # "up" | "down" | "stable"
    detalle: str


@dataclass
class Indicadores:
    """Módulo 5 - Indicadores KPIs."""
    indice_diversificacion: KPI
    indice_riesgo: KPI
    indice_competencia: KPI
    indice_fidelidad: KPI
    indice_crecimiento: KPI
    indice_oportunidad: KPI


@dataclass
class PaisData:
    """Datos de un país para el mapa comercial."""
    pais: str
    kg: float
    participacion_pct: float
    crecimiento_pct: float


@dataclass
class MapaComercial:
    """Módulo 6 - Mapa Comercial."""
    paises: list[PaisData]
    total_kg: float


@dataclass
class MesData:
    """Datos de un mes para evolución."""
    anio: int
    mes: int
    nombre_mes: str
    kg: float
    clientes_count: int
    mercados_count: int
    productores_count: int


@dataclass
class Evolucion:
    """Módulo 7 - Evolución."""
    meses: list[MesData]


@dataclass
class RankingItem:
    """Un item de ranking."""
    ranking: int
    nombre: str
    kg: float
    cantidad: int


@dataclass
class Rankings:
    """Módulo 8 - Top Rankings."""
    top_productores: list[RankingItem]
    top_depositos: list[RankingItem]
    top_certificadores: list[RankingItem]
    top_mercados: list[RankingItem]
    top_productos: list[RankingItem]


@dataclass
class FiltrosDisponibles:
    """Opciones disponibles para los filtros globales."""
    anos: list[int]
    meses: list[int]
    productores: list[dict]
    certificadores: list[dict]
    depositos: list[dict]
    mercados: list[str]
    productos: list[dict]
    temperaturas: list[str]
    tipos_movimiento: list[str]


@dataclass
class Comando360Response:
    """Respuesta completa del centro de comando."""
    resumen: ResumenEjecutivo
    alertas: AlertasDia
    oportunidades: Oportunidades
    competencia: Optional[Competencia]
    indicadores: Indicadores
    mapa: MapaComercial
    evolucion: Evolucion
    rankings: Rankings
    filtros: FiltrosDisponibles
