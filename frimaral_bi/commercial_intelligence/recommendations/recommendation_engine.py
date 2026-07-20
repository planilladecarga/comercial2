"""
=================================================================================
recommendation_engine.py — Motor de Recomendaciones
=================================================================================
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, TYPE_CHECKING

from .recommendation_types import Recommendation
from ..rules.rules_engine import RulesEngine

if TYPE_CHECKING:
    from ..scoring.models import ScoreResult


class RecommendationEngine:
    """
    Motor de generación de recomendaciones.

    Usa el RulesEngine para evaluar condiciones y genera
    recomendaciones accionables para el equipo comercial.
    """

    def __init__(self, rules_engine: RulesEngine):
        """
        Inicializa el motor de recomendaciones.

        Args:
            rules_engine: Motor de reglas
        """
        self.rules_engine = rules_engine

    def generar(
        self,
        id_empresa: int,
        score_result: "ScoreResult",
        indicadores: dict[str, Any]
    ) -> list[Recommendation]:
        """
        Genera recomendaciones para una empresa.

        Args:
            id_empresa: ID de la empresa
            score_result: Resultado del scoring
            indicadores: Indicadores básicos

        Returns:
            Lista de recomendaciones generadas
        """
        from ...api.database import db

        recomendaciones = []

        # Preparar datos para evaluación
        data = self._preparar_datos(id_empresa, score_result, indicadores)

        # Evaluar reglas por tipo
        tipos = ["SCORE", "RIESGO", "CRECIMIENTO", "FRECUENCIA", "VOLUMEN", "DIVERSIFICACION", "FIDELIDAD"]

        for tipo in tipos:
            reglas = self.rules_engine.evaluar_reglas_por_tipo(tipo, data)
            for rule in reglas:
                rec = self._crear_recomendacion(rule, id_empresa)
                recomendaciones.append(rec)

        # Guardar en BD
        self._guardar_recomendaciones(id_empresa, recomendaciones)

        # Ordenar por prioridad
        recomendaciones.sort(key=lambda r: r.prioridad, reverse=True)

        return recomendaciones

    def _preparar_datos(
        self,
        id_empresa: int,
        score_result: "ScoreResult",
        indicadores: dict[str, Any]
    ) -> dict[str, Any]:
        """Prepara el diccionario de datos para evaluación de reglas."""
        data = {
            "id_empresa": id_empresa,
            "score_total": score_result.score_total if score_result else 0,
            "nivel": score_result.breakdown.nivel if score_result and score_result.breakdown else "UNKNOWN",
            **indicadores,
        }

        # Agregar factores del breakdown si existe
        if score_result and score_result.breakdown:
            for factor in score_result.breakdown.factores:
                data[f"factor_{factor.factor_key}"] = factor.valor

        return data

    def _crear_recomendacion(self, rule: Any, id_empresa: int) -> Recommendation:
        """Crea una recomendación desde una regla."""
        recomendacion_text = rule.recomendacion.get("texto", rule.nombre)

        return Recommendation(
            regla_id=rule.regla_id,
            recomendacion=recomendacion_text,
            prioridad=rule.prioridad,
            categoria=rule.categoria,
            estado="PENDIENTE",
            fecha_generacion=datetime.now().isoformat(),
            detalle=rule.descripcion or "",
        )

    def _guardar_recomendaciones(
        self,
        id_empresa: int,
        recomendaciones: list[Recommendation]
    ) -> None:
        """Guarda las recomendaciones en la base de datos."""
        from ...api.database import db

        for rec in recomendaciones:
            db.execute(
                """INSERT INTO recomendaciones
                   (id_empresa, regla_id, recomendacion, prioridad, categoria, estado, fecha_generacion)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (id_empresa, rec.regla_id, rec.recomendacion, rec.prioridad,
                 rec.categoria, rec.estado, rec.fecha_generacion)
            )

    def obtener_recomendaciones_empresa(
        self,
        id_empresa: int,
        estado: str = None
    ) -> list[Recommendation]:
        """
        Obtiene recomendaciones guardadas para una empresa.

        Args:
            id_empresa: ID de la empresa
            estado: Filtrar por estado (opcional)

        Returns:
            Lista de recomendaciones
        """
        from ...api.database import db

        if estado:
            rows = db.execute(
                """SELECT id_recomendacion, regla_id, recomendacion, prioridad,
                          categoria, estado, fecha_generacion
                   FROM recomendaciones
                   WHERE id_empresa = ? AND estado = ?
                   ORDER BY prioridad DESC""",
                (id_empresa, estado)
            )
        else:
            rows = db.execute(
                """SELECT id_recomendacion, regla_id, recomendacion, prioridad,
                          categoria, estado, fecha_generacion
                   FROM recomendaciones
                   WHERE id_empresa = ?
                   ORDER BY prioridad DESC""",
                (id_empresa,)
            )

        return [
            Recommendation(
                id=r["id_recomendacion"],
                regla_id=r["regla_id"],
                recomendacion=r["recomendacion"],
                prioridad=r["prioridad"],
                categoria=r["categoria"],
                estado=r["estado"],
                fecha_generacion=r["fecha_generacion"],
            )
            for r in rows
        ]
