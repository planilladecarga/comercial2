"""
=================================================================================
engine.py — Competitive Intelligence Engine — FRIMARAL BI
=================================================================================

Motor unificado de inteligencia competitiva que orquesta todos los servicios
y responde preguntas comerciales automáticamente.

Uso como librería:
    from competitive_intelligence import CompetitiveIntelligenceEngine

    engine = CompetitiveIntelligenceEngine("data/frimaral_bi.db")
    comparacion = engine.comparar("CALIRAL", "ARBIZA")
    oportunidades = engine.oportunidades("CALIRAL")
    radar = engine.radar("CALIRAL")
    riesgos = engine.riesgos("CALIRAL")
    indices = engine.indices("CALIRAL")

    # Consultas comerciales específicas
    resp = engine.consulta("¿Cuánto exportó SAN JACINTO sin pasar por CALIRAL?")

Uso como CLI:
    python -m competitive_intelligence.engine --comparar CALIRAL ARBIZA
    python -m competitive_intelligence.engine --oportunidades CALIRAL
    python -m competitive_intelligence.engine --radar CALIRAL
    python -m competitive_intelligence.engine --riesgos CALIRAL
    python -m competitive_intelligence.engine --indices CALIRAL
    python -m competitive_intelligence.engine --consulta "¿Cuánto exportó SAN JACINTO sin CALIRAL?"
    python -m competitive_intelligence.engine --listar
"""

from __future__ import annotations

import sys
import json
import argparse
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, Any

from competitive_intelligence.repositorio          import RepositorioCIE
from empresa360.repositorio                        import Repositorio
from competitive_intelligence.comparador_service import ComparadorService, ResultadoComparacion
from competitive_intelligence.indicadores_service  import IndicadoresService, IndicesComerciales
from competitive_intelligence.radar_service        import RadarService, RadarCambios
from competitive_intelligence.oportunidades_service import OportunidadesService, RankingOportunidades
from competitive_intelligence.alertas_service        import AlertasService, AlertasRiesgo


# ─────────────────────────────────────────────────────────────────────────────
# RESULTADO UNIFICADO
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class ResultadoCIE:
    """
    Resultado unificado del Competitive Intelligence Engine.
    """
    empresa              : str
    encontrada          : bool = False
    comparacion         : Optional[ResultadoComparacion] = None
    indices             : Optional[IndicesComerciales]  = None
    radar               : Optional[RadarCambios]         = None
    oportunidades       : Optional[RankingOportunidades] = None
    riesgos             : Optional[AlertasRiesgo]        = None
    errores             : list[str]                     = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "empresa": self.empresa,
            "encontrada": self.encontrada,
            "errores": self.errores or [],
        }
        if self.comparacion:
            d["comparacion"] = {
                "empresa_a": self.comparacion.nombre_a,
                "empresa_b": self.comparacion.nombre_b,
                "cant_prod_compartidos": self.comparacion.cant_prod_compartidos,
                "cant_merc_compartidos": self.comparacion.cant_merc_compartidos,
                "pct_b_pasa_por_a": self.comparacion.pct_b_pasa_por_a,
            }
        if self.indices:
            d["indices"] = self.indices.to_dict()
        if self.riesgos:
            d["riesgos"] = {
                "total": self.riesgos.total,
                "criticos": self.riesgos.count_criticos,
                "warnings": self.riesgos.count_warning,
            }
        return d


# ─────────────────────────────────────────────────────────────────────────────
# ENGINE PRINCIPAL
# ─────────────────────────────────────────────────────────────────────────────

