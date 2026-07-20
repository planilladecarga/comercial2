"""
BusinessQueryDTO - Data Transfer Objects
"""
from dataclasses import dataclass, field
from typing import Optional, Any
from datetime import datetime


@dataclass
class QueryParametro:
    """Un parámetro de consulta."""
    nombre: str
    tipo: str  # "int" | "float" | "str" | "date" | "bool" | "select"
    label: str
    requerido: bool = False
    default: Any = None
    opciones: list[dict] = field(default_factory=list)  # [{"value": ..., "label": ...}]
    descripcion: str = ""


@dataclass
class QueryDefinicion:
    """Definición completa de una consulta."""
    id: str
    nombre: str
    descripcion: str
    categoria: str  # "exportacion" | "productor" | "mercado" | "ranking" | "deposito" | "certificador" | "empresa"
    sql: str
    parametros: list[QueryParametro] = field(default_factory=list)
    reglas_negocio: list[str] = field(default_factory=list)
    ejemplo_respuesta: dict = field(default_factory=dict)


@dataclass
class QueryResultado:
    """Resultado de una consulta ejecutada."""
    consulta_id: str
    consulta_nombre: str
    parametros_usados: dict
    ejecutado_en: datetime
    tiempo_ms: float
    total_registros: int
    resumen: dict  # {kg_total, kg_promedio, etc}
    kpis: list[dict]  # [{nombre, valor, unidad}]
    reglas_aplicadas: list[str]
    datos: list[dict]
    columnas: list[str]
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "consulta_id": self.consulta_id,
            "consulta_nombre": self.consulta_nombre,
            "parametros_usados": self.parametros_usados,
            "ejecutado_en": self.ejecutado_en.isoformat(),
            "tiempo_ms": round(self.tiempo_ms, 2),
            "total_registros": self.total_registros,
            "resumen": self.resumen,
            "kpis": self.kpis,
            "reglas_aplicadas": self.reglas_aplicadas,
            "datos": self.datos,
            "columnas": self.columnas,
            "metadata": self.metadata,
        }


@dataclass
class HistorialEntry:
    """Entrada del historial de consultas."""
    id: int
    consulta_id: str
    consulta_nombre: str
    parametros: dict
    usuario: str
    timestamp: datetime
    tiempo_ms: float
    total_registros: int

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "consulta_id": self.consulta_id,
            "consulta_nombre": self.consulta_nombre,
            "parametros": self.parametros,
            "usuario": self.usuario,
            "timestamp": self.timestamp.isoformat(),
            "tiempo_ms": round(self.tiempo_ms, 2),
            "total_registros": self.total_registros,
        }


@dataclass
class FavoritoEntry:
    """Consulta favorita."""
    id: int
    consulta_id: str
    consulta_nombre: str
    parametros_default: dict
    nombre_custom: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "consulta_id": self.consulta_id,
            "consulta_nombre": self.consulta_nombre,
            "parametros_default": self.parametros_default,
            "nombre_custom": self.nombre_custom,
        }
