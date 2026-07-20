/**
 * Centro de Comando Comercial
 * Sprint 6 - FRIMARAL BI
 * Dashboard Ejecutivo del Director Comercial
 */
import { useState } from "react"
import { useComando, useFiltros } from "../hooks/useComando"
import { ResumenEjecutivo } from "../components/comando/ResumenEjecutivo"
import { AlertasDia } from "../components/comando/AlertasDia"
import { Oportunidades } from "../components/comando/Oportunidades"
import { Competencia } from "../components/comando/Competencia"
import { Indicadores } from "../components/comando/Indicadores"
import { MapaComercial } from "../components/comando/MapaComercial"
import { Evolucion } from "../components/comando/Evolucion"
import { Rankings } from "../components/comando/Rankings"
import { FiltrosGlobales } from "../components/comando/FiltrosGlobales"
import { Loader2, AlertCircle } from "lucide-react"
import comandoApi from "../services/comandoApi"
import type { FiltrosDisponibles } from "../types/comando"

export function Comando360() {
  const [empresaAId, setEmpresaAId] = useState<number>(1)
  const [empresaBId, setEmpresaBId] = useState<number>(2)
  const [filtrosActivos, setFiltrosActivos] = useState({
    ano: undefined as number | undefined,
    mes: undefined as number | undefined,
    productor: undefined as string | undefined,
    mercado: undefined as string | undefined,
    producto: undefined as number | undefined,
  })

  const { data, isLoading, error, refetch } = useComando()
  const { data: filtros } = useFiltros()

  const handleCambiarFiltro = (filtro: string, valor: any) => {
    setFiltrosActivos((prev) => ({ ...prev, [filtro]: valor }))
  }

  const handleCambiarEmpresa = (idA: number, idB: number) => {
    setEmpresaAId(idA)
    setEmpresaBId(idB)
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Loader2 className="w-8 h-8 text-blue-500 animate-spin" />
        <span className="ml-3 text-gray-600">Cargando Centro de Comando...</span>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-96">
        <AlertCircle className="w-12 h-12 text-red-500 mb-4" />
        <h2 className="text-xl font-semibold text-gray-900 mb-2">Error al cargar datos</h2>
        <p className="text-gray-500 mb-4">Verifique que el servidor API esté ejecutándose</p>
        <button
          onClick={() => refetch()}
          className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600"
        >
          Reintentar
        </button>
      </div>
    )
  }

  if (!data) {
    return (
      <div className="flex items-center justify-center h-96">
        <span className="text-gray-500">No hay datos disponibles</span>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Centro de Comando Comercial</h1>
          <p className="text-sm text-gray-500">FRIMARAL BI — Dashboard Ejecutivo</p>
        </div>
        <div className="text-xs text-gray-400">
          Última actualización: {data.resumen.fecha_actualizacion || "N/A"}
        </div>
      </div>

      {/* Filtros Globales */}
      {filtros && (
        <FiltrosGlobales
          filtros={filtros as FiltrosDisponibles}
          filtrosActivos={filtrosActivos}
          onCambiarFiltro={handleCambiarFiltro}
        />
      )}

      {/* Módulo 1 - Resumen Ejecutivo */}
      <ResumenEjecutivo data={data.resumen} />

      {/* Módulos 2-3 en fila */}
      <div className="grid grid-cols-2 gap-4">
        <AlertasDia data={data.alertas} />
        <Oportunidades data={data.oportunidades} />
      </div>

      {/* Módulo 4 - Competencia */}
      <Competencia
        data={data.competencia!}
        empresas={[]}
        empresaAId={empresaAId}
        empresaBId={empresaBId}
        onCambiarEmpresa={handleCambiarEmpresa}
      />

      {/* Módulo 5 - Indicadores */}
      <Indicadores data={data.indicadores} />

      {/* Módulo 6 - Mapa y Módulo 7 - Evolución */}
      <div className="grid grid-cols-2 gap-4">
        <MapaComercial data={data.mapa} />
        <Evolucion data={data.evolucion} />
      </div>

      {/* Módulo 8 - Rankings */}
      <Rankings data={data.rankings} />
    </div>
  )
}