class CompetitiveIntelligenceEngine:
    """
    Motor unificado de inteligencia competitiva.

    Uso:
        engine = CompetitiveIntelligenceEngine("data/frimaral_bi.db")
        resultado = engine.analisis_completo("CALIRAL")
    """

    def __init__(self, db_path: str = "data/frimaral_bi.db"):
        self.db_path = Path(db_path)
        self.repo    = RepositorioCIE(str(self.db_path))

        self._comparador    = ComparadorService(self.repo, Repositorio(str(self.db_path)))
        self._indicadores   = IndicadoresService(self.repo)
        self._radar         = RadarService(self.repo)
        self._oportunidades = OportunidadesService(self.repo)
        self._alertas       = AlertasService(self.repo)

        # Cache para resolvedores de empresa
        self._empresa_cache: dict[str, int] = {}

    # ─── Resolvedor de empresa ────────────────────────────────────────────

    def _resolver_empresa(self, nombre: str) -> Optional[int]:
        """Busca ID de empresa por nombre (con cache)."""
        if nombre in self._empresa_cache:
            return self._empresa_cache[nombre]

        # Buscar en la base
        with self.repo.connect() as conn:
            cur = conn.execute(
                "SELECT id_empresa FROM dim_empresas "
                "WHERE nombre_unif LIKE ? OR nombre_norm LIKE ? LIMIT 1",
                (f"%{nombre}%", f"%{nombre}%")
            )
            row = cur.fetchone()
            if row:
                self._empresa_cache[nombre] = row[0]
                return row[0]
        return None

    def _resolver_nombre(self, id_empresa: int) -> str:
        with self.repo.connect() as conn:
            cur = conn.execute(
                "SELECT nombre_unif FROM dim_empresas WHERE id_empresa = ? LIMIT 1",
                (id_empresa,)
            )
            row = cur.fetchone()
            return row[0] if row else f"Empresa {id_empresa}"

    def listar_empresas(self) -> list[dict[str, Any]]:
        """Lista todas las empresas con datos."""
        with self.repo.connect() as conn:
            cur = conn.execute("""
                SELECT e.id_empresa, e.nombre_unif,
                       COUNT(m.id_movimiento) AS movs,
                       SUM(m.kilos_netos) AS kg_total
                FROM dim_empresas e
                LEFT JOIN movimientos m ON m.empresa_id = e.id_empresa
                WHERE e.activo = 1
                GROUP BY e.id_empresa, e.nombre_unif
                HAVING movs > 0
                ORDER BY kg_total DESC
            """)
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]

    # ─── Análisis por empresa ─────────────────────────────────────────────

    def analisis_completo(self, nombre_empresa: str) -> ResultadoCIE:
        """
        Ejecuta el análisis completo para una empresa:
        indicadores, radar, oportunidades, riesgos.
        """
        resultado = ResultadoCIE(empresa=nombre_empresa)

        id_emp = self._resolver_empresa(nombre_empresa)
        if not id_emp:
            resultado.errores = [f"Empresa no encontrada: {nombre_empresa}"]
            return resultado

        resultado.encontrada = True
        nombre = self._resolver_nombre(id_emp)
        resultado.indices       = self._indicadores.calcular(id_emp)
        resultado.radar         = self._radar.detectar(id_emp)
        resultado.oportunidades = self._oportunidades.generar(id_emp)
        resultado.riesgos       = self._alertas.detectar(id_emp)

        return resultado

    # ─── Comparaciones ────────────────────────────────────────────────────

    def comparar(
        self,
        empresa_a: str,
        empresa_b: str,
    ) -> ResultadoCIE:
        """
        Compara dos empresas en todas las dimensiones.

        Args:
            empresa_a: Primera empresa (ej: "CALIRAL")
            empresa_b: Segunda empresa (ej: "ARBIZA")

        Returns:
            ResultadoCIE con la comparación completa.
        """
        resultado = ResultadoCIE(empresa=f"{empresa_a} vs {empresa_b}")

        id_a = self._resolver_empresa(empresa_a)
        id_b = self._resolver_empresa(empresa_b)

        if not id_a:
            resultado.errores = [f"Empresa no encontrada: {empresa_a}"]
            return resultado
        if not id_b:
            resultado.errores = [f"Empresa no encontrada: {empresa_b}"]
            return resultado

        nombre_a = self._resolver_nombre(id_a)
        nombre_b = self._resolver_nombre(id_b)

        resultado.encontrada = True
        resultado.comparacion = self._comparador.comparar(nombre_a, nombre_b)

        return resultado

    def oportunidades(self, nombre_empresa: str) -> RankingOportunidades:
        """Retorna ranking de oportunidades para una empresa."""
        id_emp = self._resolver_empresa(nombre_empresa)
        if not id_emp:
            return RankingOportunidades()
        return self._oportunidades.generar(id_emp)

    def radar(self, nombre_empresa: str) -> RadarCambios:
        """Retorna radar de cambios para una empresa."""
        id_emp = self._resolver_empresa(nombre_empresa)
        if not id_emp:
            return RadarCambios()
        return self._radar.detectar(id_emp)

    def riesgos(self, nombre_empresa: str) -> AlertasRiesgo:
        """Retorna alertas de riesgo para una empresa."""
        id_emp = self._resolver_empresa(nombre_empresa)
        if not id_emp:
            return AlertasRiesgo()
        return self._alertas.detectar(id_emp)

    def indices(self, nombre_empresa: str) -> IndicesComerciales:
        """Retorna los 5 índices comerciales de una empresa."""
        id_emp = self._resolver_empresa(nombre_empresa)
        if not id_emp:
            return IndicesComerciales(0, 0, 0, 0, 0)
        return self._indicadores.calcular(id_emp)

    # ─── Consultas comerciales en lenguaje natural ─────────────────────────

    def consulta(self, pregunta: str) -> str:
        """
        Responde preguntas comerciales en lenguaje natural.

        Consultas soportadas:
            • ¿Cuánto exportó [EMPRESA] sin pasar por [EMPRESA]?
            • ¿Qué porcentaje de [EMPRESA] pasa por [EMPRESA]?
            • ¿Qué productores comparten [EMPRESA] y [EMPRESA]?
            • ¿Qué productores podría captar [EMPRESA]?
            • ¿Qué mercados no trabaja [EMPRESA] pero sí la competencia?
        """
        p = pregunta.upper()

        # Pattern: exportó X sin pasar por Y
        import re
        m = re.search(
            r"EXPORT[ÓO]\s+(.+?)\s+SIN\s+PASAR\s+POR\s+(.+?)\?*\s*$",
            p, re.IGNORECASE
        )
        if m:
            emp_exp = m.group(1).strip()
            emp_sin = m.group(2).strip()
            return self._resp_exporto_sin_pasar(emp_exp, emp_sin)

        # Pattern: qué % de X pasa por Y
        m = re.search(
            r"QU[ÉE]\s+(PORCENTAJE|S\s*%\s*DE)\s+(.+?)\s+PASA\s+POR\s+(.+?)\?*\s*$",
            p, re.IGNORECASE
        )
        if m:
            emp_a = m.group(2).strip()
            emp_b = m.group(3).strip()
            return self._resp_pct_pasa_por(emp_a, emp_b)

        # Pattern: qué productores podría captar X
        m = re.search(
            r"QU[ÉE]\s+PRODUCTORES\s+PODR[ÍI]A\s+CAPTAR\s+(.+?)\?*\s*$",
            p, re.IGNORECASE
        )
        if m:
            emp = m.group(1).strip()
            return self._resp_captar(emp)

        return (
            "❓ Consulta no reconocida. "
            "Intenta:\n"
            "  • ¿Cuánto exportó EMPRESA sin pasar por EMPRESA?\n"
            "  • ¿Qué % de EMPRESA pasa por EMPRESA?\n"
            "  • ¿Qué productores podría captar EMPRESA?\n"
        )

    def _resp_exporto_sin_pasar(self, emp_exp: str, emp_sin: str) -> str:
        """Responde: ¿Cuánto exportó X sin pasar por Y?"""
        id_exp = self._resolver_empresa(emp_exp)
        id_sin = self._resolver_empresa(emp_sin)
        if not id_exp:
            return f"❓ Empresa no encontrada: {emp_exp}"
        if not id_sin:
            return f"❓ Empresa no encontrada: {emp_sin}"

        kg = self.repo.exportacion_sin_pasar(id_exp, id_sin)
        nombre_exp = self._resolver_nombre(id_exp)
        nombre_sin = self._resolver_nombre(id_sin)
        return (
            f"📦 {nombre_exp} exportó {kg:,.0f} kg "
            f"sin pasar por {nombre_sin}."
        )

    def _resp_pct_pasa_por(self, emp_a: str, emp_b: str) -> str:
        """Responde: ¿Qué % de A pasa por B?"""
        id_a = self._resolver_empresa(emp_a)
        id_b = self._resolver_empresa(emp_b)
        if not id_a:
            return f"❓ Empresa no encontrada: {emp_a}"
        if not id_b:
            return f"❓ Empresa no encontrada: {emp_b}"

        pct = self.repo.porcentaje_paso_por(id_a, id_b)
        nombre_a = self._resolver_nombre(id_a)
        nombre_b = self._resolver_nombre(id_b)
        return (
            f"📊 {pct:.1f}% del volumen de {nombre_a} "
            f"pasó por {nombre_b}."
        )

    def _resp_captar(self, emp: str) -> str:
        """Responde: ¿Qué productores podría captar X?"""
        id_emp = self._resolver_empresa(emp)
        if not id_emp:
            return f"❓ Empresa no encontrada: {emp}"

        prods = self.repo.productores_no_usan(id_emp, id_emp)
        nombre = self._resolver_nombre(id_emp)
        if not prods:
            return f"ℹ️  No se detectaron productores que no usen {nombre}."

        lines = [f"\n🎯 Productores que {nombre} podría captar:\n"]
        for i, p in enumerate(prods[:10], 1):
            lines.append(
                f"  {i}. {p['nombre_productor']} "
                f"({(p['kg_total'] or 0):,.0f} kg)"
            )
        lines.append(f"\n  Total detectados: {len(prods)}")
        return "\n".join(lines)

    # ─── Formateadores ───────────────────────────────────────────────────

    def formatear_comparacion(self, r: ResultadoCIE) -> str:
        if not r.encontrada:
            return f"❌ {r.errores}"
        return self._comparador.formato_comparacion(r.comparacion)

    def formatear_analisis(self, r: ResultadoCIE) -> str:
        """Formatea el análisis completo."""
        lines = [
            "\n" + "═" * 70,
            f"  🚀  ANÁLISIS COMPETITIVO — {r.empresa}",
            "═" * 70,
        ]

        if r.indices:
            lines.append("\n  📊 ÍNDICES COMERCIALES")
            lines.append(self._indicadores.formato(r.indices))

        if r.riesgos and r.riesgos.total > 0:
            lines.append(self._alertas.formato(r.riesgos))

        if r.radar and r.radar.total_cambios > 0:
            lines.append(self._radar.formato(r.radar))

        if r.oportunidades:
            lines.append(self._oportunidades.formato(r.oportunidades))

        lines.append("═" * 70)
        return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────

