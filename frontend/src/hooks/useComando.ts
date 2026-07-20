/**
 * Hook principal para el Centro de Comando Comercial
 * Gestiona la obtención de datos y estados
 */
import { useQuery } from "@tanstack/react-query"
import comandoApi from "../services/comandoApi"
import type { Comando360Data } from "../types/comando"

export function useComando(idEmpresa?: number) {
  return useQuery<Comando360Data>({
    queryKey: ["comando", idEmpresa],
    queryFn: () => comandoApi.getCompleto(idEmpresa).then((r) => r.data),
    staleTime: 30000, // 30 segundos
    refetchInterval: 60000, // Refrescar cada minuto
    retry: 2,
  })
}

export function useResumen() {
  return useQuery({
    queryKey: ["comando-resumen"],
    queryFn: () => comandoApi.getResumen().then((r) => r.data),
    staleTime: 30000,
  })
}

export function useAlertas(idEmpresa?: number) {
  return useQuery({
    queryKey: ["comando-alertas", idEmpresa],
    queryFn: () => comandoApi.getAlertas(idEmpresa).then((r) => r.data),
    staleTime: 30000,
  })
}

export function useOportunidades(idEmpresa?: number) {
  return useQuery({
    queryKey: ["comando-oportunidades", idEmpresa],
    queryFn: () => comandoApi.getOportunidades(idEmpresa).then((r) => r.data),
    staleTime: 30000,
  })
}

export function useCompetencia(idA?: number, idB?: number) {
  return useQuery({
    queryKey: ["comando-competencia", idA, idB],
    queryFn: () => comandoApi.getCompetencia(idA, idB).then((r) => r.data),
    staleTime: 30000,
  })
}

export function useIndicadores(idEmpresa?: number) {
  return useQuery({
    queryKey: ["comando-indicadores", idEmpresa],
    queryFn: () => comandoApi.getIndicadores(idEmpresa).then((r) => r.data),
    staleTime: 30000,
  })
}

export function useMapa() {
  return useQuery({
    queryKey: ["comando-mapa"],
    queryFn: () => comandoApi.getMapa().then((r) => r.data),
    staleTime: 60000,
  })
}

export function useEvolucion() {
  return useQuery({
    queryKey: ["comando-evolucion"],
    queryFn: () => comandoApi.getEvolucion().then((r) => r.data),
    staleTime: 60000,
  })
}

export function useRankings() {
  return useQuery({
    queryKey: ["comando-rankings"],
    queryFn: () => comandoApi.getRankings().then((r) => r.data),
    staleTime: 60000,
  })
}

export function useFiltros() {
  return useQuery({
    queryKey: ["comando-filtros"],
    queryFn: () => comandoApi.getFiltros().then((r) => r.data),
    staleTime: 300000, // 5 minutos
  })
}
