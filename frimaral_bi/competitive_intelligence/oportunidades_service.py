"""
=================================================================================
oportunidades_service.py — Ranking de oportunidades comerciales
=================================================================================

Genera rankings priorizados de oportunidades comerciales:
    1. Productores que nunca utilizaron la empresa (oportunidad de captación)
    2. Productores que usan más de un operador (multi-depósito)
    3. Productores que ya usan competidores
    4. Productores que exportan a mercados donde la empresa no participa
    5. Productores con fuerte crecimiento
    6. Mercados no explorados
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
from competitive_intelligence.repositorio import RepositorioCIE


@dataclass
class Oportunidad:
    """Una oportunidad comercial detectada."""
    tipo       : str
    prioridad  : int          # 1=alta, 2=media, 3=baja
    nombre     : str
    kg         : float
    detalle    : str = ""
    justificacion: str = ""


@dataclass
class RankingOportunidades:
    """Ranking completo de oportunidades."""
    captacion_posible  : list[Oportunidad] = field(default_factory=list)
    multi_deposito     : list[Oportunidad] = field(default_factory=list)
    competidores       : list[Oportunidad] = field(default_factory=list)
    exportacion        : list[Oportunidad] = field(default_factory=list)
    alto_crecimiento   : list[Oportunidad] = field(default_factory=list)
    mercados_inexplorados: list[Oportunidad] = field(default_factory=list)


class OportunidadesService:
    """
    Genera rankings de oportunidades comerciales para una empresa.

    Uso:
        opp = OportunidadesService(repo)
        ranking = opp.generar(id_empresa=5)
    """

    def __init__(self, repo: RepositorioCIE):
        self.repo = repo

    def generar(self, id_empresa: int) -> RankingOportunidades:
        """
        Genera el ranking completo de oportunidades.

        Args:
            id_empresa: ID de la empresa para la que se buscan oportunidades.

        Returns:
            RankingOportunidades con todas las oportunidades detectadas.
        """
        r = RankingOportunidades()

        # 1. Productores que NUNCA usaron esta empresa (captación pura)
        todos_para_captar = self.repo.productores_no_usan(id_empresa, id_empresa)
        for p in todos_para_captar[:20]:
            r.captacion_posible.append(Oportunidad(
                tipo          = "CAPTACIÓN",
                prioridad     = 1 if (p["kg_total"] or 0) > 10_000 else 2,
                nombre        = p["nombre_productor"],
                kg            = p["kg_total"] or 0,
                detalle       = f"Primera vez visto: {p['primera_fecha']}",
                justificacion = "Nunca utilizó esta empresa — captación nueva",
            ))

        # 2. Productores multi-depósito (ya trabajan con otros)
        multi = self.repo.productores_multi_deposito()
        for p in multi[:20]:
            r.multi_deposito.append(Oportunidad(
                tipo          = "MULTI-DEPÓSITO",
                prioridad     = 1 if (p["kg_total"] or 0) > 10_000 else 2,
                nombre        = p["nombre_productor"],
                kg            = p["kg_total"] or 0,
                detalle       = f"Trabaja con {p['cantidad_empresas']} operadores",
                justificacion = "Ya tiene relación con múltiples operadores",
            ))

        # 3. Productores que exportan a mercados no explorados
        prod_exp = self.repo.ranking_global_productores(limite=50)
        mercados_propios = {
            m["mercado"] for m in self.repo.mercados_empresa(id_empresa)
        }

        # Query outside loop - was called inside loop with same args (N+1 bug)
        export_no_a = self.repo.productores_exportan_mercado_no_a(
            id_empresa, id_empresa
        )
        for e in export_no_a[:10]:
            r.exportacion.append(Oportunidad(
                tipo          = "EXPORTACIÓN",
                prioridad     = 1,
                nombre        = e["nombre_productor"],
                kg            = e["kg_total"] or 0,
                detalle       = f"Mercado: {e['mercado']}",
                justificacion = "Exporta a mercados donde no participa la empresa",
            ))

        # 4. Crecimiento de productores
        crecimiento = self.repo.crecimiento_productores(id_empresa)
        for c in crecimiento[:10]:
            var = c.get("crecimiento_pct", 0) or 0
            r.alto_crecimiento.append(Oportunidad(
                tipo          = "CRECIMIENTO",
                prioridad     = 1 if var > 50 else 2,
                nombre        = c.get("nro_productor", ""),
                kg            = c.get("kg_actual", 0) or 0,
                detalle       = f"Crecimiento: {var:+.1f}%",
                justificacion = "Productor con crecimiento superior al 30%",
            ))

        # 5. Mercados no explorados
        mercs_todos = self.repo.todos_los_mercados()
        mercs_propios = {
            m["mercado"] for m in self.repo.mercados_empresa(id_empresa)
        }
        for m in mercs_todos:
            if m["mercado"] not in mercs_propios:
                r.mercados_inexplorados.append(Oportunidad(
                    tipo          = "MERCADO",
                    prioridad     = 2,
                    nombre        = m["mercado"],
                    kg            = m["kg_total"] or 0,
                    detalle       = "No participation yet",
                    justificacion = "Mercado donde la empresa no participa",
                ))

        return r

    def formato(self, r: RankingOportunidades) -> str:
        """Formatea el ranking como informe priorizado."""
        def _seccion(titulo: str, items: list[Oportunidad], icono: str):
            if not items:
                return []
            prioridad_labels = {1: "🔴 ALTA", 2: "🟡 MEDIA", 3: "🟢 BAJA"}
            lines = [f"\n  {icono} {titulo} ({len(items)} oportunidades)"]
            lines.append(
                "  ┌────┬─────────────────────────────────────────────┬────────────┬──────────────────────────┐"
            )
            lines.append(
                "  │ PR │ NOMBRE                                      │ KG         │ JUSTIFICACIÓN           │"
            )
            lines.append(
                "  ├────┼─────────────────────────────────────────────┼────────────┼──────────────────────────┤"
            )
            for o in items[:15]:
                prio_label = prioridad_labels.get(o.prioridad, "⚪")
                lines.append(
                    f"  │ {prio_label:<4} │ {o.nombre[:45]:<45} │ "
                    f"{(o.kg/1000):>8.1f}K │ {o.justificacion[:24]:<24} │"
                )
            lines.append(
                "  └────┴─────────────────────────────────────────────┴────────────┴──────────────────────────┘"
            )
            return lines

        header = [
            "\n\n  🚀  RANKING DE OPORTUNIDADES COMERCIALES",
            "  ────────────────────────────────────────────────────────────────",
        ]

        sections = []
        sections += _seccion("CAPTACIÓN POSIBLE",     r.captacion_posible,      "🎯")
        sections += _seccion("MULTI-DEPÓSITO",        r.multi_deposito,         "🔄")
        sections += _seccion("EXPORTACIÓN",            r.exportacion,             "🌍")
        sections += _seccion("ALTO CRECIMIENTO",       r.alto_crecimiento,       "📈")
        sections += _seccion("MERCADOS INEXPLORADOS", r.mercados_inexplorados,  "🗺️")

        total = (
            len(r.captacion_posible) + len(r.multi_deposito) +
            len(r.exportacion) + len(r.alto_crecimiento) +
            len(r.mercados_inexplorados)
        )
        sections.append(f"\n  📊 Total oportunidades detectadas: {total}")

        return "\n".join(header + sections)
