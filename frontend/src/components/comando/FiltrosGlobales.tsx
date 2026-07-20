/**
 * Filtros Globales
 * Controles de filtrado para todo el dashboard
 */
import { Filter } from "lucide-react"
import type { FiltrosDisponibles } from "../../types/comando"

interface Props {
  filtros: FiltrosDisponibles
  filtrosActivos: {
    ano?: number
    mes?: number
    productor?: string
    mercado?: string
    producto?: number
  }
  onCambiarFiltro: (filtro: string, valor: any) => void
}

export function FiltrosGlobales({ filtros, filtrosActivos, onCambiarFiltro }: Props) {
  return (
    <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
      <div className="flex items-center gap-2 mb-3">
        <Filter className="w-4 h-4 text-gray-400" />
        <span className="text-sm font-medium text-gray-700">Filtros</span>
      </div>
      <div className="flex flex-wrap gap-3">
        <select
          className="text-sm border rounded-lg px-3 py-1.5"
          value={filtrosActivos.ano || ""}
          onChange={(e) => onCambiarFiltro("ano", e.target.value ? Number(e.target.value) : undefined)}
        >
          <option value="">Año</option>
          {filtros.anos.map((ano) => (
            <option key={ano} value={ano}>{ano}</option>
          ))}
        </select>

        <select
          className="text-sm border rounded-lg px-3 py-1.5"
          value={filtrosActivos.mes || ""}
          onChange={(e) => onCambiarFiltro("mes", e.target.value ? Number(e.target.value) : undefined)}
        >
          <option value="">Mes</option>
          {filtros.meses.map((m) => (
            <option key={m.mes} value={m.mes}>{m.nombre}</option>
          ))}
        </select>

        <select
          className="text-sm border rounded-lg px-3 py-1.5"
          value={filtrosActivos.productor || ""}
          onChange={(e) => onCambiarFiltro("productor", e.target.value || undefined)}
        >
          <option value="">Productor</option>
          {filtros.productores.slice(0, 50).map((p) => (
            <option key={p.nro} value={p.nro}>{p.nombre}</option>
          ))}
        </select>

        <select
          className="text-sm border rounded-lg px-3 py-1.5"
          value={filtrosActivos.mercado || ""}
          onChange={(e) => onCambiarFiltro("mercado", e.target.value || undefined)}
        >
          <option value="">Mercado</option>
          {filtros.mercados.slice(0, 50).map((m) => (
            <option key={m} value={m}>{m}</option>
          ))}
        </select>

        <select
          className="text-sm border rounded-lg px-3 py-1.5"
          value={filtrosActivos.producto || ""}
          onChange={(e) => onCambiarFiltro("producto", e.target.value ? Number(e.target.value) : undefined)}
        >
          <option value="">Producto</option>
          {filtros.productos.map((p) => (
            <option key={p.id} value={p.id}>{p.nombre}</option>
          ))}
        </select>
      </div>
    </div>
  )
}
