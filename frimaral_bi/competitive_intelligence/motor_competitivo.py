"""
=================================================================================
motor_competitivo.py — Motor de Inteligencia Competitiva (Unificado)
=================================================================================

Orquesta todos los servicios de inteligencia competitiva.

Uso:
    from competitive_intelligence import MotorCompetitivo
    motor = MotorCompetitivo("data/frimaral_bi.db")

    # Análisis completo de una empresa
    r = motor.analisis_completo("CALIRAL")

    # Comparar dos empresas
    c = motor.comparar("CALIRAL", "ARBIZA")

    # Oportunidades, Radar, Riesgos, Índices
    motor.oportunidades("CALIRAL")
    motor.radar("CALIRAL")
    motor.riesgos("CALIRAL")
    motor.indices("CALIRAL")

CLI:
    python -m competitive_intelligence.motor_competitivo "CALIRAL"
    python -m competitive_intelligence.motor_competitivo "CALIRAL" --vs "ARBIZA"
    python -m competitive_intelligence.motor_competitivo --oportunidades "CALIRAL"
    python -m competitive_intelligence.motor_competitivo --radar "CALIRAL"
    python -m competitive_intelligence.motor_competitivo --riesgos "CALIRAL"
    python -m competitive_intelligence.motor_competitivo --indices "CALIRAL"
    python -m competitive_intelligence.motor_competitivo --cuanto-sin "SAN JACINTO" "CALIRAL"
    python -m competitive_intelligence.motor_competitivo --quienes-no-usan "CALIRAL"
    python -m competitive_intelligence.motor_competitivo --quienes-ambos "CALIRAL" "ARBIZA"
"""

from __future__ import annotations

import sys
import json
import argparse
from pathlib import Path
from typing import Any, Optional

from ..empresa360.repositorio import Repositorio
from competitive_intelligence.repositorio import RepositorioCIE
from competitive_intelligence.indicadores_service import IndicadoresService, IndicesComerciales
from competitive_intelligence.comparador_service import ComparadorService, ResultadoComparacion
from competitive_intelligence.radar_service import RadarService, RadarCambios
from competitive_intelligence.oportunidades_service import OportunidadesService, RankingOportunidades
from competitive_intelligence.riesgos_service import RiesgosService, Riesgos360


# ─────────────────────────────────────────────────────────────────────────────
# RESULTADO ANÁLISIS COMPLETO
# ─────────────────────────────────────────────────────────────────────────────

class AnalisisCompleto:
    nombre_empresa: str
    encontrada: bool = False
    indices: Optional[IndicesComerciales] = None
    ranking_opp: Optional[RankingOportunidades] = None
    radar: Optional[RadarCambios] = None
    riesgos: Optional[Riesgos360] = None
    resumen: str = ""

    def __init__(self, nombre_empresa: str):
        self.nombre_empresa = nombre_empresa

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "nombre_empresa": self.nombre_empresa,
            "encontrada": self.encontrada,
            "resumen": self.resumen,
        }
        if self.indices:
            d["indices"] = self.indices.to_dict()
        if self.ranking_opp:
            d["oportunidades"] = self._opp_to_dict()
        if self.radar:
            d["radar"] = self._radar_to_dict()
        if self.riesgos:
            d["riesgos"] = [
                {"tipo": r.tipo, "nombre": r.nombre,
                 "nivel": r.nivel, "valor": r.valor, "detalle": r.detalle}
                for r in self.riesgos.riesgos
            ]
        return d

    def _opp_to_dict(self) -> dict[str, list]:
        if not self.ranking_opp:
            return {}
        def items(lst):
            return [{"tipo": o.tipo, "nombre": o.nombre, "kg": o.kg,
                     "prioridad": o.prioridad, "detalle": o.detalle}
                    for o in lst]
        return {
            "captacion_posible": items(self.ranking_opp.captacion_posible),
            "multi_deposito": items(self.ranking_opp.multi_deposito),
            "competidores": items(self.ranking_opp.competidores),
            "exportacion": items(self.ranking_opp.exportacion),
            "alto_crecimiento": items(self.ranking_opp.alto_crecimiento),
            "mercados_inexplorados": items(self.ranking_opp.mercados_inexplorados),
        }

    def _radar_to_dict(self) -> dict[str, list]:
        if not self.radar:
            return {}
        def items(lst):
            return [{"nombre": i.nombre, "kg": i.kg_actual,
                     "variacion": i.variacion_pct} for i in lst]
        return {
            "productores_nuevos": items(self.radar.productores_nuevos),
            "productores_perdidos": items(self.radar.productores_perdidos),
            "mercados_nuevos": items(self.radar.mercados_nuevos),
            "mercados_perdidos": items(self.radar.mercados_perdidos),
            "crecimiento_productores": items(self.radar.crecimiento_productores),
        }


