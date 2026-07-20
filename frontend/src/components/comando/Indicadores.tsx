/**
 * Módulo 5 - Indicadores KPIs
 * Muestra los 6 índices clave
 */
import { Activity, TrendingUp, TrendingDown, Minus } from "lucide-react"
import type { Indicadores } from "../../types/comando"

interface Props {
  data: Indicadores
}

const getIcon = (tendencia: string) => {
  switch (tendencia) {
    case "up": return TrendingUp
    case "down": return TrendingDown
    default: return Minus
  }
}

const getEstadoColor = (estado: string) => {
  switch (estado) {
    case "ok": return "text-emerald-600 bg-emerald-50 border-emerald-200"
    case "advertencia": return "text-amber-600 bg-amber-50 border-amber-200"
    case "critico": return "text-red-600 bg-red-50 border-red-200"
    default: return "text-gray-600 bg-gray-50 border-gray-200"
  }
}

const kpis = [
  { key: "indice_diversificacion", label: "Diversificación" },
  { key: "indice_riesgo", label: "Riesgo" },
  { key: "indice_competencia", label: "Competencia" },
  { key: "indice_fidelidad", label: "Fidelidad" },
  { key: "indice_crecimiento", label: "Crecimiento" },
  { key: "indice_oportunidad", label: "Oportunidad" },
]

export function Indicadores({ data }: Props) {
  const kpiList = kpis.map((k) => ({
    ...k,
    data: data[k.key as keyof Indicadores],
  }))

  return (
    <div className="bg-white rounded-xl p-5 shadow-sm border border-gray-100">
      <div className="flex items-center gap-2 mb-4">
        <Activity className="w-5 h-5 text-cyan-500" />
        <h3 className="font-semibold text-gray-900">Indicadores KPIs</h3>
      </div>
      <div className="grid grid-cols-2 gap-3">
        {kpiList.map((kpi) => {
          const Icon = getIcon(kpi.data.tendencia)
          const estadoColor = getEstadoColor(kpi.data.estado)
          return (
            <div key={kpi.key} className={`p-3 rounded-lg border ${estadoColor}`}>
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs font-medium">{kpi.label}</span>
                <Icon className="w-4 h-4" />
              </div>
              <p className="text-2xl font-bold">
                {kpi.data.valor.toFixed(1)}
                <span className="text-xs font-normal ml-1">{kpi.data.unidad}</span>
              </p>
              <p className="text-xs mt-1 opacity-75">{kpi.data.detalle}</p>
            </div>
          )
        })}
      </div>
    </div>
  )
}
