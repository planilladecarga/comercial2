"""
=================================================================================
config_repository.py — Repositorio de Configuración
=================================================================================
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional
from dataclasses import dataclass

from ...database import db


@dataclass
class FactorConfigRow:
    """Representa una fila de configuración de factor."""
    id_config: int
    factor_key: str
    factor_nombre: str
    peso_default: float
    peso_actual: float
    peso_min: float
    peso_max: float
    activo: bool


@dataclass
class RuleConfigRow:
    """Representa una fila de configuración de regla."""
    id_regla: int
    regla_id: str
    nombre: str
    descripcion: Optional[str]
    prioridad: int
    tipo_evaluacion: str
    condicion_json: str
    recomendacion_json: str
    estado: bool
    categoria: Optional[str]


class ConfigRepository:
    """
    Repositorio de configuración para el Commercial Intelligence Engine.

    Gestiona la configuración de factores y reglas en la base de datos.
    """

    def __init__(self, db_path: str = "data/frimaral_bi.db"):
        """
        Inicializa el repositorio.

        Args:
            db_path: Ruta a la base de datos
        """
        if not Path(db_path).is_absolute():
            db_path = str(Path(__file__).parent.parent.parent.parent / db_path)
        self.db_path = db_path

    # ─── Factores ─────────────────────────────────────────────────────────

    def obtener_todos_factores(self) -> list[FactorConfigRow]:
        """
        Obtiene todos los factores configurados.

        Returns:
            Lista de FactorConfigRow
        """
        rows = db.execute("SELECT * FROM config_scores ORDER BY factor_key")
        return [FactorConfigRow(**row) for row in rows]

    def obtener_factor(self, factor_key: str) -> Optional[FactorConfigRow]:
        """
        Obtiene un factor específico.

        Args:
            factor_key: Clave del factor

        Returns:
            FactorConfigRow o None
        """
        row = db.execute_one(
            "SELECT * FROM config_scores WHERE factor_key = ?",
            (factor_key,)
        )
        return FactorConfigRow(**row) if row else None

    def actualizar_peso_factor(self, factor_key: str, nuevo_peso: float) -> bool:
        """
        Actualiza el peso de un factor.

        Args:
            factor_key: Clave del factor
            nuevo_peso: Nuevo peso

        Returns:
            True si se actualizó correctamente
        """
        from datetime import datetime

        # Validar que esté dentro del rango
        factor = self.obtener_factor(factor_key)
        if not factor:
            return False

        nuevo_peso = max(factor.peso_min, min(factor.peso_max, nuevo_peso))

        db.execute(
            """UPDATE config_scores
               SET peso_actual = ?, fecha_modificacion = ?
               WHERE factor_key = ?""",
            (nuevo_peso, datetime.now().isoformat(), factor_key)
        )
        return True

    # ─── Reglas ───────────────────────────────────────────────────────────

    def obtener_todas_reglas(self) -> list[RuleConfigRow]:
        """
        Obtiene todas las reglas configuradas.

        Returns:
            Lista de RuleConfigRow
        """
        rows = db.execute("SELECT * FROM config_reglas ORDER BY prioridad DESC")
        return [RuleConfigRow(**row) for row in rows]

    def obtener_regla(self, regla_id: str) -> Optional[RuleConfigRow]:
        """
        Obtiene una regla específica.

        Args:
            regla_id: ID de la regla

        Returns:
            RuleConfigRow o None
        """
        row = db.execute_one(
            "SELECT * FROM config_reglas WHERE regla_id = ?",
            (regla_id,)
        )
        return RuleConfigRow(**row) if row else None

    def actualizar_estado_regla(self, regla_id: str, activo: bool) -> bool:
        """
        Activa o desactiva una regla.

        Args:
            regla_id: ID de la regla
            activo: Estado (True=activa, False=inactiva)

        Returns:
            True si se actualizó correctamente
        """
        db.execute(
            "UPDATE config_reglas SET estado = ? WHERE regla_id = ?",
            (1 if activo else 0, regla_id)
        )
        return True

    def obtener_reglas_por_categoria(self, categoria: str) -> list[RuleConfigRow]:
        """
        Obtiene reglas de una categoría específica.

        Args:
            categoria: Categoría (CAPTACION, RETENCION, etc.)

        Returns:
            Lista de RuleConfigRow
        """
        rows = db.execute(
            "SELECT * FROM config_reglas WHERE categoria = ? ORDER BY prioridad DESC",
            (categoria,)
        )
        return [RuleConfigRow(**row) for row in rows]
