"""
=================================================================================
servicio_relaciones.py — Productores, Certificadores y Depósitos relacionados
=================================================================================
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
from .repositorio import Repositorio


@dataclass
class ProductorRelacionado:
    nro_productor: str
    nombre: str
    kg: float
    porcentaje: float
    movimientos: int
    primera_fecha: Optional[str]
    ultima_fecha: Optional[str]


@dataclass
class CertificadorRelacionado:
    nro_certificado: str
    nombre: str
    kg: float
    movimientos: int
    primera_fecha: Optional[str]
    ultima_fecha: Optional[str]


@dataclass
class DepositoUtilizado:
    nombre: str
    departamento: Optional[str]
    kg: float
    porcentaje: float
    movimientos: int


@dataclass
class Relaciones360:
    productores: list[ProductorRelacionado] = field(default_factory=list)
    certificadores: list[CertificadorRelacionado] = field(default_factory=list)
    depositos: list[DepositoUtilizado] = field(default_factory=list)
    kg_total_empresa: float = 0.0


class ServicioRelaciones:
    """
    Extrae todas las relaciones comerciales de una empresa:
    productores, certificadores y depósitos.
    """

    def __init__(self, repo: Repositorio):
        self.repo = repo

    def obtener(self, id_empresa: int) -> Relaciones360:
        """Obtiene todas las relaciones de una empresa."""
        kg_total = self.repo.kg_totales(id_empresa)

        prod_rows = self.repo.productores_relacionados(id_empresa)
        productores = [
            ProductorRelacionado(
                nro_productor  = r["nro_productor"],
                nombre         = r["nombre_productor"],
                kg             = r["kg_total"] or 0.0,
                porcentaje     = round((r["kg_total"] or 0) * 100 / max(kg_total, 1), 2),
                movimientos    = r["cantidad_movimientos"],
                primera_fecha  = r["primera_fecha"],
                ultima_fecha   = r["ultima_fecha"],
            )
            for r in prod_rows
        ]

        cert_rows = self.repo.certificadores_relacionados(id_empresa)
        certificadores = [
            CertificadorRelacionado(
                nro_certificado = r["nro_certificado"],
                nombre          = r["certificador"],
                kg              = r["kg_total"] or 0.0,
                movimientos     = r["cantidad_movimientos"],
                primera_fecha   = r["primera_fecha"],
                ultima_fecha    = r["ultima_fecha"],
            )
            for r in cert_rows
        ]

        dep_rows = self.repo.depositos_utilizados(id_empresa)
        depositos = [
            DepositoUtilizado(
                nombre        = r["deposito"],
                departamento = r["departamento"],
                kg           = r["kg_total"] or 0.0,
                porcentaje   = r["porcentaje"] or 0.0,
                movimientos  = r["cantidad_movimientos"],
            )
            for r in dep_rows
        ]

        return Relaciones360(
            productores       = productores,
            certificadores   = certificadores,
            depositos        = depositos,
            kg_total_empresa = kg_total,
        )

    def productores_principales(
        self, relaciones: Relaciones360, top: int = 10
    ) -> list[ProductorRelacionado]:
        """Retorna los top N productores por kg."""
        return sorted(relaciones.productores, key=lambda x: x.kg, reverse=True)[:top]

    def formato_productores(self, rel: Relaciones360, top: int = 10) -> str:
        """Formatea productores como tabla."""
        principales = self.productores_principales(rel, top)
        if not principales:
            return "  ℹ️  Sin productores registrados"
        lines = [
            "  ┌──────────────────────────────────┬────────────┬──────────┬────────────┐",
            "  │ PRODUCTOR                        │        KG  │       %  │ MOVIMIENTOS│",
            "  ├──────────────────────────────────┼────────────┼──────────┼────────────┤",
        ]
        for p in principales:
            lines.append(
                f"  │ {p.nombre[:33]:<33} │ {p.kg:>10,.0f} │ {p.porcentaje:>7.1f}% │ {p.movimientos:>10,} │"
            )
        lines.append("  └──────────────────────────────────┴────────────┴──────────┴────────────┘")
        return "\n".join(lines)

    def formato_depositos(self, rel: Relaciones360) -> str:
        """Formatea depósitos como tabla."""
        if not rel.depositos:
            return "  ℹ️  Sin depósitos registrados"
        lines = [
            "  ┌──────────────────────────────────┬────────────┬──────────┬────────────┐",
            "  │ DEPÓSITO                         │        KG  │       %  │ MOVIMIENTOS│",
            "  ├──────────────────────────────────┼────────────┼──────────┼────────────┤",
        ]
        for d in rel.depositos:
            lines.append(
                f"  │ {d.nombre[:33]:<33} │ {d.kg:>10,.0f} │ {d.porcentaje:>7.1f}% │ {d.movimientos:>10,} │"
            )
        lines.append("  └──────────────────────────────────┴────────────┴──────────┴────────────┘")
        return "\n".join(lines)
