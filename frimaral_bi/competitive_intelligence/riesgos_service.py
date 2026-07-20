"""
=================================================================================
riesgos_service.py — Detección de Riesgos Comerciales
=================================================================================
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
from empresa360.repositorio import Repositorio
from competitive_intelligence.repositorio import RepositorioCIE


@dataclass
class RiesgoComercial:
    tipo      : str   # "CONCENTRACION" | "INACTIVIDAD" | "COMPETENCIA" | "MERCADO"
    nombre    : str
    detalle   : str
    nivel     : str   # "ALTO" | "MEDIO" | "BAJO"
    valor     : float
    pct_afectado: float  # % del negocio afectado
    prioridad : int   # 0=baja, 1=media, 2=alta


@dataclass
class Riesgos360:
    empresa    : str
    riesgos    : list[RiesgoComercial] = field(default_factory=list)
    nivel_general: str = "BAJO"  # "ALTO" | "MEDIO" | "BAJO"


class RiesgosService:
    """
    Detecta riesgos comerciales automáticamente.

    Tipos de riesgo:
        CONCENTRACIÓN   — Dependencia excesiva de un productor/cliente
        INACTIVIDAD     — Sin actividad reciente
        COMPETENCIA     — Pérdida de productores por competencia
        MERCADO         — Mercado en descenso
        FIDELIDAD       — Bajo índice de fidelización
    """

    UMBRAL_CONCENTRACION_ALTO = 60.0   # % del volumen en un solo actor
    UMBRAL_CONCENTRACION_MEDIO = 40.0
    UMBRAL_INACTIVIDAD_DIAS = 60

    def __init__(self, repo_cie: RepositorioCIE, repo_emp360: Repositorio):
        self.repo_cie = repo_cie
        self.repo_emp = repo_emp360

    def detectar(self, nombre_empresa: str) -> Optional[Riesgos360]:
        """Detecta todos los riesgos para una empresa."""
        emp = self.repo_emp.empresa_por_nombre(nombre_empresa)
        if not emp:
            return None

        id_empresa = emp["id_empresa"]
        nombre_unif = emp["nombre_unif"]
        riesgos: list[RiesgoComercial] = []

        kg_total = self.repo_cie.kg_total_empresa(id_empresa)
        if kg_total == 0:
            return Riesgos360(empresa=nombre_unif, riesgos=[])

        # ── 1. Concentración en productores ───────────────────────────
        prod = self.repo_cie.productores_empresa(id_empresa)
        if prod:
            sorted_prod = sorted(prod, key=lambda r: r["kg_total"], reverse=True)
            top1 = sorted_prod[0]
            top3 = sorted_prod[:3]
            top5 = sorted_prod[:5]

            # Top-1
            pct1 = (top1["kg_total"] / kg_total) * 100
            if pct1 >= self.UMBRAL_CONCENTRACION_ALTO:
                nivel, prio = "ALTO", 2
            elif pct1 >= self.UMBRAL_CONCENTRACION_MEDIO:
                nivel, prio = "MEDIO", 1
            else:
                nivel, prio = "BAJO", 0

            if nivel != "BAJO":
                riesgos.append(RiesgoComercial(
                    tipo="CONCENTRACIÓN",
                    nombre=top1["nombre_productor"],
                    detalle=f"Productor {top1['nombre_productor']} = {pct1:.1f}% del volumen total",
                    nivel=nivel, valor=pct1,
                    pct_afectado=pct1, prioridad=prio,
                ))

            # Top-3
            pct3 = sum(r["kg_total"] for r in top3) / kg_total * 100
            if pct3 >= 80:
                riesgos.append(RiesgoComercial(
                    tipo="CONCENTRACIÓN",
                    nombre="Top 3 productores",
                    detalle=f"Top-3 = {pct3:.1f}% del volumen (riesgo de concentración)",
                    nivel="ALTO", valor=pct3,
                    pct_afectado=pct3, prioridad=1,
                ))

        # ── 2. Concentración en mercados ─────────────────────────────
        merca = self.repo_cie.mercados_empresa(id_empresa)
        if merca:
            top_merca = sorted(merca, key=lambda r: r["kg_total"], reverse=True)[0]
            pct_merca = (top_merca["kg_total"] / kg_total) * 100
            if pct_merca >= self.UMBRAL_CONCENTRACION_ALTO:
                riesgos.append(RiesgoComercial(
                    tipo="CONCENTRACIÓN",
                    nombre=f"Mercado: {top_merca['mercado']}",
                    detalle=f"Un mercado representa {pct_merca:.1f}% — diversify",
                    nivel="ALTO", valor=pct_merca,
                    pct_afectado=pct_merca, prioridad=2,
                ))
            elif pct_merca >= self.UMBRAL_CONCENTRACION_MEDIO:
                riesgos.append(RiesgoComercial(
                    tipo="CONCENTRACIÓN",
                    nombre=f"Mercado: {top_merca['mercado']}",
                    detalle=f"Un mercado = {pct_merca:.1f}% del volumen",
                    nivel="MEDIO", valor=pct_merca,
                    pct_afectado=pct_merca, prioridad=1,
                ))

        # ── 3. Inactividad reciente ─────────────────────────────────
        inactivas = self.repo_cie.empresas_sin_actividad_reciente(
            self.UMBRAL_INACTIVIDAD_DIAS
        )
        if any(r["id_empresa"] == id_empresa for r in inactivas):
            riesgos.append(RiesgoComercial(
                tipo="INACTIVIDAD",
                nombre=f"> {self.UMBRAL_INACTIVIDAD_DIAS} días sin movimiento",
                detalle="Empresa sin actividad reciente — riesgo de abandono",
                nivel="ALTO", valor=100.0,
                pct_afectado=100.0, prioridad=2,
            ))

        # ── 4. Clientes en decremento ────────────────────────────────
        decr = self.repo_cie.clientes_decreciendo(id_empresa)
        for d in decr[:5]:
            riesgos.append(RiesgoComercial(
                tipo="COMPETENCIA",
                nombre=d["destino"],
                detalle=f"Cliente en caída: {d['variacion_pct']:+.1f}%",
                nivel="MEDIO" if d["variacion_pct"] > -40 else "ALTO",
                valor=abs(d["variacion_pct"]),
                pct_afectado=min(abs(d["variacion_pct"]) / 100, 1.0) * 100,
                prioridad=1 if d["variacion_pct"] > -40 else 2,
            ))

        # ── 5. Productores que abandonaron ───────────────────────────
        prod_perd = self.repo_cie.productores_que_abandonaron(
            id_empresa, dias=90
        )
        for p in prod_perd[:3]:
            riesgos.append(RiesgoComercial(
                tipo="COMPETENCIA",
                nombre=p["nombre_productor"],
                detalle=f"Productor abandonado: {p['ultima_fecha']}",
                nivel="MEDIO", valor=50.0,
                pct_afectado=min((p["kg_total"] or 0) / kg_total * 100, 100),
                prioridad=1,
            ))

        # Ordenar por prioridad
        riesgos.sort(key=lambda r: r.prioridad, reverse=True)

        # Nivel general
        if not riesgos:
            nivel_gen = "BAJO"
        elif any(r.nivel == "ALTO" for r in riesgos):
            nivel_gen = "ALTO"
        else:
            nivel_gen = "MEDIO"

        return Riesgos360(
            empresa=nombre_unif,
            riesgos=riesgos,
            nivel_general=nivel_gen,
        )

    def formato_riesgos(self, riesgos: Riesgos360) -> str:
        """Formatea los riesgos como informe visual."""
        color_nivel = {
            "ALTO": "🔴", "MEDIO": "🟡", "BAJO": "🟢"
        }
        em = color_nivel.get(riesgos.nivel_general, "⚪")

        lines = [
            "",
            "═" * 70,
            f"  ⚠️  EVALUACIÓN DE RIESGOS — {riesgos.empresa}",
            f"  Nivel general: {em} {riesgos.nivel_general}",
            "═" * 70,
        ]

        if not riesgos.riesgos:
            lines.append("\n  ✅ Sin riesgos identificados — perfil saludable")
            lines.append("═" * 70)
            return "\n".join(lines)

        lines.append(
            "  ┌──────┬──────────────────────────────────┬────────┬────────────┬──────────┐"
        )
        lines.append(
            "  │ TIPO │ RIESGO                           │ NIVEL  │    VALOR   │ % AFECT. │"
        )
        lines.append(
            "  ├──────┼──────────────────────────────────┼────────┼────────────┼──────────┤"
        )

        for r in riesgos.riesgos:
            em_color = color_nivel.get(r.nivel, "⚪")
            lines.append(
                f"  │ {r.tipo[:6]:<6} │ {r.nombre[:30]:<30} │ {em_color} {r.nivel:<6} │ "
                f"{r.valor:>9.1f}% │ {r.pct_afectado:>8.1f}% │"
            )
            lines.append(
                f"  │      │ {r.detalle[:62]:<62} │        │            │          │"
            )

        lines.append("  └──────┴──────────────────────────────────┴────────┴────────────┴──────────┘")

        # Resumen
        altos   = sum(1 for r in riesgos.riesgos if r.nivel == "ALTO")
        medios  = sum(1 for r in riesgos.riesgos if r.nivel == "MEDIO")
        bajos   = sum(1 for r in riesgos.riesgos if r.nivel == "BAJO")
        lines.append(
            f"\n  Resumen: 🔴 {altos} ALTO  |  🟡 {medios} MEDIO  |  🟢 {bajos} BAJO"
        )
        lines.append("═" * 70)
        return "\n".join(lines)
