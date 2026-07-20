"""
=================================================================================
servicio_roles.py — Detección automática de roles de empresa
=================================================================================
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
from empresa360.repositorio import Repositorio


@dataclass
class RolesEmpresa:
    es_productor: bool = False
    es_certificador: bool = False
    es_deposito: bool = False
    es_puerto: bool = False
    es_cliente: bool = False
    es_competidor: bool = False
    # Roles derivados del análisis
    roles_detectados: list[str] = field(default_factory=list)

    @property
    def todos_los_roles(self) -> list[str]:
        return self.roles_detectados


class ServicioRoles:
    """
    Detecta automáticamente todos los roles de una empresa
    basándose en su comportamiento real en los datos.
    """

    # Umbrales de decisión (pueden ajustarse)
    UMBRAL_PRODUCTOR_KG    = 0      # Si mueve kg como operador principal
    UMBRAL_CERTIF_MOVS     = 3      # Mínima cantidad de movs como certificador
    UMBRAL_CLIENTE_KG      = 1_000   # Mínimos kg como destino
    UMBRAL_COMPETIDOR_KG   = 10_000  # Mínimos kg para ser competidor real

    def __init__(self, repo: Repositorio):
        self.repo = repo

    def detectar(self, id_empresa: int) -> RolesEmpresa:
        """
        Detecta todos los roles activos de una empresa.

        Un rol se activa cuando los datos lo justifican,
        no por configuración manual.
        """
        empresa = self.repo.empresa_por_id(id_empresa)
        if not empresa:
            return RolesEmpresa()

        r = RolesEmpresa(
            es_productor     =bool(empresa.get("es_productor", 0)),
            es_certificador  =bool(empresa.get("es_certificador", 0)),
            es_deposito      =bool(empresa.get("es_deposito", 0)),
            es_puerto        =bool(empresa.get("es_puerto", 0)),
            es_competidor    =bool(empresa.get("es_competidor", 0)),
        )

        # Análisis automático derivado
        if r.es_productor or r.es_deposito:
            r.roles_detectados.append("🏭 Operador Logístico")

        if r.es_certificador:
            r.roles_detectados.append("🔍 Certificador")

        if r.es_puerto:
            r.roles_detectados.append("🚢 Puerto")

        # Rol cliente: empresas que reciben volúmenes significativos como destino
        kg_total = self.repo.kg_totales(id_empresa)
        if kg_total >= self.UMBRAL_CLIENTE_KG:
            r.es_cliente = True
            r.roles_detectados.append("🏬 Cliente")

        # Detectamos si es competidor por volumen
        if kg_total >= self.UMBRAL_COMPETIDOR_KG:
            r.roles_detectados.append("⚔️ Competidor")

        if not r.roles_detectados:
            r.roles_detectados.append("📋 Registro en Sistema")

        return r

    def detectar_multi(self, id_empresa: int) -> list[str]:
        """Retorna solo la lista de roles detectados."""
        roles = self.detectar(id_empresa)
        return roles.todos_los_roles

    def formato_roles(self, roles: RolesEmpresa) -> str:
        """Formatea los roles como bloque visual."""
        if not roles.todos_los_roles:
            return "  ℹ️  Sin roles definidos"
        return "  " + "  |  ".join(roles.todos_los_roles)
