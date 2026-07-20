"""
=================================================================================
servicio_info.py — Información General de Empresa360
=================================================================================
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
from empresa360.repositorio import Repositorio


@dataclass
class InfoGeneral:
    nombre: str
    id_empresa: int
    tipo_principal: Optional[str]
    fecha_primera: Optional[str]
    fecha_ultima: Optional[str]
    cantidad_movimientos: int
    activo: bool
    ruc: Optional[str]


class ServicioInfo:
    """Extrae información general de una empresa."""

    def __init__(self, repo: Repositorio):
        self.repo = repo

    def obtener(self, nombre_o_id: str | int) -> Optional[InfoGeneral]:
        """
        Obtiene la información general de una empresa.

        Args:
            nombre_o_id: Nombre de empresa o ID numérico.

        Returns:
            InfoGeneral o None si no se encuentra.
        """
        if isinstance(nombre_o_id, int):
            row = self.repo.empresa_por_id(nombre_o_id)
        else:
            row = self.repo.empresa_por_nombre(nombre_o_id)

        if not row:
            return None

        return InfoGeneral(
            nombre=row["nombre_unif"],
            id_empresa=row["id_empresa"],
            tipo_principal=row.get("tipo_principal"),
            fecha_primera=row.get("fecha_primera"),
            fecha_ultima=row.get("fecha_ultima"),
            cantidad_movimientos=row.get("cant_movimientos", 0),
            activo=bool(row.get("activo", 0)),
            ruc=row.get("ruc"),
        )

    def formato_tarjeta(self, info: InfoGeneral) -> str:
        """Formatea la info como tarjeta legible."""
        lines = [
            "─" * 60,
            f"  🏢  {info.nombre}",
            "─" * 60,
            f"  ID                  : {info.id_empresa}",
            f"  Tipo Principal      : {info.tipo_principal or 'N/A'}",
            f"  RUC                : {info.ruc or 'N/A'}",
            f"  Primera Aparición   : {info.fecha_primera or 'N/A'}",
            f"  Última Aparición    : {info.fecha_ultima or 'N/A'}",
            f"  Movimientos Totales : {info.cantidad_movimientos:,}",
            f"  Activo             : {'✅ Sí' if info.activo else '❌ No'}",
            "─" * 60,
        ]
        return "\n".join(lines)
