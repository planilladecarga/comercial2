/**
 * QueryFavorites - Panel de favoritos
 */
import { Star, Trash2 } from "lucide-react"

interface FavoritoEntry {
  id: number
  consulta_id: string
  consulta_nombre: string
  parametros_default: Record<string, any>
  nombre_custom?: string
}

interface Props {
  favoritos: FavoritoEntry[]
  onSelect: (fav: FavoritoEntry) => void
  onDelete: (id: number) => void
  isLoading: boolean
}

export function QueryFavorites({ favoritos, onSelect, onDelete, isLoading }: Props) {
  if (isLoading) {
    return <div className="p-4 text-sm text-gray-400">Cargando favoritos...</div>
  }

  if (favoritos.length === 0) {
    return <div className="p-4 text-sm text-gray-400">Sin favoritos guardados</div>
  }

  return (
    <div className="space-y-1 max-h-64 overflow-y-auto">
      {favoritos.map(fav => (
        <div
          key={fav.id}
          className="flex items-center gap-2 p-3 rounded-lg hover:bg-amber-50 border border-transparent hover:border-amber-100 group"
        >
          <button
            onClick={() => onSelect(fav)}
            className="flex-1 text-left"
          >
            <div className="flex items-center gap-2 mb-0.5">
              <Star className="w-3 h-3 text-amber-500 fill-amber-500" />
              <span className="text-xs font-mono text-gray-400">{fav.consulta_id}</span>
            </div>
            <p className="text-sm font-medium text-gray-900">
              {fav.nombre_custom || fav.consulta_nombre}
            </p>
            {fav.parametros_default && Object.keys(fav.parametros_default).length > 0 && (
              <p className="text-[10px] text-gray-400 mt-0.5">
                {Object.keys(fav.parametros_default).length} parámetros
              </p>
            )}
          </button>
          <button
            onClick={() => onDelete(fav.id)}
            className="p-1 text-gray-300 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-opacity"
          >
            <Trash2 className="w-3.5 h-3.5" />
          </button>
        </div>
      ))}
    </div>
  )
}