# ─────────────────────────────────────────────────────────────────────────────
# MOTOR COMPETITIVO
# ─────────────────────────────────────────────────────────────────────────────

class MotorCompetitivo:
    """
    Motor unificado de inteligencia competitiva.
    """

    def __init__(self, db_path: str = "data/frimaral_bi.db"):
        path = Path(db_path)
        if not path.is_absolute():
            path = Path(__file__).parent.parent / db_path

        self.repo_emp360 = Repositorio(str(path))
        self.repo_cie    = RepositorioCIE(str(path))

        self.srv_indices  = IndicadoresService(self.repo_cie)
        self.srv_comp     = ComparadorService(self.repo_cie, self.repo_emp360)
        self.srv_radar    = RadarService(self.repo_cie)
        self.srv_opp      = OportunidadesService(self.repo_cie)
        self.srv_riesgos  = RiesgosService(self.repo_cie, self.repo_emp360)

    # ─── Análisis completo ────────────────────────────────────────────────

    def analisis_completo(
        self, nombre_empresa: str, dias: int = 90
    ) -> AnalisisCompleto:
        """Genera un análisis competitivo completo de una empresa."""
        emp = self.repo_emp360.empresa_por_nombre(nombre_empresa)
        resultado = AnalisisCompleto(nombre_empresa=nombre_empresa)

        if not emp:
            return resultado

        resultado.encontrada = True
        id_empresa = emp["id_empresa"]

        try:
            resultado.indices = self.srv_indices.calcular(id_empresa)
        except Exception:
            pass

        try:
            resultado.ranking_opp = self.srv_opp.generar(id_empresa)
        except Exception:
            pass

        try:
            resultado.radar = self.srv_radar.detectar(id_empresa)
        except Exception:
            pass

        try:
            resultado.riesgos = self.srv_riesgos.detectar(nombre_empresa)
        except Exception:
            pass

        resultado.resumen = self._generar_resumen(resultado)
        return resultado

    def _generar_resumen(self, res: AnalisisCompleto) -> str:
        partes = []
        if res.indices:
            nivel = "🔴 ALTO" if res.indices.iries >= 70 \
                else "🟡 MEDIO" if res.indices.iries >= 40 else "🟢 BAJO"
            partes.append(f"⚠️ Riesgo: {nivel}")
        if res.ranking_opp:
            total = (len(res.ranking_opp.captacion_posible)
                   + len(res.ranking_opp.multi_deposito)
                   + len(res.ranking_opp.exportacion))
            partes.append(f"🎯 {total} oportunidades")
        if res.radar:
            partes.append(f"🔭 {res.radar.total_cambios} cambios")
        if res.riesgos and res.riesgos.riesgos:
            partes.append(f"⚠️ {len(res.riesgos.riesgos)} riesgos")
        return " | ".join(partes) if partes else "Sin datos"

    # ─── Módulos individuales ───────────────────────────────────────────

    def comparar(self, nombre_a: str, nombre_b: str) -> Optional[ResultadoComparacion]:
        return self.srv_comp.comparar(nombre_a, nombre_b)

    def oportunidades(self, nombre_empresa: str) -> Optional[RankingOportunidades]:
        emp = self.repo_emp360.empresa_por_nombre(nombre_empresa)
        if not emp:
            return None
        return self.srv_opp.generar(emp["id_empresa"])

    def radar(self, nombre_empresa: str) -> Optional[RadarCambios]:
        emp = self.repo_emp360.empresa_por_nombre(nombre_empresa)
        if not emp:
            return None
        return self.srv_radar.detectar(emp["id_empresa"])

    def riesgos(self, nombre_empresa: str) -> Optional[Riesgos360]:
        return self.srv_riesgos.detectar(nombre_empresa)

    def indices(self, nombre_empresa: str) -> Optional[IndicesComerciales]:
        emp = self.repo_emp360.empresa_por_nombre(nombre_empresa)
        if not emp:
            return None
        return self.srv_indices.calcular(emp["id_empresa"])

    # ─── Consultas comerciales específicas ─────────────────────────────

    def cuanto_exporta_sin(self, nombre_empresa: str, excluye: str) -> dict:
        """¿Cuánto exportó empresa sin pasar por excluye?"""
        emp_a = self.repo_emp360.empresa_por_nombre(nombre_empresa)
        emp_b = self.repo_emp360.empresa_por_nombre(excluye)
        if not emp_a or not emp_b:
            return {"error": "Empresa no encontrada"}
        kg = self.repo_cie.exportacion_sin_pasar(emp_b["id_empresa"], emp_a["id_empresa"])
        return {
            "empresa": emp_a["nombre_unif"],
            "excluye": emp_b["nombre_unif"],
            "kg_exportados_sin_excluye": kg,
        }

    def porcentaje_que_pasa_por(self, nombre_empresa: str, por: str) -> dict:
        """¿Qué % de empresa pasa por otra?"""
        emp_a = self.repo_emp360.empresa_por_nombre(nombre_empresa)
        emp_b = self.repo_emp360.empresa_por_nombre(por)
        if not emp_a or not emp_b:
            return {"error": "Empresa no encontrada"}
        pct = self.repo_cie.porcentaje_paso_por(emp_b["id_empresa"], emp_a["id_empresa"])
        return {
            "empresa": emp_a["nombre_unif"],
            "pasa_por": emp_b["nombre_unif"],
            "porcentaje": pct,
        }

    def quienes_usan_ambos(self, nombre_a: str, nombre_b: str) -> dict:
        """¿Qué productores comparten empresa A y B?"""
        comp = self.srv_comp.comparar(nombre_a, nombre_b)
        if not comp:
            return {"error": "Empresa no encontrada"}
        return {
            "empresa_a": nombre_a,
            "empresa_b": nombre_b,
            "productores_compartidos": [
                {"nombre": p.nombre, "nro": p.nro_productor,
                 "kg_a": p.kg_a, "kg_b": p.kg_b}
                for p in comp.productores_compartidos
            ],
            "cantidad": comp.cant_prod_compartidos,
        }

    def quienes_no_usan(self, nombre_empresa: str, limite: int = 20) -> dict:
        """¿Qué productores NO usan la empresa?"""
        emp = self.repo_emp360.empresa_por_nombre(nombre_empresa)
        if not emp:
            return {"error": "Empresa no encontrada"}
        prod_no = self.repo_cie.productores_no_usan(emp["id_empresa"], emp["id_empresa"])
        return {
            "empresa": emp["nombre_unif"],
            "productores_no_usan": [
                {"nombre": r["nombre_productor"], "nro": r["nro_productor"],
                 "kg_total": r["kg_total"]}
                for r in prod_no[:limite]
            ],
            "total": len(prod_no),
        }

    def ranking_productores(self, nombre_empresa: str, limite: int = 20) -> dict:
        """¿Cuáles son los N productores más importantes?"""
        emp = self.repo_emp360.empresa_por_nombre(nombre_empresa)
        if not emp:
            return {"error": "Empresa no encontrada"}
        prod = self.repo_cie.top_productores_empresa(emp["id_empresa"], limite)
        kg_total = self.repo_cie.kg_total_empresa(emp["id_empresa"])
        return {
            "empresa": emp["nombre_unif"],
            "kg_total": kg_total,
            "productores": [
                {"nombre": r["nombre_productor"], "nro": r["nro_productor"],
                 "kg": r["kg_total"],
                 "movimientos": r["cantidad_movimientos"],
                 "pct": round((r["kg_total"] or 0) / max(kg_total, 1) * 100, 2)}
                for r in prod
            ],
        }

    # ─── Formateadores ─────────────────────────────────────────────────

    def formatear(self, seccion: str, *args, **kwargs) -> str:
        """Formatea resultados según la sección solicitada."""
        fmt = {
            "oportunidades": self.srv_opp.formato,
            "radar": self.srv_radar.formato,
            "riesgos": self.srv_riesgos.formato_riesgos,
            "indices": self.srv_indices.formato,
        }
        fn = fmt.get(seccion)
        if fn:
            return fn(*args, **kwargs)
        return "Sección no disponible"


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────

