/**
 * Módulo 3 - Oportunidades
 * Muestra oportunidades de crecimiento
 */
import { Target, TrendingUp, Building2, Users, ShoppingCart } from "lucide-react"
import type { Oportunidades } from "../../types/comando"

interface Props {
  data: Oportunidades
}

const getIcon = (tipo: string) => {
  switch (tipo) {
    case "potencial_caliral": return Users
    case "mercado_no_participa": return Target
    case "competencia": return Building2
    case "compartido": return Users
    case "cliente_potencial": return ShoppingCart
    default: return TrendingUp
  }
}

const getColor = (tipo: string) => {
  switch (tipo) {
    case "potencial_caliral": return "bg-blue-50 border-blue-200"
    case "mercado_no_participa": return "bg-red-50 border-red-200"
    case "competencia": return "bg-amber-50 border-amber-200"
    case "compartido": return "bg-purple-50 border-purple-200"
    case "cliente_potencial": return "bg-emerald-50 border-emerald-200"
    default: return "bg-gray-50 border-gray-200"
  }
}

export function Oportunidades({ data }: Props) {
  const secciones = [
    { label: "Top 20 Productores Potenciales", items: data.top_20_productores_potenciales },
    { label: "Mercados sin Participación", items: data.mercados_no_participa },
    { label: "Productores en Competencia", items: data.productores_competencia },
    { label: "Productores Compartidos", items: data.productores_compartidos },
    { label: "Clientes Potenciales", items: data.clientes_potenciales },
  ]

  const formatKg = (kg: number) => {
    if (kg >= 1_000_000) return `${(kg / 1_000_000).toFixed(1)}M`
    if (kg >= 1_000) return `${(kg / 1_000).toFixed(0)}K`
    return kg.toFixed(0)
  }

  return (
    <div className="bg-white rounded-xl p-5 shadow-sm border border-gray-100">
      <div className="flex items-center gap-2 mb-4">
        <Target className="w-5 h-5 text-emerald-500" />
        <h3 className="font-semibold text-gray-900">Oportunidades</h3>
      </div>
      <div className="space-y-4">
        {secciones.map((seccion) =>
          seccion.items.length > 0 ? (
            <div key={seccion.label}>
              <p className="text-xs font-medium text-gray-500 uppercase mb-2">{seccion.label}</p>
              <div className="space-y-1">
                {seccion.items.slice(0, 5).map((item) => {
                  const Icon = getIcon(item.tipo)
                  const colorClass = getColor(item.tipo)
                  return (
                    <div key={item.ranking} className={`flex items-center gap-2 p-2 rounded-lg border ${colorClass}`}>
                      <span className="text-xs font-bold text-gray-400 w-5">#{item.ranking}</span>
                      <Icon className="w-4 h-4 text-gray-600" />
                      <span className="text-sm font-medium truncate flex-1">{item.nombre}</span>
                      <span className="text-xs text-gray-500">{formatKg(item.kg)}</span>
                    </div>
                  )
                })}
              </div>
            </div>
          ) : null
        )}
      </div>
    </div>
  )
}
