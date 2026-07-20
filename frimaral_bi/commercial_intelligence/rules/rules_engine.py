"""
=================================================================================
rules_engine.py — Motor de Evaluación de Reglas
=================================================================================
"""

from __future__ import annotations

import json
from typing import Any, Optional

from .rule import Rule


class RulesEngine:
    """
    Motor de reglas configurables.

    Evalúa condiciones JSON contra datos de la empresa y genera
    recomendaciones basadas en reglas activas.
    """

    # Operadores disponibles
    OPERATORS = {
        "gt": lambda a, b: a > b,
        "gte": lambda a, b: a >= b,
        "lt": lambda a, b: a < b,
        "lte": lambda a, b: a <= b,
        "eq": lambda a, b: a == b,
        "neq": lambda a, b: a != b,
        "in": lambda a, b: a in b,
        "not_in": lambda a, b: a not in b,
        "between": lambda a, b: b[0] <= a <= b[1],
        "contains": lambda a, b: b in str(a),
    }

    def __init__(self, config_repo: Any):
        """
        Inicializa el motor de reglas.

        Args:
            config_repo: Repositorio de configuración
        """
        self.config_repo = config_repo
        self._rules_cache: Optional[list[Rule]] = None

    def get_active_rules(self) -> list[Rule]:
        """Obtiene las reglas activas."""
        if self._rules_cache is None:
            rules_data = self.config_repo.obtener_todas_reglas()
            self._rules_cache = []
            for r in rules_data:
                try:
                    condicion = json.loads(r.condicion_json) if isinstance(r.condicion_json, str) else r.condicion_json
                    recomendacion = json.loads(r.recomendacion_json) if isinstance(r.recomendacion_json, str) else r.recomendacion_json
                    rule = Rule(
                        regla_id=r.regla_id,
                        nombre=r.nombre,
                        descripcion=r.descripcion or "",
                        prioridad=r.prioridad,
                        tipo_evaluacion=r.tipo_evaluacion,
                        condicion=condicion,
                        recomendacion=recomendacion,
                        estado=bool(r.estado),
                        categoria=r.categoria or "SEGUIMIENTO",
                    )
                    self._rules_cache.append(rule)
                except Exception:
                    continue
        return [r for r in self._rules_cache if r.is_active()]

    def evaluar_regla(self, rule: Rule, data: dict[str, Any]) -> bool:
        """
        Evalúa si una regla se cumple para los datos dados.

        Args:
            rule: Regla a evaluar
            data: Datos de la empresa

        Returns:
            True si la condición se cumple
        """
        return self._evaluar_condicion(rule.condicion, data)

    def _evaluar_condicion(self, condicion: dict[str, Any], data: dict[str, Any]) -> bool:
        """
        Evalúa recursively una condición.

        Args:
            condicion: Condición JSON
            data: Datos a evaluar

        Returns:
            True si la condición se cumple
        """
        if not condicion:
            return True

        operator = condicion.get("operator", "and").lower()
        conditions = condicion.get("conditions", [])

        if operator == "and":
            return all(self._evaluar_condicion(c, data) for c in conditions)
        elif operator == "or":
            return any(self._evaluar_condicion(c, data) for c in conditions)
        elif operator == "not":
            return not self._evaluar_condicion(conditions[0], data) if conditions else True
        else:
            # Simple condition
            return self._evaluar_simple(condicion, data)

    def _evaluar_simple(self, condicion: dict[str, Any], data: dict[str, Any]) -> bool:
        """
        Evalúa una condición simple.

        Args:
            condicion: Condición simple
            data: Datos

        Returns:
            True si se cumple
        """
        field = condicion.get("field", "")
        op = condicion.get("operator", "eq")
        value = condicion.get("value")

        # Obtener valor del campo (soporta dot notation)
        field_value = self._get_nested_value(data, field)

        # Evaluar
        op_func = self.OPERATORS.get(op)
        if not op_func:
            return False

        try:
            return op_func(field_value, value)
        except (TypeError, ValueError):
            return False

    def _get_nested_value(self, data: dict[str, Any], field: str) -> Any:
        """Obtiene valor anidado usando dot notation."""
        keys = field.split(".")
        value = data
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key, None)
            else:
                return None
        return value

    def evaluar_reglas_por_tipo(
        self,
        tipo: str,
        data: dict[str, Any]
    ) -> list[Rule]:
        """
        Obtiene las reglas activas de un tipo específico que se cumplen.

        Args:
            tipo: Tipo de evaluación (SCORE, RIESGO, etc.)
            data: Datos de la empresa

        Returns:
            Lista de reglas que se cumplen
        """
        rules = self.get_active_rules()
        matched = []

        for rule in rules:
            if rule.tipo_evaluacion == tipo:
                if self.evaluar_regla(rule, data):
                    matched.append(rule)

        # Ordenar por prioridad
        matched.sort(key=lambda r: r.prioridad, reverse=True)
        return matched

    def invalidate_cache(self) -> None:
        """Invalida el caché de reglas."""
        self._rules_cache = None
