/**
 * Hook para el Business Query Engine
 */
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import queryApi from "../services/queryApi"

export function useQueryCatalogo() {
  return useQuery({
    queryKey: ["query-catalogo"],
    queryFn: () => queryApi.getCatalogo().then(r => r.data),
    staleTime: 300000,
  })
}

export function useQueryCategorias() {
  return useQuery({
    queryKey: ["query-categorias"],
    queryFn: () => queryApi.getCategorias().then(r => r.data),
    staleTime: 300000,
  })
}

export function useQueryOpciones() {
  return useQuery({
    queryKey: ["query-opciones"],
    queryFn: () => queryApi.getOpciones().then(r => r.data),
    staleTime: 60000,
  })
}

export function useQueryHistorial() {
  return useQuery({
    queryKey: ["query-historial"],
    queryFn: () => queryApi.getHistorial(50).then(r => r.data),
    staleTime: 10000,
  })
}

export function useQueryFavoritos() {
  return useQuery({
    queryKey: ["query-favoritos"],
    queryFn: () => queryApi.getFavoritos().then(r => r.data),
  })
}

export function useEjecutarConsulta() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ consultaId, parametros }: { consultaId: string; parametros: Record<string, any> }) =>
      queryApi.ejecutar(consultaId, parametros).then(r => r.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["query-historial"] })
    },
  })
}

export function useGuardarFavorito() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ consultaId, consultaNombre, parametros, nombreCustom }: {
      consultaId: string
      consultaNombre: string
      parametros: Record<string, any>
      nombreCustom?: string
    }) =>
      queryApi.crearFavorito(consultaId, consultaNombre, parametros, nombreCustom).then(r => r.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["query-favoritos"] })
    },
  })
}

export function useEliminarFavorito() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => queryApi.eliminarFavorito(id).then(r => r.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["query-favoritos"] })
    },
  })
}
