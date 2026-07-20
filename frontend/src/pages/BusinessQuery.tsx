/**
 * BusinessQuery - Motor de Consultas Inteligentes
 * Sprint 7 - FRIMARAL BI
 */
import { useState, useCallback } from "react"
import {
  useQueryCatalogo,
  useQueryCategorias,
  useQueryOpciones,
  useQueryHistorial,
  useQueryFavoritos,
  useEjecutarConsulta,
  useGuardarFavorito,
  useEliminarFavorito,
} from "../hooks/useQueryEngine"
import { QueryCatalog } from "../components/business_query/QueryCatalog"
import { QueryParams } from "../components/business_query/QueryParams"
import { QueryResults } from "../components/business_query/QueryResults"
import { QueryExport } from "../components/business_query/QueryExport"
import { QueryHistory } from "../components/business_query/QueryHistory"
import { QueryFavorites } from "../components/business_query/QueryFavorites"
import { Star, History, Search, Loader2 } from "lucide-react"

type PanelType = "favoritos" | "historial" | null

export function BusinessQuery() {
  const [queryActiva, setQueryActiva] = useState<any>(null)
  const [parametros, setParametros] = useState<Record<string, any>>({})
  const [categoriaActiva, setCategoriaActiva] = useState("todas")
  const [filtroTexto, setFiltroTexto] = useState("")
  const [panel, setPanel] = useState<PanelType>(null)
  const [resultado, setResultado] = useState<any>(null)

  // Queries
  const { data: catalogo = [], isLoading: catalogoLoading } = useQueryCatalogo()
  const { data: categorias = [] } = useQueryCategorias()
  const { data: opciones = {} } = useQueryOpciones()
  const { data: historial = [], isLoading: historialLoading } = useQueryHistorial()
  const { data: favoritos = [], isLoading: favoritosLoading } = useQueryFavoritos()

  const ejecutarMut = useEjecutarConsulta()
  const guardarFavMut = useGuardarFavorito()
  const eliminarFavMut = useEliminarFavorito()

  const handleSelectQuery = useCallback((q: any) => {
    setQueryActiva(q)
    setResultado(null)
    // Inicializar parámetros con defaults
    const defaults: Record<string, any> = {}
    q.parametros.forEach((p: any) => {
      defaults[p.nombre] = p.default ?? ""
    })
    setParametros(defaults)
  }, [])

  const handleParamChange = useCallback((key: string, value: any) => {
    setParametros(prev => ({ ...prev, [key]: value }))
  }, [])

  const handleEjecutar = useCallback(() => {
    if (!queryActiva) return
    ejecutarMut.mutate(
      { consultaId: queryActiva.id, parametros },
      {
        onSuccess: (data) => setResultado(data),
      }
    )
  }, [queryActiva, parametros, ejecutarMut])

  const handleGuardarFavorito = useCallback(() => {
    if (!queryActiva) return
    guardarFavMut.mutate({
      consultaId: queryActiva.id,
      consultaNombre: queryActiva.nombre,
      parametros,
    })
  }, [queryActiva, parametros, guardarFavMut])

  const handleSelectHistorial = useCallback((entry: any) => {
    // Buscar la consulta en el catálogo
    const q = catalogo.find((c: any) => c.id === entry.consulta_id)
    if (q) {
      handleSelectQuery(q)
      setParametros(entry.parametros || {})
    }
  }, [catalogo, handleSelectQuery])

  const handleSelectFavorito = useCallback((fav: any) => {
    const q = catalogo.find((c: any) => c.id === fav.consulta_id)
    if (q) {
      handleSelectQuery(q)
      setParametros(fav.parametros_default || {})
    }
  }, [catalogo, handleSelectQuery])

  return (
    <div className="flex h-[calc(100vh-120px)] gap-4">
      {/* Sidebar izquierdo - Catálogo */}
      <div className="w-80 bg-white rounded-xl shadow-sm border border-gray-100 flex flex-col overflow-hidden">
        <div className="p-3 border-b border-gray-100 flex items-center justify-between">
          <h2 className="font-semibold text-gray-900 text-sm">Consultas</h2>
          <div className="flex gap-1">
            <button
              onClick={() => setPanel(panel === "favoritos" ? null : "favoritos")}
              className={`p-1.5 rounded-lg transition-colors ${panel === "favoritos" ? "bg-amber-100 text-amber-600" : "text-gray-400 hover:bg-gray-100"}`}
              title="Favoritos"
            >
              <Star className="w-4 h-4" />
            </button>
            <button
              onClick={() => setPanel(panel === "historial" ? null : "historial")}
              className={`p-1.5 rounded-lg transition-colors ${panel === "historial" ? "bg-blue-100 text-blue-600" : "text-gray-400 hover:bg-gray-100"}`}
              title="Historial"
            >
              <History className="w-4 h-4" />
            </button>
          </div>
        </div>

        {panel === "favoritos" ? (
          <div className="flex-1 overflow-hidden">
            <QueryFavorites
              favoritos={favoritos}
              onSelect={handleSelectFavorito}
              onDelete={(id) => eliminarFavMut.mutate(id)}
              isLoading={favoritosLoading}
            />
          </div>
        ) : panel === "historial" ? (
          <div className="flex-1 overflow-hidden">
            <QueryHistory
              historial={historial}
              onSelect={handleSelectHistorial}
              isLoading={historialLoading}
            />
          </div>
        ) : (
          <div className="flex-1 overflow-hidden">
            {catalogoLoading ? (
              <div className="flex items-center justify-center h-32">
                <Loader2 className="w-5 h-5 text-gray-400 animate-spin" />
              </div>
            ) : (
              <QueryCatalog
                catalog={catalogo}
                categorias={categorias}
                categoriaActiva={categoriaActiva}
                onSelect={handleSelectQuery}
                queryActivaId={queryActiva?.id || null}
                onFiltrar={setFiltroTexto}
                filtroTexto={filtroTexto}
                onCategoriaChange={setCategoriaActiva}
              />
            )}
          </div>
        )}
      </div>

      {/* Centro - Params y Resultados */}
      <div className="flex-1 flex flex-col gap-4 min-w-0">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold text-gray-900">Motor de Consultas</h1>
            <p className="text-xs text-gray-500">Business Query Engine — FRIMARAL BI</p>
          </div>
          {resultado && queryActiva && (
            <div className="flex items-center gap-3">
              <QueryExport resultado={resultado} consultaNombre={queryActiva.nombre} />
              <button
                onClick={handleGuardarFavorito}
                className="flex items-center gap-1.5 px-3 py-1.5 text-xs bg-amber-50 text-amber-700 rounded-lg border border-amber-200 hover:bg-amber-100"
              >
                <Star className="w-3.5 h-3.5" />
                Guardar Favorito
              </button>
            </div>
          )}
        </div>

        {/* Parámetros */}
        {queryActiva && (
          <QueryParams
            query={queryActiva}
            parametros={parametros}
            opciones={opciones}
            onChange={handleParamChange}
            onEjecutar={handleEjecutar}
            isLoading={ejecutarMut.isPending}
          />
        )}

        {/* Resultados */}
        <div className="flex-1 overflow-y-auto">
          <QueryResults
            resultado={resultado}
            isLoading={ejecutarMut.isPending}
            error={ejecutarMut.isError ? "Error al ejecutar la consulta" : null}
          />
        </div>
      </div>
    </div>
  )
}
