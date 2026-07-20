"""
Servicio de Alertas del Día - Módulo 2.
Detecta cambios significativos en el negocio.
"""
from typing import Optional
from ..database import db
from ..config import DIAS_NUEVO, DIAS_INACTIVO, UMBRAL_CRECIMIENTO_ALTO, UMBRAL_DISMINUCION_IMPORTANTE
from ..queries.comando_queries import (
    QUERY_CLIENTES_NUEVOS,
    QUERY_CLIENTES_PERDIDOS,
    QUERY_MERCADOS_NUEVOS,
    QUERY_MERCADOS_PERDIDOS,
    QUERY_PRODUCTORES_NUEVOS,
    QUERY_PRODUCTORES_INACTIVOS,
    QUERY_AUMENTOS_IMPORTANTES,
    QUERY_DISMINUCIONES_IMPORTANTES,
    QUERY_CAMBIO_DEPOSITO,
    QUERY_EMPRESA_CALIRAL,
)


class Alerta:
    def __init__(self, tipo: str, entidad: str, nombre: str, detalle: str, magnitud: Optional[float] = None):
        self.tipo = tipo
        self.entidad = entidad
        self.nombre = nombre
        self.detalle = detalle
        self.magnitud = magnitud

    def to_dict(self) -> dict:
        return {
            "tipo": self.tipo,
            "entidad": self.entidad,
            "nombre": self.nombre,
            "detalle": self.detalle,
            "magnitud": self.magnitud,
        }


class AlertasService:
    """Detecta alertas del día para el Director Comercial."""

    def obtener_alertas(self, id_empresa: int) -> dict:
        """Retorna todas las alertas del día."""
        return {
            "clientes_perdidos": self._clientes_perdidos(id_empresa),
            "clientes_nuevos": self._clientes_nuevos(id_empresa),
            "mercados_nuevos": self._mercados_nuevos(id_empresa),
            "mercados_perdidos": self._mercados_perdidos(id_empresa),
            "productores_nuevos": self._productores_nuevos(id_empresa),
            "productores_inactivos": self._productores_inactivos(id_empresa),
            "aumentos_importantes": self._aumentos_importantes(id_empresa),
            "disminuciones_importantes": self._disminuciones_importantes(id_empresa),
            "cambios_deposito": self._cambios_deposito(id_empresa),
        }

    def _clientes_perdidos(self, id_empresa: int) -> list[dict]:
        rows = db.execute(QUERY_CLIENTES_PERDIDOS, (id_empresa, DIAS_INACTIVO))
        return [
            Alerta(
                tipo="perdido",
                entidad="cliente",
                nombre=r["nombre"],
                detalle=f"Último movimiento: {r['ultima_fecha']} — {r['kg_total']:,.0f} kg históricos",
                magnitud=r["kg_total"],
            ).to_dict()
            for r in rows[:10]
        ]

    def _clientes_nuevos(self, id_empresa: int) -> list[dict]:
        rows = db.execute(QUERY_CLIENTES_NUEVOS, (id_empresa, DIAS_NUEVO))
        return [
            Alerta(
                tipo="nuevo",
                entidad="cliente",
                nombre=r["nombre"],
                detalle=f"Desde {r['primera_fecha']} — {r['kg_total']:,.0f} kg",
                magnitud=r["kg_total"],
            ).to_dict()
            for r in rows[:10]
        ]

    def _mercados_nuevos(self, id_empresa: int) -> list[dict]:
        rows = db.execute(QUERY_MERCADOS_NUEVOS, (id_empresa, DIAS_NUEVO))
        return [
            Alerta(
                tipo="nuevo",
                entidad="mercado",
                nombre=r["mercado"],
                detalle=f"Desde {r['primera_fecha']} — {r['kg_total']:,.0f} kg",
                magnitud=r["kg_total"],
            ).to_dict()
            for r in rows[:10]
        ]

    def _mercados_perdidos(self, id_empresa: int) -> list[dict]:
        rows = db.execute(QUERY_MERCADOS_PERDIDOS, (id_empresa, DIAS_INACTIVO))
        return [
            Alerta(
                tipo="perdido",
                entidad="mercado",
                nombre=r["mercado"],
                detalle=f"Último movimiento: {r['ultima_fecha']} — {r['kg_total']:,.0f} kg históricos",
                magnitud=r["kg_total"],
            ).to_dict()
            for r in rows[:10]
        ]

    def _productores_nuevos(self, id_empresa: int) -> list[dict]:
        rows = db.execute(QUERY_PRODUCTORES_NUEVOS, (id_empresa, DIAS_NUEVO))
        return [
            Alerta(
                tipo="nuevo",
                entidad="productor",
                nombre=r["nombre_productor"],
                detalle=f"Desde {r['primera_fecha']} — {r['kg_total']:,.0f} kg",
                magnitud=r["kg_total"],
            ).to_dict()
            for r in rows[:10]
        ]

    def _productores_inactivos(self, id_empresa: int) -> list[dict]:
        rows = db.execute(QUERY_PRODUCTORES_INACTIVOS, (id_empresa, DIAS_INACTIVO))
        return [
            Alerta(
                tipo="inactivo",
                entidad="productor",
                nombre=r["nombre_productor"],
                detalle=f"Inactivo desde {r['ultima_fecha']} — {r['kg_total']:,.0f} kg históricos",
                magnitud=r["kg_total"],
            ).to_dict()
            for r in rows[:10]
        ]

    def _aumentos_importantes(self, id_empresa: int) -> list[dict]:
        rows = db.execute(QUERY_AUMENTOS_IMPORTANTES, (id_empresa, id_empresa, id_empresa, id_empresa, id_empresa, id_empresa, UMBRAL_CRECIMIENTO_ALTO))
        return [
            Alerta(
                tipo="aumento",
                entidad="mercado",
                nombre=r["entidad"],
                detalle=f"+{r['variacion_pct']:.1f}% vs mes anterior",
                magnitud=r["variacion_pct"],
            ).to_dict()
            for r in rows[:10]
        ]

    def _disminuciones_importantes(self, id_empresa: int) -> list[dict]:
        rows = db.execute(QUERY_DISMINUCIONES_IMPORTANTES, (id_empresa, id_empresa, id_empresa, id_empresa, id_empresa, id_empresa, UMBRAL_DISMINUCION_IMPORTANTE))
        return [
            Alerta(
                tipo="disminucion",
                entidad="mercado",
                nombre=r["entidad"],
                detalle=f"{r['variacion_pct']:.1f}% vs mes anterior",
                magnitud=r["variacion_pct"],
            ).to_dict()
            for r in rows[:10]
        ]

    def _cambios_deposito(self, id_empresa: int) -> list[dict]:
        rows = db.execute(QUERY_CAMBIO_DEPOSITO, (id_empresa, id_empresa, id_empresa))
        return [
            Alerta(
                tipo="cambio",
                entidad="deposito",
                nombre=r["nombre_productor"],
                detalle=f"Nuevo depósito: {r['deposito_actual']}",
                magnitud=None,
            ).to_dict()
            for r in rows[:10]
        ]


alertas_service = AlertasService()
