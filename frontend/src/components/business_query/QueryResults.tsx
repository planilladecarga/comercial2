/**
 * QueryResults - Visualización de resultados con tabs
 */
import { useState } from "react"
import { Table, BarChart3, FileText, Clock, Hash, AlertCircle } from "lucide-react"

interface Props {
  resultado: {
    consulta_id: string
    consulta_nombre: string
    parametros_usados: Record<string, any>
    ejecutado_en: string
    tiempo_ms: number
    total_registros: number
    resumen: Record<string, any>
    kpis: { nombre: string; valor: number; unidad: string }[]
    reglas_aplicadas: string[]
    datos: Record<string, any>[]
    columnas: string[]
    metadata: Record<string, any>
  } | null
  isLoading: boolean
  error: string | null
}

type TabType = "resumen" | "tabla" | "kpis"

export function QueryResults({ resultado, isLoading, error }: Props) {
  const [tab, setTab] = useState<TabType>("resumen")

  if (isLoading) {
    return (
      <div className="bg-white rounded-xl p-8 shadow-sm border border-gray-100 flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full mx-auto mb-3" />
          <p className="text-sm text-gray-500">Ejecutando consulta...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-white rounded-xl p-8 shadow-sm border border-red-100 flex items-center justify-center h-64">
        <div className="text-center">
          <AlertCircle className="w-10 h-10 text-red-500 mx-auto mb-3" />
          <p className="text-sm text-red-600 font-medium">Error en la consulta</p>
          <p className="text-xs text-gray-500 mt-1">{error}</p>
        </div>
      </div>
    )
  }

  if (!resultado) {
    return (
      <div className="bg-white rounded-xl p-8 shadow-sm border border-gray-100 flex items-center justify-center h-64">
        <div className="text-center">
          <FileText className="w-10 h-10 text-gray-300 mx-auto mb-3" />
          <p className="text-sm text-gray-500">Selecciona una consulta y ejecútala</p>
          <p className="text-xs text-gray-400 mt-1">Los resultados aparecerán aquí</p>
        </div>
      </div>
    )
  }

  const tabs: { id: TabType; label: string; icon: any }[] = [
    { id: "resumen", label: "Resumen", icon: FileText },
    { id: "tabla", label: `Tabla (${resultado.total_registros})`, icon: Table },
    { id: "kpis", label: "KPIs", icon: BarChart3 },
  ]

  const formatKg = (v: number) => {
    if (v >= 1_000_000) return `${(v / 1_000_000).toFixed(2)}M`
    if (v >= 1_000) return `${(v / 1_000).toFixed(1)}K`
    return v.toFixed(0)
  }

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
      {/* Tabs */}
      <div className="flex border-b border-gray-100">
        {tabs.map(t => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={`flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
              tab === t.id
                ? "border-blue-500 text-blue-600"
                : "border-transparent text-gray-500 hover:text-gray-700"
            }`}
          >
            <t.icon className="w-4 h-4" />
            {t.label}
          </button>
        ))}
        <div className="ml-auto flex items-center gap-4 px-4 py-2 text-xs text-gray-400">
          <span className="flex items-center gap-1"><Clock className="w-3 h-3" />{resultado.tiempo_ms.toFixed(0)}ms</span>
          <span className="flex items-center gap-1"><Hash className="w-3 h-3" />{resultado.total_registros} reg</span>
        </div>
      </div>

      {/* Contenido */}
      <div className="p-5">
        {tab === "resumen" && (
          <div className="space-y-4">
            {/* Metadata */}
            <div className="grid grid-cols-4 gap-4">
              <div className="p-3 bg-blue-50 rounded-lg">
                <p className="text-xs text-blue-500 font-medium">Consulta</p>
                <p className="text-sm font-bold text-blue-900">{resultado.consulta_id}</p>
                <p className="text-xs text-blue-700">{resultado.consulta_nombre}</p>
              </div>
              <div className="p-3 bg-emerald-50 rounded-lg">
                <p className="text-xs text-emerald-500 font-medium">Kg Totales</p>
                <p className="text-2xl font-bold text-emerald-900">{formatKg(resultado.resumen?.kg_total || 0)}</p>
              </div>
              <div className="p-3 bg-purple-50 rounded-lg">
                <p className="text-xs text-purple-500 font-medium">Registros</p>
                <p className="text-2xl font-bold text-purple-900">{resultado.total_registros.toLocaleString()}</p>
              </div>
              <div className="p-3 bg-amber-50 rounded-lg">
                <p className="text-xs text-amber-500 font-medium">Tiempo</p>
                <p className="text-2xl font-bold text-amber-900">{resultado.tiempo_ms.toFixed(0)}ms</p>
                <p className="text-xs text-amber-600">{(resultado.tiempo_ms / 1000).toFixed(2)}s</p>
              </div>
            </div>

            {/* KPIs rápidos */}
            {resultado.kpis?.length > 0 && (
              <div className="grid grid-cols-5 gap-2">
                {resultado.kpis.slice(0, 5).map((k, i) => (
                  <div key={i} className="p-2 bg-gray-50 rounded-lg text-center">
                    <p className="text-[10px] text-gray-500 uppercase">{k.nombre}</p>
                    <p className="text-lg font-bold text-gray-900">{typeof k.valor === "number" ? k.valor.toLocaleString() : k.valor}</p>
                    <p className="text-[10px] text-gray-400">{k.unidad}</p>
                  </div>
                ))}
              </div>
            )}

            {/* Reglas aplicadas */}
            {resultado.reglas_aplicadas?.length > 0 && (
              <div className="p-3 bg-amber-50 rounded-lg">
                <p className="text-xs font-medium text-amber-700 mb-1">Reglas de negocio aplicadas</p>
                {resultado.reglas_aplicadas.map((r, i) => (
                  <p key={i} className="text-xs text-amber-600">• {r}</p>
                ))}
              </div>
            )}

            {/* Parámetros usados */}
            <div className="text-xs text-gray-400">
              Ejecutado: {new Date(resultado.ejecutado_en).toLocaleString()} · Parámetros: {JSON.stringify(resultado.parametros_usados)}
            </div>
          </div>
        )}

        {tab === "tabla" && (
          <div className="overflow-x-auto max-h-96 overflow-y-auto">
            <table className="w-full text-sm">
              <thead className="sticky top-0 bg-gray-50">
                <tr>
                  {resultado.columnas.map((col) => (
                    <th key={col} className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase border-b">
                      {col}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {resultado.datos.slice(0, 200).map((row, i) => (
                  <tr key={i} className="hover:bg-blue-50 border-b border-gray-50">
                    {resultado.columnas.map((col) => (
                      <td key={col} className="px-3 py-2 text-xs text-gray-700">
                        {typeof row[col] === "number"
                          ? row[col].toLocaleString(undefined, { maximumFractionDigits: 2 })
                          : row[col] ?? "-"}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
            {resultado.datos.length > 200 && (
              <p className="text-xs text-gray-400 text-center py-2">
                Mostrando 200 de {resultado.datos.length} registros
              </p>
            )}
          </div>
        )}

        {tab === "kpis" && (
          <div className="grid grid-cols-3 gap-3">
            {resultado.kpis?.map((k, i) => (
              <div key={i} className="p-4 bg-gradient-to-br from-gray-50 to-gray-100 rounded-xl border border-gray-200">
                <p className="text-xs text-gray-500 font-medium">{k.nombre}</p>
                <p className="text-3xl font-bold text-gray-900 my-2">
                  {typeof k.valor === "number" ? k.valor.toLocaleString(undefined, { maximumFractionDigits: 2 }) : k.valor}
                </p>
                <p className="text-xs text-gray-400">{k.unidad}</p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
