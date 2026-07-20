"""
=================================================================================
comparador_service.py — Comparador Genérico Entre Empresas
=================================================================================
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
from ..empresa360.repositorio import Repositorio
from competitive_intelligence.repositorio import RepositorioCIE


@dataclass
class ProductorCompartido:
    nro_productor   : str
    nombre          : str
    kg_a            : float
    kg_b            : float
    kg_total        : float
    pct_a           : float
    pct_b           : float


@dataclass
class MercadoCompartido:
    mercado         : str
    kg_a            : float
    kg_b            : float
    pct_a           : float
    pct_b           : float


@dataclass
class ClienteCompartido:
    cliente         : str
    kg_a            : float
    kg_b            : float
    pct_a           : float
    pct_b           : float


@dataclass
class ProductoCompartido:
    producto        : str
    kg_a            : float
    kg_b            : float
    pct_a           : float
    pct_b           : float


@dataclass
class ResultadoComparacion:
    """
    Resultado de comparar empresa A vs empresa B.
    Totalmente genérico — sin lógica específica de ninguna empresa.
    """
    nombre_a    : str
    nombre_b    : str
    id_a        : int
    id_b        : int

    # Totales
    kg_a        : float = 0.0
    kg_b        : float = 0.0

    # Productores
    productores_compartidos : list[ProductorCompartido] = field(default_factory=list)
    productores_exclusivos_a: list = field(default_factory=list)
    productores_exclusivos_b: list = field(default_factory=list)
    cant_prod_compartidos   : int = 0
    kg_prod_compartidos     : float = 0.0

    # Mercados
    mercados_compartidos    : list[MercadoCompartido] = field(default_factory=list)
    mercados_exclusivos_a  : list = field(default_factory=list)
    mercados_exclusivos_b  : list = field(default_factory=list)
    cant_merc_compartidos  : int = 0

    # Clientes
    clientes_compartidos    : list[ClienteCompartido] = field(default_factory=list)
    cant_cli_compartidos    : int = 0

    # Productos
    productos_compartidos   : list[ProductoCompartido] = field(default_factory=list)

    # % de paso
    pct_b_pasa_por_a        : float = 0.0
    kg_b_sin_a              : float = 0.0


class ComparadorService:
    """
    Compara dos empresas genéricamente.
    Sin hardcodeo de nombres — funciona con cualquier par de empresas.

    Uso:
        comp = ComparadorService(repo_cie, repo_emp360)
        resultado = comp.comparar("CALIRAL", "ARBIZA")
        print(resultado.nombre_a, "vs", resultado.nombre_b)
        print(f"% de ARBIZA que pasa por CALIRAL: {resultado.pct_b_pasa_por_a}%")
    """

    def __init__(self, repo_cie: RepositorioCIE, repo_emp360: Repositorio):
        self.repo_cie = repo_cie
        self.repo_emp = repo_emp360

    def comparar(
        self, nombre_a: str, nombre_b: str
    ) -> Optional[ResultadoComparacion]:
        """
        Compara empresa A vs empresa B.

        Args:
            nombre_a: Nombre de la empresa A
            nombre_b: Nombre de la empresa B

        Returns:
            ResultadoComparacion o None si alguna empresa no existe.
        """
        # Buscar empresas
        emp_a = self.repo_emp.empresa_por_nombre(nombre_a)
        emp_b = self.repo_emp.empresa_por_nombre(nombre_b)

        if not emp_a:
            return None
        if not emp_b:
            return None

        id_a = emp_a["id_empresa"]
        id_b = emp_b["id_empresa"]
        nom_a = emp_a["nombre_unif"]
        nom_b = emp_b["nombre_unif"]

        kg_a = self.repo_cie.kg_total_empresa(id_a)
        kg_b = self.repo_cie.kg_total_empresa(id_b)

        # ── Productores ────────────────────────────────────────────────
        shared_prod = self.repo_cie.productores_compartidos(id_a, id_b)
        excl_a = self.repo_cie.productores_exclusivos_a(id_a, id_b)
        excl_b = self.repo_cie.productores_exclusivos_a(id_b, id_a)

        productores_compartidos = []
        for r in shared_prod:
            kg_total = (r["kg_a"] or 0) + (r["kg_b"] or 0)
            productores_compartidos.append(ProductorCompartido(
                nro_productor = r["nro_productor"],
                nombre        = r["nombre_productor"],
                kg_a          = r["kg_a"] or 0,
                kg_b          = r["kg_b"] or 0,
                kg_total      = kg_total,
                pct_a         = round((r["kg_a"] or 0) / max(kg_a, 1) * 100, 2),
                pct_b         = round((r["kg_b"] or 0) / max(kg_b, 1) * 100, 2),
            ))

        # ── Mercados ───────────────────────────────────────────────────
        shared_merc = self.repo_cie.mercados_compartidos(id_a, id_b)
        excl_merc_a = self.repo_cie.mercados_exclusivos_a(id_a, id_b)
        excl_merc_b = self.repo_cie.mercados_exclusivos_a(id_b, id_a)

        mercados_compartidos = []
        for r in shared_merc:
            mercados_compartidos.append(MercadoCompartido(
                mercado = r["mercado"],
                kg_a    = r["kg_a"] or 0,
                kg_b    = r["kg_b"] or 0,
                pct_a   = round((r["kg_a"] or 0) / max(kg_a, 1) * 100, 2),
                pct_b   = round((r["kg_b"] or 0) / max(kg_b, 1) * 100, 2),
            ))

        # ── Clientes ───────────────────────────────────────────────────
        shared_cli = self.repo_cie.clientes_compartidos(id_a, id_b)

        clientes_compartidos = []
        for r in shared_cli:
            clientes_compartidos.append(ClienteCompartido(
                cliente = r["cliente"],
                kg_a    = r["kg_a"] or 0,
                kg_b    = r["kg_b"] or 0,
                pct_a   = round((r["kg_a"] or 0) / max(kg_a, 1) * 100, 2),
                pct_b   = round((r["kg_b"] or 0) / max(kg_b, 1) * 100, 2),
            ))

        # ── Productos ──────────────────────────────────────────────────
        shared_prod2 = self.repo_cie.productos_compartidos(id_a, id_b)
        productos_compartidos = [
            ProductoCompartido(
                producto = r["producto"],
                kg_a     = r["kg_a"] or 0,
                kg_b     = r["kg_b"] or 0,
                pct_a    = round((r["kg_a"] or 0) / max(kg_a, 1) * 100, 2),
                pct_b    = round((r["kg_b"] or 0) / max(kg_b, 1) * 100, 2),
            )
            for r in shared_prod2
        ]

        # ── % de paso ──────────────────────────────────────────────────
        pct_b_pasa_por_a = self.repo_cie.porcentaje_paso_por(id_a, id_b)
        kg_b_sin_a      = self.repo_cie.exportacion_sin_pasar(id_a, id_b)

        return ResultadoComparacion(
            nombre_a              = nom_a,
            nombre_b              = nom_b,
            id_a                  = id_a,
            id_b                  = id_b,
            kg_a                  = kg_a,
            kg_b                  = kg_b,
            productores_compartidos = productores_compartidos,
            productores_exclusivos_a= excl_a,
            productores_exclusivos_b= excl_b,
            cant_prod_compartidos  = len(productores_compartidos),
            kg_prod_compartidos    = sum(p.kg_total for p in productores_compartidos),
            mercados_compartidos   = mercados_compartidos,
            mercados_exclusivos_a  = excl_merc_a,
            mercados_exclusivos_b  = excl_merc_b,
            cant_merc_compartidos  = len(mercados_compartidos),
            clientes_compartidos   = clientes_compartidos,
            cant_cli_compartidos   = len(clientes_compartidos),
            productos_compartidos  = productos_compartidos,
            pct_b_pasa_por_a      = pct_b_pasa_por_a,
            kg_b_sin_a            = kg_b_sin_a,
        )

    def formato_comparacion(self, res: ResultadoComparacion) -> str:
        """Formatea el resultado de comparación como informe legible."""
        lines = [
            "",
            "═" * 70,
            f"  📊 ANÁLISIS COMPARATIVO",
            f"  {res.nombre_a}  vs  {res.nombre_b}",
            "═" * 70,
            "",
            f"  {'VOLUMEN TOTAL':<30} {res.nombre_a:<20} {res.nombre_b}",
            f"  {'─' * 70}",
            f"  {'Kg Totales':<30} {res.kg_a:>15,.0f}  {res.kg_b:>15,.0f}",
            "",
        ]

        # Productores compartidos
        lines.append(f"  👨‍🌾 PRODUCTORES COMPARTIDOS: {res.cant_prod_compartidos}")
        if res.productores_compartidos:
            lines.append(
                "  ┌──────────────────────────────────┬────────────┬────────────┬────────────┐"
            )
            lines.append(
                "  │ PRODUCTOR                        │  KG A      │    KG B    │  KG TOTAL  │"
            )
            lines.append(
                "  ├──────────────────────────────────┼────────────┼────────────┼────────────┤"
            )
            for p in res.productores_compartidos[:10]:
                lines.append(
                    f"  │ {p.nombre[:33]:<33} │ {p.kg_a:>10,.0f} │ {p.kg_b:>10,.0f} │ {p.kg_total:>10,.0f} │"
                )
            lines.append("  └──────────────────────────────────┴────────────┴────────────┴────────────┘")
        lines.append("")

        # Mercados compartidos
        lines.append(f"  🌍 MERCADOS COMPARTIDOS: {res.cant_merc_compartidos}")
        if res.mercados_compartidos:
            lines.append(
                "  ┌──────────────────────────────────┬────────────┬────────────┐"
            )
            lines.append(
                "  │ MERCADO                          │  % A       │    % B     │"
            )
            lines.append(
                "  ├──────────────────────────────────┼────────────┼────────────┤"
            )
            for m in res.mercados_compartidos[:8]:
                lines.append(
                    f"  │ {m.mercado[:33]:<33} │ {m.pct_a:>9.1f}%  │ {m.pct_b:>9.1f}%  │"
                )
            lines.append("  └──────────────────────────────────┴────────────┴────────────┘")
        lines.append("")

        # Porcentaje de paso
        lines.append("  📈 RELACIÓN DE PASO")
        lines.append(
            f"  • % de {res.nombre_b} que pasa por {res.nombre_a}: "
            f"{res.pct_b_pasa_por_a:.1f}%"
        )
        lines.append(
            f"  • Kg de {res.nombre_b} exportados sin {res.nombre_a}: "
            f"{res.kg_b_sin_a:,.0f} kg"
        )
        lines.append("")

        # Clientes compartidos
        if res.clientes_compartidos:
            lines.append(f"  🏬 CLIENTES COMPARTIDOS: {res.cant_cli_compartidos}")

        lines.append("═" * 70)
        return "\n".join(lines)
