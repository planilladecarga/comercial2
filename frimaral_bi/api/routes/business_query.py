"""
BusinessQueryRoutes - Rutas API del Motor de Consultas
"""
from fastapi import APIRouter, Query, Body
from typing import Optional
from pydantic import BaseModel
from ..business_query.service import service

router = APIRouter()


class EjecutarRequest(BaseModel):
    consulta_id: str
    parametros: dict = {}
    usuario: str = "system"


@router.get("/catalogo")
def get_catalogo():
    """Lista todas las consultas disponibles."""
    return service.listar_catalogo()


@router.get("/categorias")
def get_categorias():
    """Lista categorías disponibles."""
    return service.listar_categorias()


@router.get("/opciones")
def get_opciones():
    """Opciones dinámicas para los parámetros select."""
    return service.obtener_opciones_dinamicas()


@router.post("/ejecutar")
def ejecutar_consulta(req: EjecutarRequest):
    """Ejecuta una consulta y retorna resultado completo."""
    resultado = service.ejecutar(
        consulta_id=req.consulta_id,
        parametros=req.parametros,
        usuario=req.usuario,
    )
    if resultado is None:
        return {"error": "Consulta no encontrada"}, 404
    return resultado.to_dict()


@router.get("/historial")
def get_historial(limite: int = Query(default=50)):
    """Obtiene el historial de consultas."""
    return service.obtener_historial(limite)


@router.get("/favoritos")
def get_favoritos():
    """Obtiene favoritos."""
    return service.obtener_favoritos()


@router.post("/favoritos")
def crear_favorito(
    consulta_id: str = Body(...),
    consulta_nombre: str = Body(...),
    parametros: dict = Body(default={}),
    nombre_custom: Optional[str] = Body(default=None),
):
    """Guarda una consulta como favorita."""
    fid = service.guardar_favorito(consulta_id, consulta_nombre, parametros, nombre_custom)
    return {"id": fid, "status": "ok"}


@router.delete("/favoritos/{favorito_id}")
def eliminar_favorito(favorito_id: int):
    """Elimina un favorito."""
    ok = service.eliminar_favorito(favorito_id)
    return {"deleted": ok}
