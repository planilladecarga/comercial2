"""
Rutas del Centro de Comando Comercial.
"""
from fastapi import APIRouter, Query
from typing import Optional
from ..database import db
from ..services.resumen_service import resumen_service
from ..services.alertas_service import alertas_service
from ..services.oportunidades_service import oportunidades_service
from ..services.competencia_service import competencia_service
from ..services.indicadores_service import indicadores_service
from ..services.mapa_service import mapa_service
from ..services.evolucion_service import evolucion_service
from ..services.rankings_service import rankings_service
from ..services.filtros_service import filtros_service
from ..queries.comando_queries import QUERY_EMPRESA_CALIRAL

router = APIRouter()


def _get_caliral_id() -> int:
    """Obtiene el ID de CALIRAL o la primera empresa disponible."""
    row = db.execute_one(QUERY_EMPRESA_CALIRAL)
    if row:
        return row["id_empresa"]
    rows = db.execute("SELECT id_empresa FROM dim_empresas WHERE activo = 1 LIMIT 1")
    return rows[0]["id_empresa"] if rows else 1


@router.get("/resumen")
def get_resumen():
    """Módulo 1 - Resumen Ejecutivo."""
    return resumen_service.obtener_resumen()


@router.get("/alertas")
def get_alertas(id_empresa: Optional[int] = Query(default=None)):
    """Módulo 2 - Alertas del Día."""
    empresa_id = id_empresa or _get_caliral_id()
    return alertas_service.obtener_alertas(empresa_id)


@router.get("/oportunidades")
def get_oportunidades(id_empresa: Optional[int] = Query(default=None)):
    """Módulo 3 - Oportunidades."""
    empresa_id = id_empresa or _get_caliral_id()
    return oportunidades_service.obtener_oportunidades(empresa_id)


@router.get("/competencia")
def get_competencia(id_a: int = Query(default=None), id_b: int = Query(default=None)):
    """Módulo 4 - Comparación Competitiva."""
    empresa_a = id_a or _get_caliral_id()
    empresa_b = id_b or 2
    return competencia_service.comparar(empresa_a, empresa_b)


@router.get("/competencia/empresas")
def get_empresas_comparables():
    """Lista empresas disponibles para comparar."""
    return competencia_service.listar_empresas()


@router.get("/indicadores")
def get_indicadores(id_empresa: Optional[int] = Query(default=None)):
    """Módulo 5 - Indicadores KPIs."""
    empresa_id = id_empresa or _get_caliral_id()
    return indicadores_service.obtener_indicadores(empresa_id)


@router.get("/mapa")
def get_mapa():
    """Módulo 6 - Mapa Comercial."""
    return mapa_service.obtener_mapa()


@router.get("/evolucion")
def get_evolucion():
    """Módulo 7 - Evolución."""
    return evolucion_service.obtener_evolucion()


@router.get("/rankings")
def get_rankings():
    """Módulo 8 - Top Rankings."""
    return rankings_service.obtener_rankings()


@router.get("/filtros")
def get_filtros():
    """Filtros globales disponibles."""
    return filtros_service.obtener_filtros()


@router.get("/completo")
def get_completo(id_empresa: Optional[int] = Query(default=None)):
    """Retorna todos los datos del centro de comando en una sola llamada."""
    empresa_id = id_empresa or _get_caliral_id()

    return {
        "resumen": resumen_service.obtener_resumen(),
        "alertas": alertas_service.obtener_alertas(empresa_id),
        "oportunidades": oportunidades_service.obtener_oportunidades(empresa_id),
        "competencia": competencia_service.comparar(empresa_id, empresa_id + 1) if empresa_id else None,
        "indicadores": indicadores_service.obtener_indicadores(empresa_id),
        "mapa": mapa_service.obtener_mapa(),
        "evolucion": evolucion_service.obtener_evolucion(),
        "rankings": rankings_service.obtener_rankings(),
        "filtros": filtros_service.obtener_filtros(),
    }
