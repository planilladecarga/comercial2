"""
=================================================================================
servicio_competidores.py — Detección de competidores e índice de similitud
=================================================================================
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
from .repositorio import Repositorio


@dataclass
class CompetidorDetectado:
    id_empresa: int
    nombre: str
    productores_compartidos: int = 0
    mercados_compartidos: int = 0
    productos_compartidos: int = 0
    indice_similitud: float = 0.0
    razon_principal: str = ""


@dataclass
class Competidores360:
    por_productores: list[CompetidorDetectado] = field(default_factory=list)
    por_mercados: list[CompetidorDetectado] = field(default_factory=list)
    por_productos: list[CompetidorDetectado] = field(default_factory=list)
    top_competidores: list[CompetidorDetectado] = field(default_factory=list)


class ServicioCompetidores:
    """
    Detecta competidores automáticamente comparando:
        1. Productores compartidos
        2. Mercados compartidos
        3. Productos compartidos

    Calcula un índice de similitud 0–100 para cada competidor.
    """

    # Pesos para el índice de similitud
    PESO_PRODUCTORES = 0.50
    PESO_MERCADOS    = 0.30
    PESO_PRODUCTOS   = 0.20

    # Máximos para normalización (evitar que un competidor monopolice la métrica)
    MAX_PRODUCTORES_COMUNES = 10
    MAX_MERCADOS_COMUNES    = 10
    MAX_PRODUCTOS_COMUNES   = 10

    def __init__(self, repo: Repositorio):
        self.repo = repo

    def detectar(self, id_empresa: int) -> Competidores360:
        """Detecta todos los competidores y calcula similitud."""
        por_prod = self.repo.competidores_por_productores(id_empresa)
        por_merc = self.repo.competidores_por_mercados(id_empresa)
        por_prod2= self.repo.competidores_por_productos(id_empresa)

        # Propias dimensiones para normalizar
        my_prods = len(self.repo.productores_relacionados(id_empresa)) or 1
        my_mercs = len(self.repo.mercados_empresa(id_empresa)) or 1
        my_prods2= len(self.repo.productos_empresa(id_empresa)) or 1

        # Todos los competidores únicos
        all_ids: dict[int, dict] = {}
        for row in por_prod:
            eid = row["id_empresa"]
            if eid not in all_ids:
                all_ids[eid] = {"nombre": row["nombre_unif"], "id": eid,
                                 "productores_compartidos": 0,
                                 "mercados_compartidos": 0,
                                 "productos_compartidos": 0}
            all_ids[eid]["productores_compartidos"] = row["productores_compartidos"]

        for row in por_merc:
            eid = row["id_empresa"]
            if eid not in all_ids:
                all_ids[eid] = {"nombre": row["nombre_unif"], "id": eid,
                                 "productores_compartidos": 0,
                                 "mercados_compartidos": 0,
                                 "productos_compartidos": 0}
            all_ids[eid]["mercados_compartidos"] = row["mercados_compartidos"]

        for row in por_prod2:
            eid = row["id_empresa"]
            if eid not in all_ids:
                all_ids[eid] = {"nombre": row["nombre_unif"], "id": eid,
                                 "productores_compartidos": 0,
                                 "mercados_compartidos": 0,
                                 "productos_compartidos": 0}
            all_ids[eid]["productos_compartidos"] = row["productos_compartidos"]

        # Calcular índice de similitud
        competidores: list[CompetidorDetectado] = []
        for eid, data in all_ids.items():
            sim = self._indice_similitud(
                data["productores_compartidos"],
                data["mercados_compartidos"],
                data["productos_compartidos"],
                my_prods, my_mercs, my_prods2
            )
            razon = self._razon_principal(data)
            competidores.append(CompetidorDetectado(
                id_empresa              = eid,
                nombre                  = data["nombre"],
                productores_compartidos  = data["productores_compartidos"],
                mercados_compartidos     = data["mercados_compartidos"],
                productos_compartidos   = data["productos_compartidos"],
                indice_similitud        = sim,
                razon_principal         = razon,
            ))

        # Ordenar por similitud
        competidores.sort(key=lambda x: x.indice_similitud, reverse=True)

        # Top 10 por cada dimensión
        def top_k(lst: list, k=5):
            return sorted(lst, key=lambda x: x.indice_similitud, reverse=True)[:k]

        return Competidores360(
            por_productores  = top_k([c for c in competidores if c.productores_compartidos > 0], 5),
            por_mercados     = top_k([c for c in competidores if c.mercados_compartidos > 0], 5),
            por_productos   = top_k([c for c in competidores if c.productos_compartidos > 0], 5),
            top_competidores= competidores[:10],
        )

    def _indice_similitud(
        self, prod_c: int, merc_c: int, prod2_c: int,
        my_prod: int, my_merc: int, my_prod2: int,
    ) -> float:
        """Calcula índice de similitud 0–100."""
        sim_p = min(prod_c / self.MAX_PRODUCTORES_COMUNES, 1.0)
        sim_m = min(merc_c / self.MAX_MERCADOS_COMUNES, 1.0)
        sim_r = min(prod2_c / self.MAX_PRODUCTOS_COMUNES, 1.0)
        return round(
            (sim_p * self.PESO_PRODUCTORES +
             sim_m * self.PESO_MERCADOS +
             sim_r * self.PESO_PRODUCTOS) * 100, 1
        )

    def _razon_principal(self, data: dict) -> str:
        """Determina la principal razón de competencia."""
        if data["productores_compartidos"] > 0:
            return f"Comparte {data['productores_compartidos']} productores"
        if data["mercados_compartidos"] > 0:
            return f"Competencia en {data['mercados_compartidos']} mercados"
        if data["productos_compartidos"] > 0:
            return f"Productos compartidos: {data['productos_compartidos']}"
        return "Competencia indirecta"

    def formato_tabla(self, comp: Competidores360, top: int = 10) -> str:
        """Formatea competidores como tabla."""
        if not comp.top_competidores:
            return "  ℹ️  Sin competidores detectados"
        lines = [
            "  ┌──────────────────────────────────┬──────────┬──────────┬──────────┬──────────┐",
            "  │ COMPETIDOR                      │ SIMIL. % │ PROD.COM │ MERC.COM │ PROD.COM │",
            "  ├──────────────────────────────────┼──────────┼──────────┼──────────┼──────────┤",
        ]
        for c in comp.top_competidores[:top]:
            barra = "█" * int(c.indice_similitud / 10)
            lines.append(
                f"  │ {c.nombre[:33]:<33} │  {barra:<5}{c.indice_similitud:>5.1f}% "
                f"│ {c.productores_compartidos:>8} │ {c.mercados_compartidos:>8} │ "
                f"{c.productos_compartidos:>8} │"
            )
        lines.append("  └──────────────────────────────────┴──────────┴──────────┴──────────┴──────────┘")
        return "\n".join(lines)
