/**
 * QueryHistory - Panel de historial de consultas
 */
import { Clock, Hash } from "lucide-react"

interface HistorialEntry {
  id: number
  consulta_id: string
  consulta_nombre: string
  parametros: Record<string, any>
  usuario: string
  timestamp: string
  tiempo_ms: number
  total_registros: number
}

interface Props {
  historial: HistorialEntry[]
  onSelect: (entry: HistorialEntry) => void
  isLoading: boolean
}

export function QueryHistory({ historial, onSelect, isLoading }: Props) {
  if (isLoading) {
    return <div className="p-4 text-sm text-gray-400">Cargando historial...</div>
  }

  if (historial.length === 0) {
    return <div className="p-4 text-sm text-gray-400">Sin consultas ejecutadas aún</div>
  }

  return (
    <div className="space-y-1 max-h-64 overflow-y-auto">
      {historial.map(entry => (
        <button
          key={entry.id}
          onClick={() => onSelect(entry)}
          className="w-full text-left p-3 rounded-lg hover:bg-gray-50 border border-transparent hover:border-gray-100 transition-colors"
        >
          <div className="flex items-center gap-2 mb-1">
            <span className="text-[10px] font-mono text-gray-400">{entry.consulta_id}</span>
            <span className="text-xs text-gray-500">{entry.consulta_nombre}</span>
          </div>
          <div className="flex items-center gap-3 text-[10px] text-gray-400">
            <span className="flex items-center gap-0.5">
              <Clock className="w-3 h-3" />
              {new Date(entry.timestamp).toLocaleString()}
            </span>
            <span className="flex items-center gap-0.5">
              <Hash className="w-3 h-3" />
              {entry.total_registros}
            </span>
            <span>{entry.tiempo_ms.toFixed(0)}ms</span>
          </div>
        </button>
      ))}
    </div>
  )
}