def _cli() -> None:
    parser = argparse.ArgumentParser(
        description="Competitive Intelligence Engine — FRIMARAL BI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("empresa", nargs="?", default=None)
    parser.add_argument("empresa_b", nargs="?", default=None)
    parser.add_argument(
        "--db", default="data/frimaral_bi.db",
        help="Ruta a la base SQLite"
    )
    parser.add_argument(
        "--comparar", action="store_true",
        help="Compara empresa A vs empresa B"
    )
    parser.add_argument(
        "--oportunidades", action="store_true",
        help="Muestra ranking de oportunidades"
    )
    parser.add_argument(
        "--radar", action="store_true",
        help="Muestra radar de cambios"
    )
    parser.add_argument(
        "--riesgos", action="store_true",
        help="Muestra alertas de riesgo"
    )
    parser.add_argument(
        "--indices", action="store_true",
        help="Muestra los 5 índices comerciales"
    )
    parser.add_argument(
        "--consulta", type=str, default=None,
        help="Pregunta en lenguaje natural"
    )
    parser.add_argument(
        "--listar", action="store_true",
        help="Lista empresas disponibles"
    )
    parser.add_argument(
        "--formato", default="texto",
        choices=["texto", "json"],
    )

    args = parser.parse_args()

    db_path = Path(__file__).parent.parent / args.db
    if not db_path.exists():
        print(f"❌ Base de datos no encontrada: {db_path}", file=sys.stderr)
        sys.exit(1)

    engine = CompetitiveIntelligenceEngine(str(db_path))

    # Listar
    if args.listar:
        empresas = engine.listar_empresas()
        print(f"\n  🏢  EMPRESAS DISPONIBLES ({len(empresas)} total)\n")
        print("  ┌────┬──────────────────────────────────────────┬────────────┬────────────┐")
        print("  │ #  │ NOMBRE                                     │   MOVIMS.  │  KG TOTAL  │")
        print("  ├────┼──────────────────────────────────────────┼────────────┼────────────┤")
        for i, emp in enumerate(empresas[:50], 1):
            nom = emp.get("nombre_unif", "")[:40]
            mov = emp.get("movs", 0) or 0
            kg  = emp.get("kg_total", 0) or 0
            print(f"  │ {i:>3} │ {nom:<42} │ {mov:>10,} │ {(kg/1000):>9.0f}K │")
        print("  └────┴──────────────────────────────────────────┴────────────┴────────────┘")
        return

    # Consulta en lenguaje natural
    if args.consulta:
        print(engine.consulta(args.consulta))
        return

    # Comparación
    if args.comparar:
        if not args.empresa or not args.empresa_b:
            print("❌ Se requieren dos empresas para --comparar", file=sys.stderr)
            sys.exit(1)
        r = engine.comparar(args.empresa, args.empresa_b)
        if args.formato == "json":
            print(json.dumps(r.to_dict(), ensure_ascii=False, indent=2))
        else:
            print(engine.formatear_comparacion(r))
        return

    # Análisis de una empresa
    if args.empresa:
        r = engine.analisis_completo(args.empresa)

        seccion = None
        if args.oportunidades:
            seccion = "oportunidades"
        elif args.radar:
            seccion = "radar"
        elif args.riesgos:
            seccion = "riesgos"
        elif args.indices:
            seccion = "indices"

        if args.formato == "json":
            print(json.dumps(r.to_dict(), ensure_ascii=False, indent=2))
            return

        if seccion == "oportunidades" and r.oportunidades:
            print(engine._oportunidades.formato(r.oportunidades))
        elif seccion == "radar" and r.radar:
            print(engine._radar.formato(r.radar))
        elif seccion == "riesgos" and r.riesgos:
            print(engine._alertas.formato(r.riesgos))
        elif seccion == "indices" and r.indices:
            print(engine._indicadores.formato(r.indices))
        else:
            print(engine.formatear_analisis(r))
        return

    parser.print_help()


if __name__ == "__main__":
    _cli()
