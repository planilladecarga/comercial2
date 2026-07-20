"""
=================================================================================
factor_base.py — Base class for all scoring factors
=================================================================================
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Optional

from ..models import FactorResult


@dataclass
class FactorConfig:
    """Configuration for a scoring factor."""
    factor_key: str
    factor_nombre: str
    peso: float = 0.0
    peso_min: float = 0.0
    peso_max: float = 100.0
    activo: bool = True


class FactorBase(ABC):
    """
    Base class for all scoring factors.

    Each factor must implement:
    - calculate(): Returns FactorResult with value 0-100
    """

    def __init__(self, repo, config: Optional[FactorConfig] = None):
        self.repo = repo
        self.config = config

    @abstractmethod
    def calculate(self, id_empresa: int, periodo: str = "ultimos_6_meses") -> FactorResult:
        """
        Calculate the factor value for an empresa.

        Args:
            id_empresa: ID of the empresa
            periodo: Evaluation period

        Returns:
            FactorResult with value between 0-100
        """
        pass

    def _create_result(
        self,
        factor_key: str,
        factor_nombre: str,
        valor: float,
        peso: float,
        contribucion: float,
        comparacion_periodo: str = "",
        detalle: str = "",
    ) -> FactorResult:
        """Helper to create a FactorResult."""
        return FactorResult(
            factor_key=factor_key,
            factor_nombre=factor_nombre,
            valor=max(0, min(100, valor)),  # Clamp to 0-100
            peso=peso,
            contribucion=contribucion,
            comparacion_periodo=comparacion_periodo,
            detalle=detalle,
        )

    def _query_movimientos(
        self,
        id_empresa: int,
        meses: int = 6,
    ) -> list[dict[str, Any]]:
        """Query movimientos for an empresa within a period."""
        query = """
            SELECT
                m.fecha_movimiento,
                m.kilos_netos,
                m.tipo_movimiento,
                m.destino,
                e.nombre_unif AS empresa,
                p.nombre_producto AS producto
            FROM movimientos m
            LEFT JOIN dim_empresas e ON m.empresa_id = e.id_empresa
            LEFT JOIN dim_productos p ON m.producto_id = p.id_producto
            WHERE m.empresa_id = ?
              AND m.fecha_movimiento >= date('now', ?)
            ORDER BY m.fecha_movimiento DESC
        """
        offset = f"-{meses} months"
        return self.repo.execute(query, (id_empresa, offset))

    def _query_movimientos_anterior(
        self,
        id_empresa: int,
        meses: int = 6,
    ) -> list[dict[str, Any]]:
        """Query movimientos for the previous period."""
        query = """
            SELECT
                m.fecha_movimiento,
                m.kilos_netos,
                m.tipo_movimiento
            FROM movimientos m
            WHERE m.empresa_id = ?
              AND m.fecha_movimiento >= date('now', ?)
              AND m.fecha_movimiento < date('now', ?)
            ORDER BY m.fecha_movimiento DESC
        """
        return self.repo.execute(query, (id_empresa, f"-{meses * 2} months", f"-{meses} months"))

    def _kg_total(self, movimientos: list[dict]) -> float:
        """Calculate total kg from movimientos."""
        return sum(m.get("kilos_netos", 0) or 0 for m in movimientos)

    def _unique_count(self, movimientos: list[dict], field: str) -> int:
        """Count unique values of a field in movimientos."""
        values = set()
        for m in movimientos:
            val = m.get(field)
            if val:
                values.add(val)
        return len(values)

    def _periodo_a_meses(self, periodo: str) -> int:
        """Convert period string to months."""
        mapping = {
            "ultimo_mes": 1,
            "ultimos_3_meses": 3,
            "ultimos_6_meses": 6,
            "ultimo_anio": 12,
            "ultimos_2_anios": 24,
        }
        return mapping.get(periodo, 6)
