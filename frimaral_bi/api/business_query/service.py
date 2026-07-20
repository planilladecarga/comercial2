"""
BusinessQueryService - Lógica de negocio del motor de consultas
"""
import time
from datetime import datetime
from typing import Optional
from .catalog import CONSULTAS_CATALOGO, get_consulta_por_id, CATEGORIAS
from .dto import QueryResultado
from .repository import repo


class BusinessQueryService:
    """Servicio principal del motor de consultas."""

    def listar_catalogo(self) -> list[dict]:
        """Retorna el catálogo completo de consultas."""
        return [
            {
                "id": q.id,
                "nombre": q.nombre,
                "descripcion": q.descripcion,
                "categoria": q.categoria,
                "parametros": [
                    {
                        "nombre": p.nombre,
                        "tipo": p.tipo,
                        "label": p.label,
                        "requerido": p.requerido,
                        "default": p.default,
                        "opciones": p.opciones,
                        "descripcion": p.descripcion,
                    }
                    for p in q.parametros
                ],
                "reglas_negocio": q.reglas_negocio,
            }
            for q in CONSULTAS_CATALOGO
        ]

    def listar_categorias(self) -> list[dict]:
        """Retorna categorías disponibles."""
        cat_names = {
            "exportacion": "Exportaciones",
            "productor": "Productores",
            "mercado": "Mercados",
            "ranking": "Rankings",
            "deposito": "Depósitos",
            "certificador": "Certificadores",
            "empresa": "Empresa",
        }
        return [{"id": c, "nombre": cat_names.get(c, c)} for c in CATEGORIAS]

    def obtener_opciones_dinamicas(self) -> dict:
        """Obtiene opciones dinámicas para los parámetros select."""
        empresas = repo.obtener_empresas()
        mercados = repo.obtener_mercados()
        productos = repo.obtener_productos()
        certificadores = repo.obtener_certificadores()
        depositos = repo.obtener_depositos()
        rango_fechas = repo.obtener_fechas_rango()

        return {
            "empresa": [{"value": e["id_empresa"], "label": e["nombre_unif"]} for e in empresas],
            "empresa_a": [{"value": e["id_empresa"], "label": e["nombre_unif"]} for e in empresas],
            "empresa_b": [{"value": e["id_empresa"], "label": e["nombre_unif"]} for e in empresas],
            "empresa_origen": [{"value": e["id_empresa"], "label": e["nombre_unif"]} for e in empresas],
            "empresa_referencia": [{"value": e["id_empresa"], "label": e["nombre_unif"]} for e in empresas],
            "empresa_competencia": [{"value": e["id_empresa"], "label": e["nombre_unif"]} for e in empresas],
            "certificador": [{"value": e["id_empresa"], "label": e["nombre_unif"]} for e in certificadores],
            "deposito": [{"value": e["id_empresa"], "label": e["nombre_unif"]} for e in depositos],
            "mercado": [{"value": m, "label": m} for m in mercados],
            "producto": [{"value": p["id_producto"], "label": p["nombre_producto"]} for p in productos],
            "fecha_desde": rango_fechas.get("min", ""),
            "fecha_hasta": rango_fechas.get("max", ""),
        }

    def ejecutar(
        self,
        consulta_id: str,
        parametros: dict,
        usuario: str = "system",
    ) -> Optional[QueryResultado]:
        """Ejecuta una consulta y retorna el resultado completo."""
        consulta_def = get_consulta_por_id(consulta_id)
        if not consulta_def:
            return None

        # Merge con defaults
        params = {}
        for p in consulta_def.parametros:
            key = p.nombre
            params[key] = parametros.get(key, p.default)

        # Normalizar empresa=0 -> omitir (para queries opcionales)
        for key in ["empresa"]:
            if params.get(key) == 0 or params.get(key) == "":
                params[key] = 0

        # Ejecutar SQL
        try:
            datos, tiempo_ms = repo.ejecutar_consulta(consulta_def.sql, params)
        except Exception as e:
            # Intentar con valores por defecto para params faltantes
            safe_params = {}
            for k, v in params.items():
                if v is None or v == "":
                    safe_params[k] = "%%" if k in ("fecha_desde", "fecha_hasta") else 0
                else:
                    safe_params[k] = v
            datos, tiempo_ms = repo.ejecutar_consulta(consulta_def.sql, safe_params)

        # Calcular resumen
        resumen = self._calcular_resumen(datos)

        # Calcular KPIs
        kpis = self._calcular_kpis(datos, consulta_def.id)

        # Columnas
        columnas = list(datos[0].keys()) if datos else []

        # Guardar historial
        repo.guardar_historial(
            consulta_id=consulta_id,
            consulta_nombre=consulta_def.nombre,
            parametros=parametros,
            usuario=usuario,
            tiempo_ms=tiempo_ms,
            total_registros=len(datos),
        )

        return QueryResultado(
            consulta_id=consulta_id,
            consulta_nombre=consulta_def.nombre,
            parametros_usados=params,
            ejecutado_en=datetime.now(),
            tiempo_ms=tiempo_ms,
            total_registros=len(datos),
            resumen=resumen,
            kpis=kpis,
            reglas_aplicadas=consulta_def.reglas_negocio,
            datos=datos,
            columnas=columnas,
            metadata={
                "descripcion": consulta_def.descripcion,
                "categoria": consulta_def.categoria,
            },
        )

    def _calcular_resumen(self, datos: list[dict]) -> dict:
        """Calcula el resumen ejecutivo de los datos."""
        if not datos:
            return {"kg_total": 0, "kg_promedio": 0, "movimientos": 0}

        kg_cols = [k for k in datos[0].keys() if "kg" in k.lower() or "peso" in k.lower()]
        kg_total = sum(float(r.get(kg_cols[0], 0) or 0) for r in datos) if kg_cols else 0
        kg_promedio = kg_total / len(datos) if datos else 0

        mov_cols = [k for k in datos[0].keys() if "movimiento" in k.lower() or "cantidad" in k.lower() or "operaciones" in k.lower()]
        mov_total = sum(int(r.get(mov_cols[0], 0) or 0) for r in datos) if mov_cols else len(datos)

        return {
            "kg_total": round(kg_total, 2),
            "kg_promedio": round(kg_promedio, 2),
            "movimientos": mov_total,
            "registros": len(datos),
        }

    def _calcular_kpis(self, datos: list[dict], consulta_id: str) -> list[dict]:
        """Calcula KPIs específicos según el tipo de consulta."""
        kpis = []

        if not datos:
            return kpis

        # KPIs genéricos
        kg_cols = [k for k in datos[0].keys() if "kg" in k.lower() and "total" in k.lower()]
        if kg_cols:
            kg_col = kg_cols[0]
            kgs = sorted([float(r.get(kg_col, 0) or 0) for r in datos], reverse=True)
            total = sum(kgs)

            kpis.extend([
                {"nombre": "Kg Total", "valor": round(total, 2), "unidad": "kg"},
                {"nombre": "Kg Promedio", "valor": round(total / len(kgs), 2) if kgs else 0, "unidad": "kg"},
                {"nombre": "Kg Máximo", "valor": max(kgs), "unidad": "kg"},
                {"nombre": "Kg Mínimo", "valor": min(kgs), "unidad": "kg"},
                {"nombre": "Registros", "valor": len(datos), "unidad": "reg"},
            ])

            if len(kgs) > 1:
                # Mediana
                mid = len(kgs) // 2
                median = kgs[mid] if len(kgs) % 2 else (kgs[mid-1] + kgs[mid]) / 2
                kpis.append({"nombre": "Kg Mediana", "valor": round(median, 2), "unidad": "kg"})

        return kpis

    def obtener_historial(self, limite: int = 50) -> list[dict]:
        """Obtiene el historial de consultas."""
        return repo.obtener_historial(limite)

    def obtener_favoritos(self) -> list[dict]:
        """Obtiene favoritos."""
        return repo.obtener_favoritos()

    def guardar_favorito(
        self,
        consulta_id: str,
        consulta_nombre: str,
        parametros: dict,
        nombre_custom: str = None,
    ) -> int:
        """Guarda una consulta como favorita."""
        return repo.guardar_favorito(consulta_id, consulta_nombre, parametros, nombre_custom)

    def eliminar_favorito(self, favorito_id: int) -> bool:
        """Elimina un favorito."""
        return repo.eliminar_favorito(favorito_id)


service = BusinessQueryService()
