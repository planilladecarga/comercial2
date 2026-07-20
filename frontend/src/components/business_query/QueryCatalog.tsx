/**
 * QueryCatalog - Barra lateral con catálogo de consultas
 */
import { Search, Filter } from "lucide-react"

interface QueryParam {
  nombre: string
  tipo: string
  label: string
  requerido: boolean
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
  catalog: QueryItem[]
  categorias: { id: string; nombre: string }[]
  categoriaActiva: string
  onSelect: (query: QueryItem) => void
  queryActivaId: string | null
  onFiltrar: (texto: string) => void
  filtroTexto: string
  onCategoriaChange: (cat: string) => void
}

export function QueryCatalog({
  catalog,
  categorias,
  categoriaActiva,
  onSelect,
  queryActivaId,
  onFiltrar,
  filtroTexto,
  onCategoriaChange,
}: Props) {
  const filtered = catalog.filter(q =>
    categoriaActiva === "todas" || q.categoria === categoriaActiva
  ).filter(q =>
    filtroTexto === "" ||
    q.nombre.toLowerCase().includes(filtroTexto.toLowerCase()) ||
    q.descripcion.toLowerCase().includes(filtroTexto.toLowerCase()) ||
    q.id.toLowerCase().includes(filtroTexto.toLowerCase())
  )

  const getCategoryColor = (cat: string) => {
    const colors: Record<string, string> = {
      exportacion: "bg-blue-50 text-blue-700 border-blue-200",
      productor: "bg-emerald-50 text-emerald-700 border-emerald-200",
      mercado: "bg-purple-50 text-purple-700 border-purple-200",
      ranking: "bg-amber-50 text-amber-700 border-amber-200",
      deposito: "bg-cyan-50 text-cyan-700 border-cyan-200",
      certificador: "bg-indigo-50 text-indigo-700 border-indigo-200",
      empresa: "bg-gray-50 text-gray-700 border-gray-200",
    }
    return colors[cat] || "bg-gray-50 text-gray-700 border-gray-200"
  }

  return (
    <div className="flex flex-col h-full">
      {/* Buscador */}
      <div className="p-3 border-b border-gray-100">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            placeholder="Buscar consulta..."
            value={filtroTexto}
            onChange={e => onFiltrar(e.target.value)}
            className="w-full pl-9 pr-3 py-2 text-sm border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      </div>

      {/* Categorías */}
      <div className="flex flex-wrap gap-1 p-3 border-b border-gray-100">
        <button
          onClick={() => onCategoriaChange("todas")}
          className={`px-2 py-1 text-xs rounded-full border ${
            categoriaActiva === "todas"
              ? "bg-gray-800 text-white border-gray-800"
              : "bg-white text-gray-600 border-gray-200 hover:bg-gray-50"
          }`}
        >
          Todas
        </button>
        {categorias.map(cat => (
          <button
            key={cat.id}
            onClick={() => onCategoriaChange(cat.id)}
            className={`px-2 py-1 text-xs rounded-full border ${
              categoriaActiva === cat.id
                ? "bg-gray-800 text-white border-gray-800"
                : "bg-white text-gray-600 border-gray-200 hover:bg-gray-50"
            }`}
          >
            {cat.nombre}
          </button>
        ))}
      </div>

      {/* Lista de consultas */}
      <div className="flex-1 overflow-y-auto">
        {filtered.map(q => (
          <button
            key={q.id}
            onClick={() => onSelect(q)}
            className={`w-full text-left p-3 border-b border-gray-50 hover:bg-blue-50 transition-colors ${
              queryActivaId === q.id ? "bg-blue-50 border-l-4 border-l-blue-500" : ""
            }`}
          >
            <div className="flex items-center gap-2 mb-1">
              <span className="text-xs font-mono text-gray-400">{q.id}</span>
              <span className={`px-1.5 py-0.5 text-[10px] rounded border ${getCategoryColor(q.categoria)}`}>
                {q.categoria}
              </span>
            </div>
            <p className="text-sm font-medium text-gray-900">{q.nombre}</p>
            <p className="text-xs text-gray-500 mt-0.5 line-clamp-2">{q.descripcion}</p>
          </button>
        ))}
        {filtered.length === 0 && (
          <div className="p-4 text-center text-sm text-gray-400">
            No hay consultas que coincidan
          </div>
        )}
      </div>
    </div>
  )
}
