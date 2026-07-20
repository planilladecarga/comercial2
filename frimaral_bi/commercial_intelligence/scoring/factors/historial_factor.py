"""
=================================================================================
historial_factor.py — Factor: Historial
=================================================================================
Calculates historical relationship score and loyalty level.
"""

from __future__ import annotations

from typing import Any, Optional
from .factor_base import FactorBase
from ..models import NivelFidelidad


class HistorialFactor(FactorBase):
    """Factor de Historial: Evalúa tiempo de relación y cambios históricos."""

    def calculate(self, id_empresa: int, periodo: str = "ultimos_6_meses") -> Any:
        """
        Calculate history factor (0-100).

        Based on relationship duration.
        """
        emp = self.repo.empresa_por_id(id_empresa)
        if not emp:
            return self._create_result(
                factor_key="historial",
                factor_nombre="Historial",
                valor=0,
                peso=0,
                contribucion=0,
                detalle="Empresa no encontrada",
            )

        fecha_primera = emp.get("fecha_primera", "")
        if not fecha_primera:
            return self._create_result(
                factor_key="historial",
                factor_nombre="Historial",
                valor=30,
                peso=0,
                contribucion=0,
                detalle="Sin datos de inicio",
            )

        # Calculate months of relationship
        query = """
            SELECT
                MIN(m.fecha_movimiento) as primera_fecha,
                MAX(m.fecha_movimiento) as ultima_fecha
            FROM movimientos m
            WHERE m.empresa_id = ?
        """
        result = self.repo.execute_one(query, (id_empresa,))

        if result and result["primera_fecha"]:
            # Calculate months difference
            meses_query = """
                SELECT
                    (strftime('%Y', 'now') - strftime('%Y', ?)) * 12 +
                    (strftime('%m', 'now') - strftime('%m', ?)) as meses
            """
            meses_result = self.repo.execute_one(meses_query, (result["primera_fecha"], result["primera_fecha"]))
            meses = meses_result["meses"] if meses_result else 0
        else:
            meses = 0

        # Score based on months
        if meses <= 3:
            score = 20
        elif meses <= 6:
            score = 40
        elif meses <= 12:
            score = 60
        elif meses <= 24:
            score = 80
        else:
            score = 100

        peso = self.config.peso if self.config else 0
        contribucion = score * peso / 100 if peso > 0 else 0

        return self._create_result(
            factor_key="historial",
            factor_nombre="Historial",
            valor=score,
            peso=peso,
            contribucion=contribucion,
            comparacion_periodo=f"{meses} meses de relación",
            detalle=f"{meses} meses ({periodo})",
        )

    def calcular_fidelidad(self, id_empresa: int) -> NivelFidelidad:
        """
        Calculate loyalty level based on history and deposit changes.
        """
        # Get empresa data
        emp = self.repo.empresa_por_id(id_empresa)
        if not emp:
            return NivelFidelidad.MUY_BAJA

        # Get first and last dates
        query = """
            SELECT
                MIN(m.fecha_movimiento) as primera_fecha,
                MAX(m.fecha_movimiento) as ultima_fecha,
                COUNT(DISTINCT m.nombre_establecimiento) as cant_depositos
            FROM movimientos m
            WHERE m.empresa_id = ?
        """
        result = self.repo.execute_one(query, (id_empresa,))

        if not result or not result["primera_fecha"]:
            return NivelFidelidad.MUY_BAJA

        # Calculate months
        meses_query = """
            SELECT
                (strftime('%Y', 'now') - strftime('%Y', ?)) * 12 +
                (strftime('%m', 'now') - strftime('%m', ?)) as meses
        """
        meses_result = self.repo.execute_one(meses_query, (result["primera_fecha"], result["primera_fecha"]))
        meses = meses_result["meses"] if meses_result else 0
        cant_depositos = result["cant_depositos"] or 1

        # Determine fidelity level
        if meses <= 3:
            return NivelFidelidad.MUY_BAJA
        elif meses <= 6:
            return NivelFidelidad.BAJA
        elif meses <= 12:
            return NivelFidelidad.MEDIA
        elif meses <= 24:
            if cant_depositos == 1:
                return NivelFidelidad.ALTA
            return NivelFidelidad.ALTA
        else:
            # More than 2 years
            if cant_depositos == 1:
                return NivelFidelidad.MUY_ALTA
            elif cant_depositos <= 2:
                return NivelFidelidad.MUY_ALTA
            return NivelFidelidad.ALTA
