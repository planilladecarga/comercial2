"""
=================================================================================
servicio_indicadores.py — KPIs de Empresa360
=================================================================================
"""

from __future__ import annotations
from dataclasses import dataclass
from .repositorio import Repositorio


@dataclass
class Indicadores360:
    kg_totales: float = 0.0
    cantidad_movimientos: int = 0
    cantidad_productores: int = 0
    cantidad_certificadores: int = 0
    cantidad_mercados: int = 0
    cantidad_productos: int = 0
    cantidad_cortes: int = 0
    cantidad_clientes: int = 0
    cantidad_competidores: int = 0
    ranking_volumen: int = 0  # Posición en ranking general


class ServicioIndicadores:
    """Calcula todos los KPIs de una empresa."""

    def __init__(self, repo: Repositorio):
        self.repo = repo

    def calcular(self, id_empresa: int) -> Indicadores360:
        """Calcula indicadores a partir de los datos."""
        prod_rel    = self.repo.productores_relacionados(id_empresa)
        cert_rel    = self.repo.certificadores_relacionados(id_empresa)
        mercados    = self.repo.mercados_empresa(id_empresa)
        productos   = self.repo.productos_empresa(id_empresa)
        cortes      = self.repo.cortes_empresa(id_empresa)
        clientes    = self.repo.clientes_empresa(id_empresa)

        # Ranking
        ranking = self.repo.ranking_empresas(limite=1000)
        rank_pos = next(
            (i + 1 for i, r in enumerate(ranking) if r["id_empresa"] == id_empresa),
            0
        )

        return Indicadores360(
            kg_totales             = self.repo.kg_totales(id_empresa),
            cantidad_movimientos   = self.repo.cantidad_movimientos(id_empresa),
            cantidad_productores   = len(prod_rel),
            cantidad_certificadores= len(cert_rel),
            cantidad_mercados      = len(mercados),
            cantidad_productos     = len(productos),
            cantidad_cortes        = len(cortes),
            cantidad_clientes      = len(clientes),
            cantidad_competidores  = len(self.repo.competidores_por_productores(id_empresa)),
            ranking_volumen        = rank_pos,
        )

    def formato_tabla(self, ind: Indicadores360) -> str:
        """Formatea indicadores como tabla visual."""
        pct_total = ind.cantidad_movimientos * 100 / max(ind.cantidad_movimientos, 1)
        lines = [
            "  ┌──────────────────────────────┬───────────────┐",
            "  │ INDICADOR                    │ VALOR         │",
            "  ├──────────────────────────────┼───────────────┤",
            f"  │ 📦 Kg Totales                │ {ind.kg_totales:>12,.0f} │",
            f"  │ 📋 Cant. Movimientos        │ {ind.cantidad_movimientos:>12,} │",
            f"  │ 👨‍🌾 Productores Relacionados   │ {ind.cantidad_productores:>12} │",
            f"  │ 🔍 Certificadores           │ {ind.cantidad_certificadores:>12} │",
            f"  │ 🌍 Mercados                 │ {ind.cantidad_mercados:>12} │",
            f"  │ 🥩 Productos               │ {ind.cantidad_productos:>12} │",
            f"  │ 🔪 Cortes                  │ {ind.cantidad_cortes:>12} │",
            f"  │ 🏬 Clientes                │ {ind.cantidad_clientes:>12} │",
            f"  │ ⚔️ Competidores Detectados│ {ind.cantidad_competidores:>12} │",
            f"  │ 🏆 Ranking por Volumen     │ #{ind.ranking_volumen:>11,} │",
            "  └──────────────────────────────┴───────────────┘",
        ]
        return "\n".join(lines)
