"""
CommercialIntelligenceRoutes - Rutas API del Commercial Intelligence Engine
"""
from fastapi import APIRouter, Query, Path, Body
from typing import Optional
from pydantic import BaseModel
from datetime import datetime

from ..database import db
from frimaral_bi.commercial_intelligence import MotorComercial

router = APIRouter()

# Instancia global del motor
_motor: Optional[MotorComercial] = None


def get_motor() -> MotorComercial:
    """Obtiene o crea la instancia del motor comercial."""
    global _motor
    if _motor is None:
        _motor = MotorComercial()
    return _motor


# ─── Modelos Pydantic ────────────────────────────────────────────────────────

class ActualizarRecomendacionRequest(BaseModel):
    estado: str
    notas: Optional[str] = None


class CalcularTodoRequest(BaseModel):
    periodo: str = "ultimos_6_meses"


class ActualizarPesoFactorRequest(BaseModel):
    peso_actual: float


# ─── Scores ─────────────────────────────────────────────────────────────────

@router.get("/scores")
def get_scores(periodo: str = Query(default="ultimos_6_meses")):
    """Obtiene los scores de todas las empresas."""
    motor = get_motor()
    scores = motor.calcular_scores(periodo)
    return {
        "total": len(scores),
        "scores": [
            {
                "id_empresa": s.id_empresa,
                "score_total": round(s.score_total, 2),
                "nivel": s.breakdown.nivel if s.breakdown else None,
                "periodo": periodo,
            }
            for s in scores
        ],
    }


@router.get("/scores/{id_empresa}")
def get_score_empresa(id_empresa: int, periodo: str = Query(default="ultimos_6_meses")):
    """Obtiene el score de una empresa específica."""
    motor = get_motor()
    score = motor.score_empresa(id_empresa, periodo)
    if not score:
        return {"error": "Empresa no encontrada"}, 404
    return {
        "id_empresa": score.id_empresa,
        "score_total": round(score.score_total, 2),
        "nivel": score.breakdown.nivel if score.breakdown else None,
        "periodo": periodo,
    }


@router.get("/scores/{id_empresa}/breakdown")
def get_score_breakdown(id_empresa: int, periodo: str = Query(default="ultimos_6_meses")):
    """Obtiene el breakdown detallado del score de una empresa."""
    motor = get_motor()
    score = motor.score_empresa(id_empresa, periodo)
    if not score:
        return {"error": "Empresa no encontrada"}, 404

    if not score.breakdown:
        return {"error": "Sin breakdown disponible"}, 404

    return {
        "id_empresa": id_empresa,
        "score_total": round(score.score_total, 2),
        "nivel": score.breakdown.nivel,
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
            for f in score.breakdown.factores
        ],
        "fecha_calculo": score.breakdown.fecha_calculo,
        "periodo_evaluado": score.breakdown.periodo_evaluado,
    }


# ─── Riesgos ─────────────────────────────────────────────────────────────────

@router.get("/riesgos")
def get_riesgos(periodo: str = Query(default="ultimos_6_meses")):
    """Obtiene los niveles de riesgo de todas las empresas."""
    motor = get_motor()
    scores = motor.calcular_scores(periodo)
    riesgos = []
    for s in scores:
        riesgo = motor.risk_engine.calcular_riesgo(s.id_empresa, s)
        riesgos.append({
            "id_empresa": s.id_empresa,
            "nivel_riesgo": riesgo.nivel.value,
            "score_total": round(s.score_total, 2),
        })
    return {"total": len(riesgos), "riesgos": riesgos}


@router.get("/riesgos/{id_empresa}")
def get_riesgo_empresa(id_empresa: int, periodo: str = Query(default="ultimos_6_meses")):
    """Obtiene el Nivel de riesgo de una empresa específica."""
    motor = get_motor()
    score = motor.score_empresa(id_empresa, periodo)
    if not score:
        return {"error": "Empresa no encontrada"}, 404

    riesgo = motor.risk_engine.calcular_riesgo(id_empresa, score)
    return {
        "id_empresa": id_empresa,
        "nivel_riesgo": riesgo.nivel.value,
        "score_total": round(score.score_total, 2),
    }


# ─── Oportunidades ───────────────────────────────────────────────────────────

@router.get("/oportunidades")
def get_oportunidades(periodo: str = Query(default="ultimos_6_meses")):
    """Obtiene los niveles de potencial de todas las empresas."""
    motor = get_motor()
    scores = motor.calcular_scores(periodo)
    oportunidades = []
    for s in scores:
        potencial = motor.opportunity_engine.calcular_potencial(s.id_empresa, s)
        oportunidades.append({
            "id_empresa": s.id_empresa,
            "nivel_potencial": potencial.nivel.value,
            "score_total": round(s.score_total, 2),
        })
    return {"total": len(oportunidades), "oportunidades": oportunidades}


@router.get("/oportunidades/{id_empresa}")
def get_oportunidad_empresa(id_empresa: int, periodo: str = Query(default="ultimos_6_meses")):
    """Obtiene el nivel de potencial de una empresa específica."""
    motor = get_motor()
    score = motor.score_empresa(id_empresa, periodo)
    if not score:
        return {"error": "Empresa no encontrada"}, 404

    potencial = motor.opportunity_engine.calcular_potencial(id_empresa, score)
    return {
        "id_empresa": id_empresa,
        "nivel_potencial": potencial.nivel.value,
        "score_total": round(score.score_total, 2),
    }


# ─── Recomendaciones ────────────────────────────────────────────────────────

