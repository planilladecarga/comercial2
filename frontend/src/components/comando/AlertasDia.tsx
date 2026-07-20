/**
 * Módulo 2 - Alertas del Día
 * Muestra cambios significativos en el negocio
 */
import { AlertTriangle, TrendingUp, TrendingDown, Users, Building2, Package } from "lucide-react"
import type { AlertasDia } from "../../types/comando"

interface Props {
  data: AlertasDia
}

const getIcon = (tipo: string) => {
  switch (tipo) {
    case "nuevo": return TrendingUp
    case "perdido": return TrendingDown
    case "inactivo": return Users
    case "aumento": return TrendingUp
    case "disminucion": return TrendingDown
    case "cambio": return Building2
    default: return AlertTriangle
  }
}

const getColor = (tipo: string) => {
  switch (tipo) {
    case "nuevo": return "text-emerald-600 bg-emerald-50"
    case "perdido": return "text-red-600 bg-red-50"
    case "inactivo": return "text-amber-600 bg-amber-50"
    case "aumento": return "text-blue-600 bg-blue-50"
    case "disminucion": return "text-orange-600 bg-orange-50"
    case "cambio": return "text-purple-600 bg-purple-50"
    default: return "text-gray-600 bg-gray-50"
  }
}

export function AlertasDia({ data }: Props) {
  const alertas = [
    { label: "Clientes Nuevos", items: data.clientes_nuevos },
    { label: "Clientes Perdidos", items: data.clientes_perdidos },
    { label: "Mercados Nuevos", items: data.mercados_nuevos },
    { label: "Mercados Perdidos", items: data.mercados_perdidos },
    { label: "Productores Nuevos", items: data.productores_nuevos },
    { label: "Productores Inactivos", items: data.productores_inactivos },
    { label: "Aumentos Importantes", items: data.aumentos_importantes },
    { label: "Disminuciones Importantes", items: data.disminuciones_importantes },
    { label: "Cambios Depósito", items: data.cambios_deposito },
  ]

  return (
    <div className="bg-white rounded-xl p-5 shadow-sm border border-gray-100">
      <div className="flex items-center gap-2 mb-4">
        <AlertTriangle className="w-5 h-5 text-amber-500" />
        <h3 className="font-semibold text-gray-900">Alertas del Día</h3>
      </div>
      <div className="space-y-4">
        {alertas.map((grupo) =>
          grupo.items.length > 0 ? (
            <div key={grupo.label}>
              <p className="text-xs font-medium text-gray-500 uppercase mb-2">{grupo.label}</p>
              <div className="space-y-1">
                {grupo.items.slice(0, 3).map((alerta, i) => {
                  const Icon = getIcon(alerta.tipo)
                  const colorClass = getColor(alerta.tipo)
                  return (
                    <div key={i} className={`flex items-center gap-2 p-2 rounded-lg ${colorClass}`}>
                      <Icon className="w-4 h-4 flex-shrink-0" />
                      <span className="text-sm font-medium truncate">{alerta.nombre}</span>
                      {alerta.magnitud !== null && alerta.magnitud !== undefined && (
                        <span className="text-xs ml-auto">{alerta.magnitud > 0 ? "+" : ""}{alerta.magnitud.toFixed(1)}%</span>
                      )}
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
