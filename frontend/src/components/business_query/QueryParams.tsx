/**
 * QueryParams - Formulario de parámetros de consulta
 */
import { Settings2 } from "lucide-react"

interface QueryParam {
  nombre: string
  tipo: string
  label: string
  requerido: boolean
  default: any
  opciones: { value: any; label: string }[]
  descripcion: string
}

interface QueryItem {
  id: string
  nombre: string
  descripcion: string
  categoria: string
  parametros: QueryParam[]
  reglas_negocio: string[]
}

interface Props {
  query: QueryItem
  parametros: Record<string, any>
  opciones: Record<string, { value: any; label: string }[]>
  onChange: (key: string, value: any) => void
  onEjecutar: () => void
  isLoading: boolean
}

export function QueryParams({ query, parametros, opciones, onChange, onEjecutar, isLoading }: Props) {
  const requeridosFaltantes = query.parametros
    .filter(p => p.requerido && !parametros[p.nombre])
    .length

  return (
    <div className="bg-white rounded-xl p-5 shadow-sm border border-gray-100">
      <div className="flex items-center gap-2 mb-4">
        <Settings2 className="w-5 h-5 text-blue-500" />
        <div>
          <h3 className="font-semibold text-gray-900">{query.nombre}</h3>
          <p className="text-xs text-gray-500">{query.descripcion}</p>
        </div>
      </div>

      {/* Parámetros */}
      <div className="grid grid-cols-2 gap-3 mb-4">
        {query.parametros.map(p => (
          <div key={p.nombre} className="col-span-1">
            <label className="block text-xs font-medium text-gray-700 mb-1">
              {p.label}
              {p.requerido && <span className="text-red-500 ml-1">*</span>}
            </label>

            {p.tipo === "select" ? (
              <select
                value={parametros[p.nombre] ?? p.default ?? ""}
                onChange={e => onChange(p.nombre, e.target.value)}
                className="w-full text-sm border rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">{p.descripcion || "Seleccionar..."}</option>
                {(opciones[p.nombre] || p.opciones).map((opt: any) => (
                  <option key={opt.value} value={opt.value}>{opt.label}</option>
                ))}
              </select>
            ) : p.tipo === "int" ? (
              <input
                type="number"
                value={parametros[p.nombre] ?? p.default ?? ""}
                onChange={e => onChange(p.nombre, parseInt(e.target.value) || 0)}
                className="w-full text-sm border rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder={p.descripcion}
              />
            ) : p.tipo === "date" ? (
              <input
                type="date"
                value={parametros[p.nombre] ?? ""}
                onChange={e => onChange(p.nombre, e.target.value)}
                className="w-full text-sm border rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            ) : (
              <input
                type="text"
                value={parametros[p.nombre] ?? ""}
                onChange={e => onChange(p.nombre, e.target.value)}
                className="w-full text-sm border rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder={p.descripcion}
              />
            )}
          </div>
        ))}
      </div>

      {/* Reglas de negocio */}
      {query.reglas_negocio.length > 0 && (
        <div className="mb-4 p-3 bg-amber-50 rounded-lg border border-amber-100">
          <p className="text-xs font-medium text-amber-700 mb-1">Reglas aplicadas</p>
          <ul className="space-y-0.5">
            {query.reglas_negocio.map((r, i) => (
              <li key={i} className="text-xs text-amber-600">• {r}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Botón ejecutar */}
      <button
        onClick={onEjecutar}
        disabled={isLoading || requeridosFaltantes > 0}
        className={`w-full py-2.5 rounded-lg font-medium text-sm transition-colors ${
          isLoading || requeridosFaltantes > 0
            ? "bg-gray-200 text-gray-400 cursor-not-allowed"
            : "bg-blue-600 text-white hover:bg-blue-700"
        }`}
      >
        {isLoading ? "Ejecutando..." : `Ejecutar${requeridosFaltantes > 0 ? ` (${requeridosFaltantes} params requeridos)` : ""}`}
      </button>
    </div>
  )
}
