"""
=================================================================================
tests/test_commercial_intelligence.py — Tests para Commercial Intelligence Engine
=================================================================================
"""

import pytest
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


class TestScoringFactors:
    """Tests para los factores de scoring."""

    def test_volumen_factor_calculate(self):
        """Test que el factor de volumen calcula correctamente."""
        from frimaral_bi.commercial_intelligence.scoring.factors.volumen_factor import VolumenFactor
        from frimaral_bi.empresa360.repositorio import Repositorio

        db_path = project_root / "frimaral_bi" / "data" / "frimaral_bi.db"
        if not db_path.exists():
            pytest.skip("Database not found")

        repo = Repositorio(str(db_path))
        factor = VolumenFactor(repo)

        # Test with a real empresa
        empresas = repo.todas_empresas_id()
        if empresas:
            id_empresa = empresas[0][0]
            result = factor.calculate(id_empresa)

            assert result.factor_key == "volumen"
            assert 0 <= result.valor <= 100
            assert result.peso > 0

    def test_frecuencia_factor_calculate(self):
        """Test que el factor de frecuencia calcula correctamente."""
        from frimaral_bi.commercial_intelligence.scoring.factors.frecuencia_factor import FrecuenciaFactor
        from frimaral_bi.empresa360.repositorio import Repositorio

        db_path = project_root / "frimaral_bi" / "data" / "frimaral_bi.db"
        if not db_path.exists():
            pytest.skip("Database not found")

        repo = Repositorio(str(db_path))
        factor = FrecuenciaFactor(repo)

        empresas = repo.todas_empresas_id()
        if empresas:
            id_empresa = empresas[0][0]
            result = factor.calculate(id_empresa)

            assert result.factor_key == "frecuencia"
            assert 0 <= result.valor <= 100

    def test_crecimiento_factor_calculate(self):
        """Test que el factor de crecimiento calcula correctamente."""
        from frimaral_bi.commercial_intelligence.scoring.factors.crecimiento_factor import CrecimientoFactor
        from frimaral_bi.empresa360.repositorio import Repositorio

        db_path = project_root / "frimaral_bi" / "data" / "frimaral_bi.db"
        if not db_path.exists():
            pytest.skip("Database not found")

        repo = Repositorio(str(db_path))
        factor = CrecimientoFactor(repo)

        empresas = repo.todas_empresas_id()
        if empresas:
            id_empresa = empresas[0][0]
            result = factor.calculate(id_empresa)

            assert result.factor_key == "crecimiento"
            assert 0 <= result.valor <= 100


class TestRulesEngine:
    """Tests para el motor de reglas."""

    def test_evaluar_condicion_simple(self):
        """Test evaluación de condición simple."""
        from frimaral_bi.commercial_intelligence.rules.rules_engine import RulesEngine

        # Create mock config repo
        class MockConfigRepo:
            def obtener_todas_reglas(self):
                return []

        engine = RulesEngine(MockConfigRepo())

        # Test simple condition
        condicion = {
            "field": "score_total",
            "operator": "gt",
            "value": 50
        }

        data = {"score_total": 75}
        result = engine._evaluar_simple(condicion, data)
        assert result is True

        data = {"score_total": 30}
        result = engine._evaluar_simple(condicion, data)
        assert result is False

    def test_evaluar_condicion_and(self):
        """Test evaluación de condición AND."""
        from frimaral_bi.commercial_intelligence.rules.rules_engine import RulesEngine

        class MockConfigRepo:
            def obtener_todas_reglas(self):
                return []

        engine = RulesEngine(MockConfigRepo())

        condicion = {
            "operator": "and",
            "conditions": [
                {"field": "score_total", "operator": "gte", "value": 50},
                {"field": "factor_crecimiento", "operator": "gt", "value": 30}
            ]
        }

        data = {"score_total": 75, "factor_crecimiento": 60}
        result = engine._evaluar_condicion(condicion, data)
        assert result is True

        data = {"score_total": 30, "factor_crecimiento": 60}
        result = engine._evaluar_condicion(condicion, data)
        assert result is False

    def test_evaluar_condicion_or(self):
        """Test evaluación de condición OR."""
        from frimaral_bi.commercial_intelligence.rules.rules_engine import RulesEngine

        class MockConfigRepo:
            def obtener_todas_reglas(self):
                return []

        engine = RulesEngine(MockConfigRepo())

        condicion = {
            "operator": "or",
            "conditions": [
                {"field": "score_total", "operator": "gte", "value": 80},
                {"field": "factor_crecimiento", "operator": "gt", "value": 90}
            ]
        }

        data = {"score_total": 85, "factor_crecimiento": 30}
        result = engine._evaluar_condicion(condicion, data)
        assert result is True


class TestRiskLevels:
    """Tests para niveles de riesgo."""

    def test_risk_level_from_score(self):
        """Test determinación de nivel desde score."""
        from frimaral_bi.commercial_intelligence.risk.risk_levels import RiskLevel

        assert RiskLevel.from_score(80) == RiskLevel.BAJO
        assert RiskLevel.from_score(70) == RiskLevel.BAJO
        assert RiskLevel.from_score(60) == RiskLevel.MEDIO
        assert RiskLevel.from_score(50) == RiskLevel.MEDIO
        assert RiskLevel.from_score(40) == RiskLevel.ALTO
        assert RiskLevel.from_score(30) == RiskLevel.ALTO
        assert RiskLevel.from_score(20) == RiskLevel.CRITICO


class TestPotentialLevels:
    """Tests para niveles de potencial."""

    def test_potential_level_values(self):
        """Test valores de nivel de potencial."""
        from frimaral_bi.commercial_intelligence.opportunity.opportunity_engine import PotentialLevel

        assert PotentialLevel.MUY_ALTO.value == "MUY_ALTO"
        assert PotentialLevel.ALTO.value == "ALTO"
        assert PotentialLevel.MEDIO.value == "MEDIO"
        assert PotentialLevel.BAJO.value == "BAJO"


class TestRecommendations:
    """Tests para recomendaciones."""

    def test_recommendation_creation(self):
        """Test creación de recomendación."""
        from frimaral_bi.commercial_intelligence.recommendations.recommendation_types import Recommendation

        rec = Recommendation(
            regla_id="REC001",
            recomendacion="Test recommendation",
            prioridad=80,
            categoria="SEGUIMIENTO"
        )

        assert rec.regla_id == "REC001"
        assert rec.prioridad == 80
        assert rec.estado == "PENDIENTE"
        assert rec.fecha_generacion != ""


class TestIndicators:
    """Tests para indicadores."""

    def test_indicators_bundle_creation(self):
        """Test creación de bundle de indicadores."""
        from frimaral_bi.commercial_intelligence.indicators.indicators_calculator import IndicatorsBundle

        bundle = IndicatorsBundle(
            opportunity_score=75.5,
            risk_score=25.0,
            loyalty_score=80.0,
            growth_score=60.0,
            diversification_score=55.0,
            competitiveness_score=70.0
        )

        result = bundle.to_dict()

        assert result["OPPORTUNITY_SCORE"] == 75.5
        assert result["RISK_SCORE"] == 25.0
        assert result["LOYALTY_SCORE"] == 80.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
