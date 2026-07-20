/**
 * Cliente API para el Business Query Engine
 * Sprint 7 - FRIMARAL BI
 */
import axios from "axios"

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000"

const api = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
})

export const queryApi = {
  // Catálogo
  getCatalogo: () => api.get("/api/query/catalogo"),
  getCategorias: () => api.get("/api/query/categorias"),
  getOpciones: () => api.get("/api/query/opciones"),

  // Ejecutar
  ejecutar: (consultaId: string, parametros: Record<string, any>, usuario = "system") =>
    api.post("/api/query/ejecutar", {
      consulta_id: consultaId,
      parametros,
      usuario,
    }),

  // Historial
  getHistorial: (limite = 50) => api.get("/api/query/historial", { params: { limite } }),

  // Favoritos
  getFavoritos: () => api.get("/api/query/favoritos"),
  crearFavorito: (consultaId: string, consultaNombre: string, parametros: Record<string, any>, nombreCustom?: string) =>
    api.post("/api/query/favoritos", {
      consulta_id: consultaId,
      consulta_nombre: consultaNombre,
      parametros,
      nombre_custom: nombreCustom,
    }),
  eliminarFavorito: (id: number) => api.delete(`/api/query/favoritos/${id}`),
}

export default queryApi
