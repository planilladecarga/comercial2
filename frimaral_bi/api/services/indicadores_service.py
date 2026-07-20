"""
Servicio de Indicadores KPIs - Módulo 5.
Calcula los índices clave del negocio.
"""
from ..database import db
from ..queries.comando_queries import (
    QUERY_INDICADORES_PARTICIPACION,
    QUERY_INDICADORES_DIVERSIFICACION,
    QUERY_INDICADORES_CONCENTRACION,
    QUERY_INDICADORES_FIDELIDAD,
    QUERY_INDICADORES_CRECIMIENTO,
    QUERY_EMPRESA_CALIRAL,
)


class KPI:
    def __init__(self, codigo: str, nombre: str, valor: float, unidad: str, estado: str, tendencia: str, detalle: str):
        self.codigo = codigo
        self.nombre = nombre
        self.valor = valor
        self.unidad = unidad
        self.estado = estado
        self.tendencia = tendencia
        self.detalle = detalle

    def to_dict(self) -> dict:
        return {
            "codigo": self.codigo,
            "nombre": self.nombre,
            "valor": self.valor,
            "unidad": self.unidad,
            "estado": self.estado,
            "tendencia": self.tendencia,
            "detalle": self.detalle,
        }


class IndicadoresService:
    """Calcula los KPIs del Centro de Comando."""

    def obtener_indicadores(self, id_empresa: int) -> dict:
        """Retorna todos los indicadores KPIs."""
        participacion = self._indice_participacion(id_empresa)
        diversificacion = self._indice_diversificacion()
        riesgo = self._indice_riesgo(id_empresa)
        fidelidad = self._indice_fidelidad(id_empresa)
        crecimiento = self._indice_crecimiento(id_empresa)
        oportunidad = self._indice_oportunidad(id_empresa)

        return {
            "indice_diversificacion": participacion,
            "indice_riesgo": riesgo,
            "indice_competencia": diversificacion,
            "indice_fidelidad": fidelidad,
            "indice_crecimiento": crecimiento,
            "indice_oportunidad": oportunidad,
        }

    def _indice_participacion(self, id_empresa: int) -> dict:
        row = db.execute_one(QUERY_INDICADORES_PARTICIPACION, (id_empresa,))
        valor = row["participacion"] if row else 0.0
        estado = "ok" if valor >= 20 else "advertencia" if valor >= 10 else "critico"
        return KPI(
            codigo="IND001",
            nombre="Índice Participación",
            valor=valor,
            unidad="%",
            estado=estado,
            tendencia="up" if valor > 20 else "stable",
            detalle=f"Participación en el mercado total: {valor:.2f}%",
        ).to_dict()

    def _indice_diversificacion(self) -> dict:
        row = db.execute_one(QUERY_INDICADORES_DIVERSIFICACION)
        valor = row["indice_diversificacion"] if row else 0.0
        estado = "ok" if valor >= 5000 else "advertencia" if valor >= 3000 else "critico"
        return KPI(
            codigo="IND002",
            nombre="Índice Diversificación",
            valor=valor,
            unidad="indice",
            estado=estado,
            tendencia="up" if valor >= 5000 else "down",
            detalle=f"Diversificación del mercado (0-10000, mayor es mejor)",
        ).to_dict()

    def _indice_riesgo(self, id_empresa: int) -> dict:
        row = db.execute_one(QUERY_INDICADORES_CONCENTRACION, (id_empresa, id_empresa))
        concentracion = row["concentracion"] if row else 0.0
        # Índice de riesgo = 100 - concentración (inverso)
        valor = max(0, 100 - concentracion)
        estado = "ok" if valor >= 50 else "advertencia" if valor >= 30 else "critico"
        return KPI(
            codigo="IND003",
            nombre="Índice Riesgo",
            valor=valor,
            unidad="%",
            estado=estado,
            tendencia="up" if valor >= 50 else "down",
            detalle=f"Menor concentración = menor riesgo (concentración actual: {concentracion:.1f}%)",
        ).to_dict()

    def _indice_fidelidad(self, id_empresa: int) -> dict:
        row = db.execute_one(QUERY_INDICADORES_FIDELIDAD, (id_empresa,))
        valor = row["indice_fidelidad"] if row else 0.0
        estado = "ok" if valor >= 50 else "advertencia" if valor >= 30 else "critico"
        return KPI(
            codigo="IND004",
            nombre="Índice Fidelidad",
            valor=valor,
            unidad="%",
            estado=estado,
            tendencia="up" if valor >= 50 else "down",
            detalle=f"Productores exclusivos: {valor:.1f}%",
        ).to_dict()

    def _indice_crecimiento(self, id_empresa: int) -> dict:
        row = db.execute_one(QUERY_INDICADORES_CRECIMIENTO, (id_empresa, id_empresa, id_empresa, id_empresa, id_empresa, id_empresa))
        if not row or row["kg_anterior"] == 0:
            valor = 0.0
        else:
            valor = row["crecimiento_pct"] if row else 0.0
        estado = "ok" if valor >= 0 else "advertencia" if valor >= -10 else "critico"
        tendencia = "up" if valor > 0 else "down" if valor < 0 else "stable"
        return KPI(
            codigo="IND005",
            nombre="Índice Crecimiento",
            valor=valor,
            unidad="%",
            estado=estado,
            tendencia=tendencia,
            detalle=f"Crecimiento vs mes anterior: {valor:+.1f}%",
        ).to_dict()

    def _indice_oportunidad(self, id_empresa: int) -> dict:
        # Oportunidad = potencial de mercados no explorados
        # Simplificado: 0-100 basado en diversificación
        row_div = db.execute_one(QUERY_INDICADORES_DIVERSIFICACION)
        diversificacion = row_div["indice_diversificacion"] if row_div else 0.0
        valor = min(100, diversificacion / 100)  # Normalizado a 0-100
        estado = "ok" if valor >= 50 else "advertencia" if valor >= 25 else "critico"
        return KPI(
            codigo="IND006",
            nombre="Índice Oportunidad",
            valor=valor,
            unidad="indice",
            estado=estado,
            tendencia="up" if valor >= 50 else "down",
            detalle=f"Potencial de diversificación: {valor:.0f}/100",
        ).to_dict()


indicadores_service = IndicadoresService()
