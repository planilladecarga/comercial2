/**
 * Módulo 4 - Comparación Competitiva
 * Compara CALIRAL vs empresa seleccionada
 */
import { BarChart3, Building2, Users, Globe, Package } from "lucide-react"
import type { Competencia } from "../../types/comando"

interface Props {
  data: Competencia
  empresas: { id_empresa: number; nombre_unif: string }[]
  empresaAId: number
  empresaBId: number
  onCambiarEmpresa: (idA: number, idB: number) => void
}

export function Competencia({ data, empresas, empresaAId, empresaBId, onCambiarEmpresa }: Props) {
  if (!data) {
    return (
      <div className="bg-white rounded-xl p-5 shadow-sm border border-gray-100">
        <div className="flex items-center gap-2 mb-4">
          <BarChart3 className="w-5 h-5 text-purple-500" />
          <h3 className="font-semibold text-gray-900">Comparación Competitiva</h3>
        </div>
        <p className="text-sm text-gray-500">Cargando datos...</p>
      </div>
    )
  }

  const formatKg = (kg: number) => {
    if (kg >= 1_000_000) return `${(kg / 1_000_000).toFixed(2)}M`
    if (kg >= 1_000) return `${(kg / 1_000).toFixed(1)}K`
    return kg.toFixed(0)
  }

  const totalKg = data.kg_a + data.kg_b || 1
  const ratioA = (data.kg_a / totalKg) * 100
  const ratioB = (data.kg_b / totalKg) * 100

  return (
    <div className="bg-white rounded-xl p-5 shadow-sm border border-gray-100">
      <div className="flex items-center gap-2 mb-4">
        <BarChart3 className="w-5 h-5 text-purple-500" />
        <h3 className="font-semibold text-gray-900">Comparación Competitiva</h3>
      </div>

      {/* Selector de empresas */}
      <div className="flex gap-2 mb-4">
        <select
          className="flex-1 text-sm border rounded-lg p-2"
          value={empresaAId}
          onChange={(e) => onCambiarEmpresa(Number(e.target.value), empresaBId)}
        >
          {empresas.map((e) => (
            <option key={e.id_empresa} value={e.id_empresa}>{e.nombre_unif}</option>
          ))}
        </select>
        <span className="text-gray-400 self-center">vs</span>
        <select
          className="flex-1 text-sm border rounded-lg p-2"
          value={empresaBId}
          onChange={(e) => onCambiarEmpresa(empresaAId, Number(e.target.value))}
        >
          {empresas.map((e) => (
            <option key={e.id_empresa} value={e.id_empresa}>{e.nombre_unif}</option>
          ))}
        </select>
      </div>

      {/* Comparación de KG */}
      <div className="mb-4">
        <div className="flex justify-between text-sm mb-1">
          <span className="font-medium">{data.empresa_a}</span>
          <span className="text-gray-500">{formatKg(data.kg_a)} ({typeof data.participacion_a === 'number' ? data.participacion_a.toFixed(1) : '—'}%)</span>
        </div>
        <div className="h-3 bg-gray-100 rounded-full overflow-hidden">
          <div className="h-full bg-emerald-500" style={{ width: `${ratioA}%` }} />
        </div>
        <div className="flex justify-between text-sm mt-1">
          <span className="font-medium">{data.empresa_b}</span>
          <span className="text-gray-500">{formatKg(data.kg_b)} ({typeof data.participacion_b === 'number' ? data.participacion_b.toFixed(1) : '—'}%)</span>
        </div>
        <div className="h-3 bg-gray-100 rounded-full overflow-hidden">
          <div className="h-full bg-purple-500" style={{ width: `${ratioB}%` }} />
        </div>
      </div>

      {/* Métricas comparadas */}
      <div className="grid grid-cols-2 gap-4">
        <div className="p-3 bg-gray-50 rounded-lg">
          <div className="flex items-center gap-2 mb-2">
            <Users className="w-4 h-4 text-gray-400" />
            <span className="text-xs text-gray-500">Productores</span>
          </div>
          <div className="flex justify-between">
            <span className="text-sm font-medium">{data.comparacion.a.productores_count}</span>
            <span className="text-gray-300">|</span>
            <span className="text-sm font-medium">{data.comparacion.b.productores_count}</span>
          </div>
        </div>
        <div className="p-3 bg-gray-50 rounded-lg">
          <div className="flex items-center gap-2 mb-2">
            <Globe className="w-4 h-4 text-gray-400" />
            <span className="text-xs text-gray-500">Mercados</span>
          </div>
          <div className="flex justify-between">
            <span className="text-sm font-medium">{data.comparacion.a.mercados_count}</span>
            <span className="text-gray-300">|</span>
            <span className="text-sm font-medium">{data.comparacion.b.mercados_count}</span>
          </div>
        </div>
        <div className="p-3 bg-gray-50 rounded-lg">
          <div className="flex items-center gap-2 mb-2">
            <Building2 className="w-4 h-4 text-gray-400" />
            <span className="text-xs text-gray-500">Clientes</span>
          </div>
          <div className="flex justify-between">
            <span className="text-sm font-medium">{data.comparacion.a.clientes_count}</span>
            <span className="text-gray-300">|</span>
            <span className="text-sm font-medium">{data.comparacion.b.clientes_count}</span>
          </div>
        </div>
        <div className="p-3 bg-gray-50 rounded-lg">
          <div className="flex items-center gap-2 mb-2">
            <Package className="w-4 h-4 text-gray-400" />
            <span className="text-xs text-gray-500">Productos</span>
          </div>
          <div className="flex justify-between">
            <span className="text-sm font-medium">{data.comparacion.a.productos_count}</span>
            <span className="text-gray-300">|</span>
            <span className="text-sm font-medium">{data.comparacion.b.productos_count}</span>
          </div>
        </div>
      </div>
    </div>
  )
}
