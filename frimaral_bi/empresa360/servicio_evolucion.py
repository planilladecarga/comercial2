"""
=================================================================================
servicio_evolucion.py — Evolución mensual de volúmenes
=================================================================================
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
from .repositorio import Repositorio


@dataclass
class MesDato:
    anio: int
    mes: int
    nombre_mes: str
    trimestre: int
    kg: float
    movimientos: int
    variacion_pct: Optional[float] = None  # vs mes anterior


@dataclass
class Evolucion360:
    meses: list[MesDato] = field(default_factory=list)
    kg_maximo: float = 0.0
    kg_promedio: float = 0.0
    tendencia: str = "estable"  # "subiendo" | "bajando" | "estable"


class ServicioEvolucion:
    """Calcula la evolución mensual de una empresa."""

    def __init__(self, repo: Repositorio):
        self.repo = repo

    def calcular(self, id_empresa: int) -> Evolucion360:
        """Calcula la evolución mensual de kg y movimientos."""
        filas = self.repo.evolucion_mensual(id_empresa)

        if not filas:
            return Evolucion360()

        meses: list[MesDato] = []
        prev_kg: float | None = None

        for row in filas:
            kg = row["kg_total"] or 0.0
            variacion: float | None = None
            if prev_kg is not None and prev_kg > 0:
                variacion = round(((kg - prev_kg) / prev_kg) * 100, 1)
            prev_kg = kg

            meses.append(MesDato(
                anio          = row["anio"],
                mes           = row["mes"],
                nombre_mes    = row["nombre_mes"],
                trimestre     = row["trimestre"],
                kg            = kg,
                movimientos   = row["cantidad_movimientos"],
                variacion_pct = variacion,
            ))

        kg_values = [m.kg for m in meses]
        kg_max = max(kg_values) if kg_values else 0.0
        kg_avg = sum(kg_values) / len(kg_values) if kg_values else 0.0

        # Tendencia: últimas 3 varianzas
        tendencia = self._calcular_tendencia(meses)

        return Evolucion360(
            meses       = meses,
            kg_maximo   = kg_max,
            kg_promedio = kg_avg,
            tendencia   = tendencia,
        )

    def _calcular_tendencia(self, meses: list[MesDato]) -> str:
        """Calcula tendencia basándose en los últimos 3 meses."""
        if len(meses) < 2:
            return "⏳ Sin datos suficientes"
        ultimos = meses[-3:]
        varianzas = [m.variacion_pct for m in ultimos if m.variacion_pct is not None]
        if not varianzas:
            return "➡️  Estable"
        avg_var = sum(varianzas) / len(varianzas)
        if avg_var > 5:
            return "📈 Subiendo"
        elif avg_var < -5:
            return "📉 Bajando"
        return "➡️  Estable"

    def formato_tabla(self, evo: Evolucion360, top: int = 12) -> str:
        """Formatea evolución como tabla ASCII (últimos N meses)."""
        if not evo.meses:
            return "  ℹ️  Sin datos de evolución"
        meses = evo.meses[-top:]
        lines = [
            "  ┌────────┬──────────┬────────────┬──────────┬──────────┐",
            "  │ PERÍODO     │     KG    │   VARIAC.  │ MOVIMS.  │ TEND.   │",
            "  ├────────┼──────────┼────────────┼──────────┼──────────┤",
        ]
        for m in meses:
            var_str = f"{m.variacion_pct:+.1f}%" if m.variacion_pct else "  —  "
            indicador = "📈" if (m.variacion_pct or 0) > 5 else "📉" if (m.variacion_pct or 0) < -5 else "➡️"
            periodo = f"{m.nombre_mes[:3]} {m.anio}"
            lines.append(
                f"  │ {periodo:<10} │ {m.kg:>9,.0f} │ {indicador} {var_str:>7} │ {m.movimientos:>8,} │          │"
            )
        lines.append("  └────────┴──────────┴────────────┴──────────┴──────────┘")
        lines.append(f"  📊 Promedio: {evo.kg_promedio:,.0f} kg/mes  |  "
                     f"Máximo: {evo.kg_maximo:,.0f} kg  |  "
                     f"Tendencia: {evo.tendencia}")
        return "\n".join(lines)

    def markets_evolucion(self, evo: Evolucion360) -> list[dict]:
        """Retorna datos de evolución para graphing (dict limpio)."""
        return [
            {
                "periodo": f"{m.nombre_mes[:3]} {m.anio}",
                "kg": m.kg,
                "movimientos": m.movimientos,
                "variacion_pct": m.variacion_pct,
            }
            for m in evo.meses
        ]
