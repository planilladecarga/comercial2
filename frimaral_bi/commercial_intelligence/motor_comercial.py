"""
=================================================================================
motor_comercial.py — Orquestador del Commercial Intelligence Engine
=================================================================================

Uso:
    from commercial_intelligence import MotorComercial
    motor = MotorComercial("data/frimaral_bi.db")

    # Análisis completo de una empresa
    resultado = motor.analisis_completo("CALIRAL")

    # Calcular scores de todas las empresas
    scores = motor.calcular_scores()

    # Obtener rankings
    rankings = motor.generar_rankings()

    # Obtener recomendaciones
    recomendaciones = motor.generar_recomendaciones("CALIRAL")
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional
from dataclasses import dataclass, asdict

from empresa360.repositorio import Repositorio
from ..database import db
from .scoring.scoring_service import ScoringService
from .scoring.models import ScoreResult, ScoreBreakdown, FactorDetail
from .rules.rules_engine import RulesEngine
from .recommendations.recommendation_engine import RecommendationEngine
from .risk.risk_engine import RiskEngine, RiskLevel
from .opportunity.opportunity_engine import OpportunityEngine, PotentialLevel
from .configuration.config_repository import ConfigRepository
from .rankings.rankings_generator import RankingsGenerator
from .indicators.indicators_calculator import IndicatorsCalculator
from .rules.rule import Rule
from .recommendations.recommendation_types import Recommendation


# ─────────────────────────────────────────────────────────────────────────────
# RESULTADO ANÁLISIS COMPLETO
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class AnalisisComercialResult:
    """Resultado completo del análisis comercial de una empresa."""
    nombre_empresa: str
    encontrada: bool = False
    id_empresa: Optional[int] = None
    tipo_empresa: Optional[str] = None

    # Scores
    score_total: Optional[float] = None
    nivel_riesgo: Optional[str] = None
    nivel_potencial: Optional[str] = None
    nivel_fidelidad: Optional[str] = None
    nivel_dependencia: Optional[str] = None

    # Breakdown
    breakdown: Optional[ScoreBreakdown] = None

    # Recomendaciones
    recomendaciones: list[Recommendation] = None

    # Indicadores
    indicadores: Optional[dict[str, Any]] = None

    # Metadata
    fecha_calculo: Optional[str] = None
    periodo_evaluado: Optional[str] = None

    def __post_init__(self):
        if self.recomendaciones is None:
            self.recomendaciones = []

    def to_dict(self) -> dict[str, Any]:
        """Convierte el resultado a diccionario para JSON."""
        result = {
            "nombre_empresa": self.nombre_empresa,
            "encontrada": self.encontrada,
        }

        if not self.encontrada:
            return result

        result.update({
            "id_empresa": self.id_empresa,
            "tipo_empresa": self.tipo_empresa,
            "score_total": round(self.score_total, 2) if self.score_total else None,
            "nivel_riesgo": self.nivel_riesgo,
            "nivel_potencial": self.nivel_potencial,
            "nivel_fidelidad": self.nivel_fidelidad,
            "nivel_dependencia": self.nivel_dependencia,
            "fecha_calculo": self.fecha_calculo,
            "periodo_evaluado": self.periodo_evaluado,
        })

        if self.breakdown:
            result["breakdown"] = {
                "score_total": round(self.breakdown.score_total, 2),
                "nivel": self.breakdown.nivel,
                "factores": [
                    {
                        "factor_key": f.factor_key,
                        "factor_nombre": f.factor_nombre,
                        "valor": round(f.valor, 2),
                        "peso": round(f.peso, 2),
                        "contribucion": round(f.contribucion, 2),
                        "comparacion_periodo": f.comparacion_periodo,
                        "detalle": f.detalle,
                    }
                    for f in self.breakdown.factores
                ],
                "fecha_calculo": self.breakdown.fecha_calculo,
                "periodo_evaluado": self.breakdown.periodo_evaluado,
            }

        if self.recomendaciones:
            result["recomendaciones"] = [
                {
                    "id": r.id,
                    "regla_id": r.regla_id,
                    "recomendacion": r.recomendacion,
                    "prioridad": r.prioridad,
                    "categoria": r.categoria,
                    "estado": r.estado,
                }
                for r in self.recomendaciones
            ]

        if self.indicadores:
            result["indicadores"] = self.indicadores

        return result


# ─────────────────────────────────────────────────────────────────────────────
# MOTOR COMERCIAL
# ─────────────────────────────────────────────────────────────────────────────

class MotorComercial:
    """
    Orquestador principal del Commercial Intelligence Engine.

    Coordina todos los servicios para generar un análisis comercial completo
    de cada empresa.
    """

    def __init__(self, db_path: str = "data/frimaral_bi.db"):
        """
        Inicializa el motor comercial.

        Args:
            db_path: Ruta a la base de datos SQLite
        """
        path = Path(db_path)
        if not path.is_absolute():
            path = Path(__file__).parent.parent.parent / db_path

        self.repo_emp360 = Repositorio(str(path))
        self.config_repo = ConfigRepository(str(path))

        # Inicializar servicios
        self.scoring_service = ScoringService(self.config_repo)
        self.rules_engine = RulesEngine(self.config_repo)
        self.recommendation_engine = RecommendationEngine(self.rules_engine)
        self.risk_engine = RiskEngine(self.scoring_service)
        self.opportunity_engine = OpportunityEngine(self.scoring_service)
        self.rankings_generator = RankingsGenerator(
            self.scoring_service,
            self.risk_engine,
            self.opportunity_engine,
            self.repo_emp360,
        )
        self.indicators_calculator = IndicatorsCalculator(self.repo_emp360)

        # Asegurar tablas de configuración
        self._asegurar_tablas()

    def _asegurar_tablas(self) -> None:
        """Crea las tablas de configuración si no existen."""
        from .configuration.default_config import DEFAULT_SCORES_CONFIG, DEFAULT_RULES

        # Tabla config_scores
        db.execute("""
            CREATE TABLE IF NOT EXISTS config_scores (
                id_config INTEGER PRIMARY KEY AUTOINCREMENT,
                factor_key TEXT UNIQUE NOT NULL,
                factor_nombre TEXT NOT NULL,
                peso_default REAL NOT NULL,
                peso_actual REAL NOT NULL,
                peso_min REAL NOT NULL,
                peso_max REAL NOT NULL,
                activo INTEGER DEFAULT 1,
                fecha_modificacion TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Tabla config_reglas
        db.execute("""
            CREATE TABLE IF NOT EXISTS config_reglas (
                id_regla INTEGER PRIMARY KEY AUTOINCREMENT,
                regla_id TEXT UNIQUE NOT NULL,
                nombre TEXT NOT NULL,
                descripcion TEXT,
                prioridad INTEGER DEFAULT 50,
                tipo_evaluacion TEXT NOT NULL,
                condicion_json TEXT NOT NULL,
                recomendacion_json TEXT NOT NULL,
                estado INTEGER DEFAULT 1,
                categoria TEXT,
                fecha_creacion TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Tabla scores_empresa
        db.execute("""
            CREATE TABLE IF NOT EXISTS scores_empresa (
                id_score INTEGER PRIMARY KEY AUTOINCREMENT,
                id_empresa INTEGER NOT NULL,
                tipo_empresa TEXT NOT NULL,
                score_total REAL NOT NULL,
                nivel_riesgo TEXT NOT NULL,
                nivel_potencial TEXT NOT NULL,
                nivel_fidelidad TEXT NOT NULL,
                nivel_dependencia TEXT,
                breakdown_json TEXT NOT NULL,
                fecha_calculo TEXT NOT NULL,
                periodo_evaluado TEXT,
                UNIQUE(id_empresa, periodo_evaluado)
            )
        """)

        # Tabla recomendaciones
        db.execute("""
            CREATE TABLE IF NOT EXISTS recomendaciones (
                id_recomendacion INTEGER PRIMARY KEY AUTOINCREMENT,
                id_empresa INTEGER NOT NULL,
                regla_id TEXT NOT NULL,
                recomendacion TEXT NOT NULL,
                prioridad INTEGER NOT NULL,
                categoria TEXT NOT NULL,
                estado TEXT DEFAULT 'PENDIENTE',
                fecha_generacion TEXT NOT NULL,
                fecha_resolucion TEXT,
                notas TEXT
            )
        """)

        # Tabla rankings
        db.execute("""
            CREATE TABLE IF NOT EXISTS rankings (
                id_ranking INTEGER PRIMARY KEY AUTOINCREMENT,
                tipo_ranking TEXT NOT NULL,
                id_empresa INTEGER NOT NULL,
                posicion INTEGER NOT NULL,
                score_parcial REAL,
                metricas_json TEXT,
                fecha_calculo TEXT NOT NULL,
                periodo_evaluado TEXT,
                UNIQUE(tipo_ranking, id_empresa, periodo_evaluado)
            )
        """)

        # Poblar configuración por defecto si está vacía
        self._poblar_config_default()

    def _poblar_config_default(self) -> None:
        """Pobla la configuración por defecto si las tablas están vacías."""
        from .configuration.default_config import DEFAULT_SCORES_CONFIG, DEFAULT_RULES

        # Poblar config_scores
        existing_scores = db.execute_scalar("SELECT COUNT(*) FROM config_scores")
        if existing_scores == 0:
            for config in DEFAULT_SCORES_CONFIG:
                db.execute(
                    """INSERT INTO config_scores
                       (factor_key, factor_nombre, peso_default, peso_actual, peso_min, peso_max)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (config["factor_key"], config["factor_nombre"],
                     config["peso_default"], config["peso_actual"],
                     config["peso_min"], config["peso_max"])
                )

        # Poblar config_reglas
        existing_rules = db.execute_scalar("SELECT COUNT(*) FROM config_reglas")
        if existing_rules == 0:
            for regla in DEFAULT_RULES:
                db.execute(
                    """INSERT INTO config_reglas
                       (regla_id, nombre, descripcion, prioridad, tipo_evaluacion,
                        condicion_json, recomendacion_json, estado, categoria)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (regla["regla_id"], regla["nombre"], regla["descripcion"],
                     regla["prioridad"], regla["tipo_evaluacion"],
                     json.dumps(regla["condicion"]),
                     json.dumps(regla["recomendacion"]),
                     regla["estado"], regla["categoria"])
                )

    # ─── Análisis Completo ────────────────────────────────────────────────

    def analisis_completo(self, nombre_empresa: str, periodo: str = "ultimos_6_meses") -> AnalisisComercialResult:
        """
        Genera un análisis comercial completo de una empresa.

        Args:
            nombre_empresa: Nombre de la empresa a analizar
            periodo: Período de evaluación (default: "ultimos_6_meses")

        Returns:
            AnalisisComercialResult con todos los análisis
        """
        resultado = AnalisisComercialResult(nombre_empresa=nombre_empresa)

        emp = self.repo_emp360.empresa_por_nombre(nombre_empresa)
        if not emp:
            return resultado

        resultado.encontrada = True
        resultado.id_empresa = emp["id_empresa"]
        resultado.tipo_empresa = emp.get("tipo_principal", "PRODUCTOR")

        try:
            # 1. Calcular Score
            score_result = self.scoring_service.calcular_score(
                emp["id_empresa"],
                periodo=periodo
            )
            resultado.score_total = score_result.score_total
            resultado.breakdown = score_result.breakdown

            # 2. Calcular Riesgo
            resultado.nivel_riesgo = self.risk_engine.calcular_riesgo(
                emp["id_empresa"],
                score_result
            ).value

            # 3. Calcular Potencial
            resultado.nivel_potencial = self.opportunity_engine.calcular_potencial(
                emp["id_empresa"],
                score_result
            ).value

            # 4. Calcular Fidelidad
            from .scoring.factors.historial_factor import HistorialFactor
            historial_factor = HistorialFactor(self.scoring_service.repo)
            resultado.nivel_fidelidad = historial_factor.calcular_fidelidad(
                emp["id_empresa"]
            ).value

            # 5. Detectar Dependencia
            from .scoring.factors.volumen_factor import VolumenFactor
            vol_factor = VolumenFactor(self.scoring_service.repo)
            resultado.nivel_dependencia = vol_factor.detectar_dependencia(
                emp["id_empresa"]
            )

            # 6. Generar Recomendaciones
            resultado.recomendaciones = self.recommendation_engine.generar(
                emp["id_empresa"],
                score_result,
                self._obtener_indicadores_basicos(emp["id_empresa"])
            )

            # 7. Calcular Indicadores
            resultado.indicadores = self.indicators_calculator.calcular_todos(
                emp["id_empresa"],
                score_result
            )

            # Metadata
            from datetime import datetime
            resultado.fecha_calculo = datetime.now().isoformat()
            resultado.periodo_evaluado = periodo

        except Exception as e:
            # Log error pero no fallar
            print(f"Error en análisis completo: {e}")

        return resultado

    def _obtener_indicadores_basicos(self, id_empresa: int) -> dict[str, Any]:
        """Obtiene indicadores básicos para el motor de reglas."""
        try:
            movs = self.repo_emp360.movimientos_por_empresa(id_empresa, limite=1000)
            kg_total = self.repo_emp360.kg_totales(id_empresa)
            cant_mov = len(movs)

            # Productores únicos
            productores = set()
            for m in movs:
                if m.get("nombre_productor"):
                    productores.add(m["nombre_productor"])

            # Mercados únicos
            mercados = set()
            for m in movs:
                if m.get("mercado"):
                    mercados.add(m["mercado"])

            return {
                "kg_total": kg_total,
                "cant_movimientos": cant_mov,
                "cant_productores": len(productores),
                "cant_mercados": len(mercados),
            }
        except Exception:
            return {}

    # ─── Scores ────────────────────────────────────────────────────────────

    def calcular_scores(self, periodo: str = "ultimos_6_meses") -> list[ScoreResult]:
        """
        Calcula el score comercial para todas las empresas.

        Args:
            periodo: Período de evaluación

        Returns:
            Lista de ScoreResult para cada empresa
        """
        resultados = []
        empresas = self.repo_emp360.todas_empresas_id()

        for id_empresa, nombre in empresas:
            try:
                score = self.scoring_service.calcular_score(id_empresa, periodo)
                resultados.append(score)
            except Exception:
                continue

        return resultados

    def score_empresa(self, id_empresa: int, periodo: str = "ultimos_6_meses") -> Optional[ScoreResult]:
        """Calcula el score para una empresa específica."""
        return self.scoring_service.calcular_score(id_empresa, periodo)

    # ─── Rankings ─────────────────────────────────────────────────────────

    def generar_rankings(self, periodo: str = "ultimos_6_meses") -> dict[str, list[dict]]:
        """
        Genera todos los rankings automáticos.

        Returns:
            Diccionario con rankings por tipo
        """
        return self.rankings_generator.generar_todos(periodo)

    def ranking(self, tipo_ranking: str, limite: int = 20, periodo: str = "ultimos_6_meses") -> list[dict]:
        """Obtiene un ranking específico."""
        return self.rankings_generator.generar(tipo_ranking, limite, periodo)

    # ─── Recomendaciones ─────────────────────────────────────────────────

    def generar_recomendaciones(self, nombre_empresa: str, periodo: str = "ultimos_6_meses") -> list[Recommendation]:
        """Genera recomendaciones para una empresa."""
        emp = self.repo_emp360.empresa_por_nombre(nombre_empresa)
        if not emp:
            return []

        score_result = self.scoring_service.calcular_score(emp["id_empresa"], periodo)
        indicadores = self._obtener_indicadores_basicos(emp["id_empresa"])

        return self.recommendation_engine.generar(emp["id_empresa"], score_result, indicadores)

    def actualizar_recomendacion(self, id_recomendacion: int, estado: str, notas: str = None) -> bool:
        """Actualiza el estado de una recomendación."""
        from datetime import datetime

        if notas:
            db.execute(
                "UPDATE recomendaciones SET estado = ?, notas = ?, fecha_resolucion = ? WHERE id_recomendacion = ?",
                (estado, notas, datetime.now().isoformat(), id_recomendacion)
            )
        else:
            db.execute(
                "UPDATE recomendaciones SET estado = ?, fecha_resolucion = ? WHERE id_recomendacion = ?",
                (estado, datetime.now().isoformat(), id_recomendacion)
            )
        return True

    # ─── Configuración ───────────────────────────────────────────────────

    def obtener_config_factores(self) -> list[dict]:
        """Obtiene la configuración actual de factores."""
        return self.config_repo.obtener_todos_factores()

    def actualizar_peso_factor(self, factor_key: str, nuevo_peso: float) -> bool:
        """Actualiza el peso de un factor."""
        return self.config_repo.actualizar_peso_factor(factor_key, nuevo_peso)

    def obtener_reglas(self) -> list[Rule]:
        """Obtiene todas las reglas configuradas."""
        return self.config_repo.obtener_todas_reglas()

    def actualizar_estado_regla(self, regla_id: str, activo: bool) -> bool:
        """Activa o desactiva una regla."""
        return self.config_repo.actualizar_estado_regla(regla_id, activo)


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────

def _cli():
    """Interfaz de línea de comandos para el motor comercial."""
    import argparse
    import sys

    parser = argparse.ArgumentParser(
        description="Commercial Intelligence Engine — FRIMARAL BI Sprint 8",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("empresa", nargs="?", default=None)
    parser.add_argument("--db", default="data/frimaral_bi.db")
    parser.add_argument("--periodo", default="ultimos_6_meses")
    parser.add_argument("--formato", choices=["texto", "json"], default="texto")
    parser.add_argument("--scores", action="store_true")
    parser.add_argument("--rankings", action="store_true")
    parser.add_argument("--ranking-tipo")

    args = parser.parse_args()
    db_path = Path(__file__).parent.parent.parent / args.db

    if not db_path.exists():
        print(f"❌ Base no encontrada: {db_path}", file=sys.stderr)
        sys.exit(1)

    motor = MotorComercial(str(db_path))

    # ── Scores global ──────────────────────────────────────────────────
    if args.scores:
        scores = motor.calcular_scores(periodo=args.periodo)
        print(f"\n📊 SCORES CALCULADOS: {len(scores)} empresas")
        for s in scores[:20]:
            print(f"  {s.id_empresa}: {s.score_total:.1f} ({s.breakdown.nivel if s.breakdown else 'N/A'})")
        return

    # ── Rankings ───────────────────────────────────────────────────────
    if args.rankings or args.ranking_tipo:
        tipo = args.ranking_tipo or "TOP_OPORTUNIDADES"
        ranking = motor.ranking(tipo, limite=20, periodo=args.periodo)
        print(f"\n🏆 RANKING: {tipo}")
        for i, item in enumerate(ranking, 1):
            print(f"  {i}. {item['nombre']} — Score: {item.get('score_parcial', 'N/A')}")
        return

    # ── Análisis completo ──────────────────────────────────────────────
    if not args.empresa:
        parser.print_help()
        sys.exit(1)

    resultado = motor.analisis_completo(args.empresa, periodo=args.periodo)

    if not resultado.encontrada:
        print(f"❌ Empresa no encontrada: {args.empresa}")
        sys.exit(1)

    if args.formato == "json":
        print(json.dumps(resultado.to_dict(), ensure_ascii=False, indent=2))
        return

    # Texto
    print("")
    print("═" * 70)
    print(f"  📈 ANÁLISIS COMERCIAL — {resultado.nombre_empresa}")
    print("═" * 70)

    if resultado.score_total is not None:
        print(f"\n  SCORE COMERCIAL: {resultado.score_total:.1f}/100")
        print(f"  Riesgo: {resultado.nivel_riesgo}")
        print(f"  Potencial: {resultado.nivel_potencial}")
        print(f"  Fidelidad: {resultado.nivel_fidelidad}")
        if resultado.nivel_dependencia:
            print(f"  Dependencia: {resultado.nivel_dependencia}")

    if resultado.breakdown:
        print("\n  ─── DESGLOSE ───")
        for f in resultado.breakdown.factores:
            print(f"  • {f.factor_nombre}: {f.valor:.1f} (peso: {f.peso}) — {f.detalle}")

    if resultado.recomendaciones:
        print(f"\n  ─── RECOMENDACIONES ({len(resultado.recomendaciones)}) ───")
        for r in resultado.recomendaciones[:5]:
            print(f"  [{r.prioridad}] {r.recomendacion}")

    print("\n" + "═" * 70)


if __name__ == "__main__":
    _cli()
