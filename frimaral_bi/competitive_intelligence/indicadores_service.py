"""
=================================================================================
indicadores_service.py — Índices comerciales de inteligencia competitiva
=================================================================================

Calcula 5 índices documentados:

    1. Índice de Diversificación (IDIV)
       Mide qué tan diversificado está el portfolio de un empresa.
       0 = monoproducer, 100 = perfectamente diversificado.

    2. Índice de Fidelidad (IFID)
       Mide qué tan estables son los productores/clientes de la empresa.
       0 = sin fidelidad, 100 = máxima fidelidad.

    3. Índice de Presión Competitiva (ICOMP)
       Mide qué tan competido está el ecosistema de la empresa.
       0 = sin presión, 100 = mercado altamente competido.

    4. Índice de Riesgo (IRIES)
       Mide concentración: clientes, mercados, dependencia.
       0 = sin riesgo, 100 = riesgo máximo.

    5. Índice de Oportunidad (IOPORT)
       Mide el potencial de crecimiento basado en dinámica de mercado.
       0 = sin oportunidad, 100 = máxima oportunidad.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
from competitive_intelligence.repositorio import RepositorioCIE


@dataclass
class IndicesComerciales:
    """Los 5 índices calculados para una empresa."""
    idiv    : float  # Índice Diversificación   (0-100)
    ifid    : float  # Índice Fidelidad         (0-100)
    icomp   : float  # Índice Competencia       (0-100)
    iries   : float  # Índice Riesgo            (0-100)
    ioport  : float  # Índice Oportunidad       (0-100)

    def to_dict(self) -> dict[str, float]:
        return {
            "indice_diversificacion"  : round(self.idiv, 1),
            "indice_fidelidad"        : round(self.ifid, 1),
            "indice_competencia"      : round(self.icomp, 1),
            "indice_riesgo"           : round(self.iries, 1),
            "indice_oportunidad"      : round(self.ioport, 1),
        }


class IndicadoresService:
    """
    Calcula los 5 índices comerciales para cualquier empresa.

    Uso:
        svc = IndicadoresService(repo)
        idx = svc.calcular(id_empresa=5)
    """

    def __init__(self, repo: RepositorioCIE):
        self.repo = repo

    def calcular(self, id_empresa: int) -> IndicesComerciales:
        """
        Calcula los 5 índices para una empresa.

        Metodología:
            IDIV  — Herfindahl-Hirschman inverso sobre productos/mercados
            IFID  — Productores que vuelven vs total de productores únicos
            ICOMP — % de productores que también trabajan con competidores
            IRIES — Concentración de kg en top 3 clientes/mercados
            IOPORT — Growth rate de mercado vs company growth rate
        """
        kg_total = self.repo.kg_total_empresa(id_empresa)
        if kg_total == 0:
            return IndicesComerciales(0, 0, 0, 0, 0)

        # ── IDIV: Diversificación ─────────────────────────────────────────────
        idiv = self._calcular_diversificacion(id_empresa, kg_total)

        # ── IFID: Fidelidad ─────────────────────────────────────────────────
        ifid = self._calcular_fidelidad(id_empresa)

        # ── ICOMP: Presión competitiva ───────────────────────────────────────
        icomp = self._calcular_competencia(id_empresa)

        # ── IRIES: Riesgo ───────────────────────────────────────────────────
        iries = self._calcular_riesgo(id_empresa, kg_total)

        # ── IOPORT: Oportunidad ──────────────────────────────────────────────
        ioport = self._calcular_oportunidad(id_empresa)

        return IndicesComerciales(
            idiv   = round(idiv, 1),
            ifid   = round(ifid, 1),
            icomp  = round(icomp, 1),
            iries  = round(iries, 1),
            ioport = round(ioport, 1),
        )

    def _calcular_diversificacion(
        self, id_empresa: int, kg_total: float
    ) -> float:
        """
        IDIV: 1 - HHI normalizado.
        HHI = sum(s_i^2) donde s_i = share de cada producto/mercado.
        IDIV = (1 - HHI) * 100 / (1 - 1/n)
        """
        if kg_total == 0:
            return 0.0

        # Por producto
        prods = self.repo.productos_empresa(id_empresa)
        if not prods:
            return 0.0

        shares_prod = [(p["kg_total"] or 0) / kg_total for p in prods]
        hhi_prod = sum(s ** 2 for s in shares_prod)

        # Por mercado
        mercs = self.repo.mercados_empresa(id_empresa)
        if not mercs:
            return 0.0

        shares_merc = [(m["kg_total"] or 0) / kg_total for m in mercs]
        hhi_merc = sum(s ** 2 for s in shares_merc)

        # HHI combinado
        hhi = (hhi_prod + hhi_merc) / 2

        n_prod = len(prods)
        n_merc = len(mercs)
        n = max(n_prod, n_merc, 1)

        # Normalizado 0-100
        hhi_normalizado = hhi * n
        idiv = max(0, (1 - hhi_normalizado) * 100)
        return min(idiv, 100.0)

    def _calcular_fidelidad(self, id_empresa: int) -> float:
        """
        IFID: Productores que tienen más de 1 movimiento con la empresa
        vs total de productores únicos.
        """
        prods = self.repo.productores_empresa(id_empresa)
        if not prods:
            return 0.0

        fieles = [p for p in prods if (p["cantidad_movimientos"] or 0) > 1]
        return (len(fieles) / len(prods)) * 100

    def _calcular_competencia(self, id_empresa: int) -> float:
        """
        ICOMP: % de productores de la empresa que también trabajan
        con AL MENOS una otra empresa (competencia indirecta).
        """
        prods_a = self.repo.productores_empresa(id_empresa)
        if not prods_a:
            return 0.0

        prod_ids_a = {p["nro_productor"] for p in prods_a}
        if not prod_ids_a:
            return 0.0

        # Buscar esos mismos productores en otras empresas
        multi_dep = self.repo.productores_multi_deposito()
        en_conflicto = [
            p for p in multi_dep
            if p["nro_productor"] in prod_ids_a
        ]
        return (len(en_conflicto) / len(prods_a)) * 100

    def _calcular_riesgo(
        self, id_empresa: int, kg_total: float
    ) -> float:
        """
        IRIES: Concentración en top 3 clientes y top 3 mercados.
        Si top3 representa >60% del volumen → alto riesgo.
        """
        if kg_total == 0:
            return 0.0

        riesgo = 0.0

        # Concentración por cliente
        clis = self.repo.clientes_empresa(id_empresa)
        if clis:
            top3_kg = sum(c["kg_total"] or 0 for c in clis[:3])
            conc_clientes = top3_kg / kg_total
            riesgo += conc_clientes * 30  # peso 30

        # Concentración por mercado
        mercs = self.repo.mercados_empresa(id_empresa)
        if mercs:
            top3_kg = sum(m["kg_total"] or 0 for m in mercs[:3])
            conc_mercados = top3_kg / kg_total
            riesgo += conc_mercados * 30  # peso 30

        # Concentración por producto
        prods = self.repo.productos_empresa(id_empresa)
        if prods:
            top1_kg = prods[0]["kg_total"] or 0
            conc_prod = top1_kg / kg_total
            riesgo += conc_prod * 40  # peso 40

        return min(riesgo, 100.0)

    def _calcular_oportunidad(self, id_empresa: int) -> float:
        """
        IOPORT: Basado en:
          - % de mercado no explorado por la empresa
          - Productores nuevos en los últimos 90 días
          - Crecimiento de productores con alto potencial
        """
        oportunidad = 0.0

        # Oportunidad por mercados no explorados
        mercs_propios = set(
            m["mercado"] for m in self.repo.mercados_empresa(id_empresa)
        )
        mercs_todos = self.repo.todos_los_mercados()
        mercs_totales = {m["mercado"] for m in mercs_todos}

        mercs_inexplorados = mercs_totales - mercs_propios
        if mercs_totales:
            oportunidad += (
                len(mercs_inexplorados) / len(mercs_totales)
            ) * 40

        # Oportunidad por productores nuevos
        nuevos = self.repo.productores_nuevos(id_empresa, dias=90)
        if nuevos:
            oportunidad += min(len(nuevos) * 2, 20)

        # Oportunidad por productores con alto crecimiento
        crecimiento = self.repo.crecimiento_productores(id_empresa)
        if crecimiento:
            oportunidad += min(len(crecimiento) * 3, 40)

        return min(oportunidad, 100.0)

    # ─── Formateador ───────────────────────────────────────────────────────

    def formato(self, idx: IndicesComerciales) -> str:
        """Formatea los índices como tabla visual con explicación."""
        def barra(valor: float, ancho: int = 20) -> str:
            filled = int((valor / 100) * ancho)
            return "[" + "█" * filled + "░" * (ancho - filled) + "]"

        lines = [
            "  ┌─────────────────────┬────────────┬──────────────────────────────┐",
            "  │ ÍNDICE              │ VALOR      │ DESCRIPCIÓN                 │",
            "  ├─────────────────────┼────────────┼──────────────────────────────┤",
            f"  │ 🔀 IDIV (Diversif.) │ {barra(idx.idiv):20} │ 0=monoproducer 100=diversif │",
            f"  │ 💚 IFID (Fidelidad) │ {barra(idx.ifid):20} │ 0=sin fidelidad 100=fiel   │",
            f"  │ ⚔️  ICOMP (Comp.)   │ {barra(idx.icomp):20} │ 0=solo 100=competido      │",
            f"  │ ⚠️  IRIES (Riesgo)  │ {barra(idx.iries):20} │ 0=sin riesgo 100=máximo   │",
            f"  │ 🚀 IOPORT (Oport.)  │ {barra(idx.ioport):20} │ 0=sin opción 100=máxima   │",
            "  └─────────────────────┴────────────┴──────────────────────────────┘",
        ]
        return "\n".join(lines)