@router.get("/recomendaciones")
def get_recomendaciones(
    id_empresa: Optional[int] = Query(default=None),
    categoria: Optional[str] = Query(default=None),
    estado: Optional[str] = Query(default=None),
):
    """Obtiene las recomendaciones generadas."""
    query = "SELECT * FROM recomendaciones WHERE 1=1"
    params = []

    if id_empresa:
        query += " AND id_empresa = ?"
        params.append(id_empresa)
    if categoria:
        query += " AND categoria = ?"
        params.append(categoria)
    if estado:
        query += " AND estado = ?"
        params.append(estado)

    query += " ORDER BY prioridad DESC"

    rows = db.execute(query, tuple(params))
    return {"total": len(rows), "recomendaciones": rows}


@router.post("/recomendaciones/{id_recomendacion}/actualizar")
def actualizar_recomendacion(
    id_recomendacion: int,
    req: ActualizarRecomendacionRequest,
):
    """Actualiza el estado de una recomendación."""
    motor = get_motor()
    notas = req.notas if req.notas else ""
    ok = motor.actualizar_recomendacion(id_recomendacion, req.estado, notas)
    return {"ok": ok, "id_recomendacion": id_recomendacion}


# ─── Rankings ────────────────────────────────────────────────────────────────

@router.get("/rankings/{tipo_ranking}")
def get_ranking(
    tipo_ranking: str,
    limite: int = Query(default=20),
    periodo: str = Query(default="ultimos_6_meses"),
):
    """Obtiene un ranking específico."""
    motor = get_motor()
    ranking = motor.ranking(tipo_ranking.upper(), limite, periodo)
    return {"tipo_ranking": tipo_ranking.upper(), "total": len(ranking), "ranking": ranking}


# ─── Indicadores ────────────────────────────────────────────────────────────

@router.get("/indicadores")
def get_indicadores():
    """Obtiene los indicadores calculados."""
    motor = get_motor()
    return {
        "indicadores": [
            {"key": "OPPORTUNITY_SCORE", "nombre": "Potencial de Oportunidad", "rango": "0-100"},
            {"key": "RISK_SCORE", "nombre": "Nivel de Riesgo", "rango": "0-100 (menor es mejor)"},
            {"key": "LOYALTY_SCORE", "nombre": "Índice de Fidelidad", "rango": "0-100"},
            {"key": "GROWTH_SCORE", "nombre": "Índice de Crecimiento", "rango": "0-100"},
            {"key": "DIVERSIFICATION_SCORE", "nombre": "Índice de Diversificación", "rango": "0-100"},
            {"key": "COMPETITIVENESS_SCORE", "nombre": "Índice de Competitividad", "rango": "0-100"},
        ]
    }


@router.get("/indicadores/{id_empresa}")
def get_indicadores_empresa(
    id_empresa: int,
    periodo: str = Query(default="ultimos_6_meses"),
):
    """Obtiene los indicadores de una empresa específica."""
    motor = get_motor()
    score = motor.score_empresa(id_empresa, periodo)
    if not score:
        return {"error": "Empresa no encontrada"}, 404

    indicadores = motor.indicators_calculator.calcular_todos(id_empresa, score)
    return {"id_empresa": id_empresa, "indicadores": indicadores}


# ─── Configuración ──────────────────────────────────────────────────────────

@router.get("/config/factores")
def get_config_factores():
    """Obtiene la configuración actual de los factores del score."""
    motor = get_motor()
    factores = motor.obtener_config_factores()
    return {"factores": factores}


@router.put("/config/factores/{factor_key}")
def actualizar_peso_factor(factor_key: str, req: ActualizarPesoFactorRequest):
    """Actualiza el peso de un factor."""
    motor = get_motor()
    ok = motor.actualizar_peso_factor(factor_key, req.peso_actual)
    return {"ok": ok, "factor_key": factor_key, "nuevo_peso": req.peso_actual}


@router.get("/config/reglas")
def get_config_reglas():
    """Obtiene todas las reglas configuradas."""
    motor = get_motor()
    reglas = motor.obtener_reglas()
    return {
        "reglas": [
            {
                "regla_id": r.regla_id,
                "nombre": r.nombre,
                "descripcion": r.descripcion,
                "prioridad": r.prioridad,
                "tipo_evaluacion": r.tipo_evaluacion,
                "estado": r.estado,
                "categoria": r.categoria,
            }
            for r in reglas
        ]
    }


# ─── Cálculo Masivo ──────────────────────────────────────────────────────────

@router.post("/calcular-todo")
def calcular_todo(req: CalcularTodoRequest = CalcularTodoRequest()):
    """Calcula scores, rankings y recomendaciones para todas las empresas."""
    motor = get_motor()
    periodo = req.periodo

    # Calcular scores
    scores = motor.calcular_scores(periodo)

    # Generar rankings
    rankings = motor.generar_rankings(periodo)

    return {
        "status": "completado",
        "periodo": periodo,
        "scores_calculados": len(scores),
        "rankings": {k: len(v) for k, v in rankings.items()},
        "timestamp": datetime.now().isoformat(),
    }


# ─── Análisis Completo ───────────────────────────────────────────────────────

@router.get("/analisis/{nombre_empresa}")
def get_analisis_completo(
    nombre_empresa: str,
    periodo: str = Query(default="ultimos_6_meses"),
):
    """Obtiene el análisis comercial completo de una empresa."""
    motor = get_motor()
    resultado = motor.analisis_completo(nombre_empresa, periodo)
    return resultado.to_dict()