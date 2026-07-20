/**
 * Módulo 7 - Evolución Mensual
 * Muestra la tendencia temporal
 */
import { LineChart } from "lucide-react"
import type { Evolucion } from "../../types/comando"

interface Props {
  data: Evolucion
}

export function Evolucion({ data }: Props) {
  const formatKg = (kg: number) => {
    if (kg >= 1_000_000) return `${(kg / 1_000_000).toFixed(1)}M`
    if (kg >= 1_000) return `${(kg / 1_000).toFixed(0)}K`
    return kg.toFixed(0)
  }

  const maxKg = Math.max(...data.meses.map((m) => m.kg), 1)

  return (
    <div className="bg-white rounded-xl p-5 shadow-sm border border-gray-100">
      <div className="flex items-center gap-2 mb-4">
        <LineChart className="w-5 h-5 text-indigo-500" />
        <h3 className="font-semibold text-gray-900">Evolución Mensual</h3>
      </div>
      <div className="space-y-3">
        {data.meses.slice(-12).map((mes) => (
          <div key={`${mes.anio}-${mes.mes}`} className="flex items-center gap-3">
            <span className="text-xs text-gray-500 w-20">{mes.nombre_mes} {mes.anio}</span>
            <div className="flex-1 h-4 bg-gray-100 rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-indigo-500 to-indigo-400"
                style={{ width: `${(mes.kg / maxKg) * 100}%` }}
              />
            </div>
            <span className="text-xs text-gray-600 w-16 text-right font-medium">{formatKg(mes.kg)}</span>
            <div className="flex gap-2 text-xs text-gray-400 w-24 justify-end">
              <span title="Clientes">{mes.clientes_count}c</span>
              <span title="Mercados">{mes.mercados_count}m</span>
              <span title="Productores">{mes.productores_count}p</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
