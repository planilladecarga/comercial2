/**
 * Módulo 8 - Top Rankings
 * Muestra los mejores en cada categoría
 */
import { Trophy, Medal } from "lucide-react"
import type { Rankings } from "../../types/comando"

interface Props {
  data: Rankings
}

export function Rankings({ data }: Props) {
  const formatKg = (kg: number) => {
    if (kg >= 1_000_000) return `${(kg / 1_000_000).toFixed(1)}M`
    if (kg >= 1_000) return `${(kg / 1_000).toFixed(0)}K`
    return kg.toFixed(0)
  }

  const secciones = [
    { label: "Top Productores", items: data.top_productores, color: "bg-emerald-500" },
    { label: "Top Depósitos", items: data.top_depositos, color: "bg-blue-500" },
    { label: "Top Certificadores", items: data.top_certificadores, color: "bg-purple-500" },
    { label: "Top Mercados", items: data.top_mercados, color: "bg-amber-500" },
    { label: "Top Productos", items: data.top_productos, color: "bg-rose-500" },
  ]

  return (
    <div className="bg-white rounded-xl p-5 shadow-sm border border-gray-100">
      <div className="flex items-center gap-2 mb-4">
        <Trophy className="w-5 h-5 text-amber-500" />
        <h3 className="font-semibold text-gray-900">Top Rankings</h3>
      </div>
      <div className="grid grid-cols-5 gap-4">
        {secciones.map((seccion) => (
          <div key={seccion.label}>
            <p className="text-xs font-medium text-gray-500 uppercase mb-2">{seccion.label}</p>
            <div className="space-y-1">
              {seccion.items.slice(0, 5).map((item) => (
                <div key={item.ranking} className="flex items-center gap-2">
                  {item.ranking <= 3 ? (
                    <Medal className={`w-4 h-4 ${item.ranking === 1 ? "text-amber-500" : item.ranking === 2 ? "text-gray-400" : "text-amber-700"}`} />
                  ) : (
                    <span className="w-4 text-center text-xs text-gray-400">#{item.ranking}</span>
                  )}
                  <span className="text-xs truncate flex-1" title={item.nombre}>{item.nombre}</span>
                  <span className="text-xs text-gray-500">{formatKg(item.kg)}</span>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
