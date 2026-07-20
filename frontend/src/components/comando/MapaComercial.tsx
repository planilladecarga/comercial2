/**
 * Módulo 6 - Mapa Comercial
 * Muestra distribución por países
 */
import { Globe } from "lucide-react"
import type { MapaComercial } from "../../types/comando"

interface Props {
  data: MapaComercial
}

export function MapaComercial({ data }: Props) {
  const formatKg = (kg: number) => {
    if (kg >= 1_000_000) return `${(kg / 1_000_000).toFixed(1)}M`
    if (kg >= 1_000) return `${(kg / 1_000).toFixed(0)}K`
    return kg.toFixed(0)
  }

  return (
    <div className="bg-white rounded-xl p-5 shadow-sm border border-gray-100">
      <div className="flex items-center gap-2 mb-4">
        <Globe className="w-5 h-5 text-blue-500" />
        <h3 className="font-semibold text-gray-900">Mapa Comercial</h3>
        <span className="text-xs text-gray-500 ml-auto">{formatKg(data.total_kg)} total</span>
      </div>
      <div className="space-y-2 max-h-64 overflow-y-auto">
        {data.paises.map((pais) => (
          <div key={pais.pais} className="flex items-center gap-3">
            <span className="text-sm font-medium w-40 truncate">{pais.pais}</span>
            <div className="flex-1 h-2 bg-gray-100 rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-blue-500 to-blue-400"
                style={{ width: `${pais.participacion_pct}%` }}
              />
            </div>
            <span className="text-xs text-gray-500 w-16 text-right">{pais.participacion_pct.toFixed(1)}%</span>
            <span className={`text-xs w-16 text-right ${pais.crecimiento_pct >= 0 ? "text-emerald-600" : "text-red-600"}`}>
              {pais.crecimiento_pct >= 0 ? "+" : ""}{pais.crecimiento_pct.toFixed(1)}%
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}
