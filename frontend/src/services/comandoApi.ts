/**
 * Cliente API para el Centro de Comando Comercial
 * Sprint 6 - FRIMARAL BI
 */
import axios from "axios"

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000"

const api = axios.create({
  baseURL: API_BASE,
  timeout: 10000,
})

export const comandoApi = {
  // Módulo 1 - Resumen Ejecutivo
  getResumen: () => api.get("/api/comando/resumen"),

  // Módulo 2 - Alertas del Día
  getAlertas: (idEmpresa?: number) =>
    api.get("/api/comando/alertas", { params: { id_empresa: idEmpresa } }),

  // Módulo 3 - Oportunidades
  getOportunidades: (idEmpresa?: number) =>
    api.get("/api/comando/oportunidades", { params: { id_empresa: idEmpresa } }),

  // Módulo 4 - Competencia
  getCompetencia: (idA?: number, idB?: number) =>
    api.get("/api/comando/competencia", { params: { id_a: idA, id_b: idB } }),
  getEmpresas: () => api.get("/api/comando/competencia/empresas"),

  // Módulo 5 - Indicadores
  getIndicadores: (idEmpresa?: number) =>
    api.get("/api/comando/indicadores", { params: { id_empresa: idEmpresa } }),

  // Módulo 6 - Mapa
  getMapa: () => api.get("/api/comando/mapa"),

  // Módulo 7 - Evolución
  getEvolucion: () => api.get("/api/comando/evolucion"),

  // Módulo 8 - Rankings
  getRankings: () => api.get("/api/comando/rankings"),

  // Filtros
  getFiltros: () => api.get("/api/comando/filtros"),

  // Datos completos
  getCompleto: (idEmpresa?: number) =>
    api.get("/api/comando/completo", { params: { id_empresa: idEmpresa } }),
}

export default comandoApi
