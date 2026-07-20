"""
=================================================================================
scoring_service.py — Servicio principal de Scoring
=================================================================================
Orchestrates all factors to calculate the commercial score.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from empresa360.repositorio import Repositorio
from .models import ScoreResult, ScoreBreakdown, FactorResult
from .factors.factor_base import FactorConfig
from .factors.volumen_factor import VolumenFactor
from .factors.frecuencia_factor import FrecuenciaFactor
from .factors.crecimiento_factor import CrecimientoFactor
from .factors.caida_factor import CaidaFactor
from .factors.mercado_div_factor import MercadoDivFactor
from .factors.producto_div_factor import ProductoDivFactor
from .factors.depositos_factor import DepositosFactor
from .factors.certificadores_factor import CertificadoresFactor
from .factors.estabilidad_factor import EstabilidadFactor
from .factors.historial_factor import HistorialFactor


class ScoringService:
    """
    Servicio de Scoring Comercial.

    Calcula el Score Comercial (0-100) para cada empresa basándose en
    múltiples factores configurables.
    """

    def __init__(self, config_repo: Any):
        """
        Inicializa el servicio de scoring.

        Args:
            config_repo: Repositorio de configuración
        """
        self.config_repo = config_repo
        self.repo = Repositorio(config_repo.db_path)

        # Inicializar factores
        self._init_factores()

    def _init_factores(self) -> None:
        """Inicializa todos los factores con su configuración."""
        # Cargar configuración de factores
        factores_config = self.config_repo.obtener_todos_factores()
        config_dict = {f["factor_key"]: f for f in factores_config}

        # Factor: Volumen
        vol_config = config_dict.get("volumen")
        self.volumen_factor = VolumenFactor(
            self.repo,
            FactorConfig(
                factor_key="volumen",
                factor_nombre="Volumen Total",
                peso=vol_config["peso_actual"] if vol_config else 20,
            ) if vol_config else None
        )

        # Factor: Frecuencia
        freq_config = config_dict.get("frecuencia")
        self.frecuencia_factor = FrecuenciaFactor(
            self.repo,
            FactorConfig(
                factor_key="frecuencia",
                factor_nombre="Frecuencia de Movimientos",
                peso=freq_config["peso_actual"] if freq_config else 15,
            ) if freq_config else None
        )

        # Factor: Crecimiento
        crec_config = config_dict.get("crecimiento")
        self.crecimiento_factor = CrecimientoFactor(
            self.repo,
            FactorConfig(
                factor_key="crecimiento",
                factor_nombre="Crecimiento",
                peso=crec_config["peso_actual"] if crec_config else 20,
            ) if crec_config else None
        )

        # Factor: Caída
        caida_config = config_dict.get("caida")
        self.caida_factor = CaidaFactor(
            self.repo,
            FactorConfig(
                factor_key="caida",
                factor_nombre="Caída / Estabilidad",
                peso=caida_config["peso_actual"] if caida_config else 15,
            ) if caida_config else None
        )

        # Factor: Diversificación Mercados
        mkt_config = config_dict.get("mercado_div")
        self.mercado_div_factor = MercadoDivFactor(
            self.repo,
            FactorConfig(
                factor_key="mercado_div",
                factor_nombre="Diversificación de Mercados",
                peso=mkt_config["peso_actual"] if mkt_config else 10,
            ) if mkt_config else None
        )

        # Factor: Diversificación Productos
        prod_config = config_dict.get("producto_div")
        self.producto_div_factor = ProductoDivFactor(
            self.repo,
            FactorConfig(
                factor_key="producto_div",
                factor_nombre="Diversificación de Productos",
                peso=prod_config["peso_actual"] if prod_config else 10,
            ) if prod_config else None
        )

        # Factor: Depósitos
        dep_config = config_dict.get("depositos")
        self.depositos_factor = DepositosFactor(
            self.repo,
            FactorConfig(
                factor_key="depositos",
                factor_nombre="Cantidad de Depósitos",
                peso=dep_config["peso_actual"] if dep_config else 5,
            ) if dep_config else None
        )

        # Factor: Certificadores
        cert_config = config_dict.get("certificadores")
        self.certificadores_factor = CertificadoresFactor(
            self.repo,
            FactorConfig(
                factor_key="certificadores",
                factor_nombre="Cantidad de Certificadores",
                peso=cert_config["peso_actual"] if cert_config else 5,
            ) if cert_config else None
        )

        # Factor: Estabilidad
        self.estabilidad_factor = EstabilidadFactor(self.repo)

        # Factor: Historial
        self.historial_factor = HistorialFactor(self.repo)

    def calcular_score(
        self,
        id_empresa: int,
        periodo: str = "ultimos_6_meses"
    ) -> ScoreResult:
        """
        Calcula el score comercial para una empresa.

        Args:
            id_empresa: ID de la empresa
            periodo: Período de evaluación

        Returns:
            ScoreResult con el score total y breakdown
        """
        # Get empresa info
        emp = self.repo.empresa_por_id(id_empresa)
        if not emp:
            return ScoreResult(
                id_empresa=id_empresa,
                nombre_empresa="DESCONOCIDA",
                score_total=0,
            )

        nombre = emp.get("nombre_unif", "SIN NOMBRE")
        tipo = emp.get("tipo_principal", "PRODUCTOR")

        # Calcular cada factor
        factores = []
        total_score = 0.0
        total_peso = 0.0

        # Volumen
        try:
            r = self.volumen_factor.calculate(id_empresa, periodo)
            factores.append(r)
            total_score += r.contribucion
            total_peso += r.peso
        except Exception:
            pass

        # Frecuencia
        try:
            r = self.frecuencia_factor.calculate(id_empresa, periodo)
            factores.append(r)
            total_score += r.contribucion
            total_peso += r.peso
        except Exception:
            pass

        # Crecimiento
        try:
            r = self.crecimiento_factor.calculate(id_empresa, periodo)
            factores.append(r)
            total_score += r.contribucion
            total_peso += r.peso
        except Exception:
            pass

        # Caída
        try:
            r = self.caida_factor.calculate(id_empresa, periodo)
            factores.append(r)
            total_score += r.contribucion
            total_peso += r.peso
        except Exception:
            pass

        # Diversificación Mercados
        try:
            r = self.mercado_div_factor.calculate(id_empresa, periodo)
            factores.append(r)
            total_score += r.contribucion
            total_peso += r.peso
        except Exception:
            pass

        # Diversificación Productos
        try:
            r = self.producto_div_factor.calculate(id_empresa, periodo)
            factores.append(r)
            total_score += r.contribucion
            total_peso += r.peso
        except Exception:
            pass

        # Depósitos
        try:
            r = self.depositos_factor.calculate(id_empresa, periodo)
            factores.append(r)
            total_score += r.contribucion
            total_peso += r.peso
        except Exception:
            pass

        # Certificadores
        try:
            r = self.certificadores_factor.calculate(id_empresa, periodo)
            factores.append(r)
            total_score += r.contribucion
            total_peso += r.peso
        except Exception:
            pass

        # Normalizar score si hay pesos
        if total_peso > 0:
            score_total = (total_score / total_peso) * 100
        else:
            score_total = 50  # Default

        # Determinar nivel
        nivel = self._determinar_nivel(score_total)

        # Crear breakdown
        breakdown = ScoreBreakdown(
            score_total=score_total,
            nivel=nivel,
            factores=factores,
            fecha_calculo=datetime.now().isoformat(),
            periodo_evaluado=periodo,
        )

        return ScoreResult(
            id_empresa=id_empresa,
            nombre_empresa=nombre,
            tipo_empresa=tipo,
            score_total=score_total,
            breakdown=breakdown,
        )

    def _determinar_nivel(self, score: float) -> str:
        """Determina el nivel según el score."""
        if score >= 80:
            return "EXCELENTE"
        elif score >= 70:
            return "MUY_BUENO"
        elif score >= 60:
            return "BUENO"
        elif score >= 50:
            return "REGULAR"
        elif score >= 30:
            return "MALO"
        else:
            return "CRITICO"

    def recalcular_factores(self) -> None:
        """Recarga la configuración de factores."""
        self._init_factores()