def _cli() -> None:
    parser = argparse.ArgumentParser(
        description="Competitive Intelligence Engine — FRIMARAL BI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("empresa", nargs="?", default=None)
    parser.add_argument("--db", default="data/frimaral_bi.db")
    parser.add_argument("--vs", dest="vs")
    parser.add_argument("--seccion",
                        choices=["completo", "indices", "oportunidades",
                                 "radar", "riesgos", "comparacion"],
                        default="completo")
    parser.add_argument("--formato", choices=["texto", "json"], default="texto")
    parser.add_argument("--oportunidades", metavar="EMPRESA")
    parser.add_argument("--radar", metavar="EMPRESA")
    parser.add_argument("--riesgos", metavar="EMPRESA")
    parser.add_argument("--indices", metavar="EMPRESA")
    parser.add_argument("--cuanto-sin", nargs=2, metavar=("EMPRESA", "EXCLUYE"))
    parser.add_argument("--quienes-no-usan", metavar="EMPRESA")
    parser.add_argument("--quienes-ambos", nargs=2, metavar=("A", "B"))
    parser.add_argument("--ranking-prod", nargs=2, metavar=("EMPRESA", "N"), type=int)
    parser.add_argument("--dias", type=int, default=90)

    args = parser.parse_args()
    db_path = Path(__file__).parent.parent / args.db

    if not db_path.exists():
        print(f"❌ Base no encontrada: {db_path}", file=sys.stderr)
        sys.exit(1)

    motor = MotorCompetitivo(str(db_path))

    # ── --oportunidades ────────────────────────────────────────────────
    if args.oportunidades:
        r = motor.oportunidades(args.oportunidades)
        if not r:
            print(f"❌ Empresa no encontrada: {args.oportunidades}")
            sys.exit(1)
        print(motor.srv_opp.formato(r))
        return

    # ── --radar ───────────────────────────────────────────────────────
    if args.radar:
        r = motor.radar(args.radar)
        if not r:
            print(f"❌ Empresa no encontrada: {args.radar}")
            sys.exit(1)
        print(motor.srv_radar.formato(r))
        return

    # ── --riesgos ─────────────────────────────────────────────────────
    if args.riesgos:
        r = motor.riesgos(args.riesgos)
        if not r:
            print(f"❌ Empresa no encontrada: {args.riesgos}")
            sys.exit(1)
        print(motor.srv_riesgos.formato_riesgos(r))
        return

    # ── --indices ─────────────────────────────────────────────────────
    if args.indices:
        r = motor.indices(args.indices)
        if not r:
            print(f"❌ Empresa no encontrada: {args.indices}")
            sys.exit(1)
        print(motor.srv_indices.formato(r))
        return

    # ── --cuanto-sin ──────────────────────────────────────────────────
    if args.cuanto_sin:
        res = motor.cuanto_exporta_sin(args.cuanto_sin[0], args.cuanto_sin[1])
        if "error" in res:
            print(f"❌ {res['error']}")
            sys.exit(1)
        print(f"\n  📤 Exportación de {res['empresa']} sin pasar por {res['excluye']}:")
        print(f"  → {res['kg_exportados_sin_excluye']:,.0f} kg")
        return

    # ── --quienes-no-usan ─────────────────────────────────────────────
    if args.quienes_no_usan:
        res = motor.quienes_no_usan(args.quienes_no_usan)
        if "error" in res:
            print(f"❌ {res['error']}")
            sys.exit(1)
        print(f"\n  🎯 Productores que NO usan {res['empresa']} ({res['total']} total):")
        for p in res["productores_no_usan"]:
            print(f"  • {p['nombre']} — {p['kg_total']:,.0f} kg")
        return

    # ── --quienes-ambos ───────────────────────────────────────────────
    if args.quienes_ambos:
        res = motor.quienes_usan_ambos(args.quienes_ambos[0], args.quienes_ambos[1])
        if "error" in res:
            print(f"❌ {res['error']}")
            sys.exit(1)
        print(f"\n  🔗 Productores compartidos entre {res['empresa_a']} y {res['empresa_b']}:")
        print(f"  Total: {res['cantidad']}")
        for p in res["productores_compartidos"]:
            print(f"  • {p['nombre']} — A:{p['kg_a']:,.0f} kg | B:{p['kg_b']:,.0f} kg")
        return

    # ── Comparar ──────────────────────────────────────────────────────
    if args.vs:
        comp = motor.comparar(args.empresa, args.vs)
        if not comp:
            print("❌ Alguna empresa no fue encontrada")
            sys.exit(1)
        if args.formato == "json":
            d = {
                "empresa_a": comp.nombre_a, "empresa_b": comp.nombre_b,
                "kg_a": comp.kg_a, "kg_b": comp.kg_b,
                "productores_compartidos": comp.cant_prod_compartidos,
                "pct_b_pasa_por_a": comp.pct_b_pasa_por_a,
                "kg_b_sin_a": comp.kg_b_sin_a,
            }
            print(json.dumps(d, ensure_ascii=False, indent=2))
        else:
            print(motor.srv_comp.formato_comparacion(comp))
        return

    # ── Análisis completo ─────────────────────────────────────────────
    if not args.empresa:
        parser.print_help()
        sys.exit(1)

    resultado = motor.analisis_completo(args.empresa, dias=args.dias)

    if not resultado.encontrada:
        print(f"❌ Empresa no encontrada: {args.empresa}")
        sys.exit(1)

    if args.formato == "json":
        print(json.dumps(resultado.to_dict(), ensure_ascii=False, indent=2))
        return

    # Texto
    print("")
    print("═" * 70)
    print(f"  🏢 ANÁLISIS COMPETITIVO — {resultado.nombre_empresa}")
    print(f"  Resumen: {resultado.resumen}")
    print("═" * 70)

    if resultado.indices:
        print("\n  ─── ÍNDICES ───")
        print(motor.srv_indices.formato(resultado.indices))

    if resultado.ranking_opp:
        print("\n  ─── OPORTUNIDADES ───")
        print(motor.srv_opp.formato(resultado.ranking_opp))

    if resultado.radar:
        print("\n  ─── RADAR ───")
        print(motor.srv_radar.formato(resultado.radar))

    if resultado.riesgos:
        print("\n  ─── RIESGOS ───")
        print(motor.srv_riesgos.formato_riesgos(resultado.riesgos))

    print("\n" + "═" * 70)


if __name__ == "__main__":
    _cli()
