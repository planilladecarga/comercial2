/**
 * Módulo 1 - Resumen Ejecutivo
 * Vista rápida del estado del negocio
 */
import { Package, Truck, Building2, Users, Shield, Warehouse, Globe, Beef } from "lucide-react"
import type { ResumenEjecutivo } from "../../types/comando"

interface Props {
  data: ResumenEjecutivo
}

export function ResumenEjecutivo({ data }: Props) {
  const formatKg = (kg: number) => {
    if (kg >= 1_000_000) return `${(kg / 1_000_000).toFixed(2)}M`
    if (kg >= 1_000) return `${(kg / 1_000).toFixed(1)}K`
    return kg.toFixed(0)
  }

  const cards = [
    { label: "Movimientos", value: data.cantidad_movimientos.toLocaleString(), icon: Package, color: "bg-blue-500" },
    { label: "Kg Totales", value: formatKg(data.kg_totales), icon: Beef, color: "bg-emerald-500" },
    { label: "Exportaciones", value: formatKg(data.exportaciones_kg), icon: Truck, color: "bg-purple-500" },
    { label: "Depósito", value: formatKg(data.deposito_kg), icon: Warehouse, color: "bg-amber-500" },
    { label: "Empresas", value: data.cantidad_empresas, icon: Building2, color: "bg-cyan-500" },
    { label: "Productoras", value: data.cantidad_productoras, icon: Users, color: "bg-green-500" },
    { label: "Certificadores", value: data.cantidad_certificadores, icon: Shield, color: "bg-indigo-500" },
    { label: "Mercados", value: data.cantidad_mercados, icon: Globe, color: "bg-teal-500" },
    { label: "Productos", value: data.cantidad_productos, icon: Package, color: "bg-rose-500" },
  ]

  return (
    <div className="bg-white rounded-xl p-5 shadow-sm border border-gray-100">
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-semibold text-gray-900">Resumen Ejecutivo</h3>
        <span className="text-xs text-gray-500">
          Actualizado: {data.fecha_actualizacion || "N/A"}
        </span>
      </div>
      <div className="grid grid-cols-3 gap-4">
        {cards.map((card) => (
          <div key={card.label} className="flex items-center gap-3">
            <span className={`${card.color} text-white p-2 rounded-lg`}>
              <card.icon className="w-4 h-4" />
            </span>
            <div>
              <p className="text-xl font-bold text-gray-900">{card.value}</p>
              <p className="text-xs text-gray-500">{card.label}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
