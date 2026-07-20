/**
 * QueryExport - Botones de exportación
 */
import { FileSpreadsheet, FileText } from "lucide-react"

interface Props {
  resultado: any
  consultaNombre: string
}

export function QueryExport({ resultado, consultaNombre }: Props) {
  if (!resultado) return null

  const exportCSV = () => {
    if (!resultado.datos?.length) return
    const cols = resultado.columnas
    const header = cols.join(",")
    const rows = resultado.datos.map((row: any) =>
      cols.map((c: string) => {
        const v = row[c]
        const str = String(v ?? "")
        if (str.includes(",") || str.includes('"') || str.includes("\n")) {
          return `"${str.replace(/"/g, '""')}"`
        }
        return str
      }).join(",")
    )
    const csv = [header, ...rows].join("\n")
    downloadFile(csv, consultaNombre + "_" + Date.now() + ".csv", "text/csv")
  }

  const exportJSON = () => {
    const json = JSON.stringify(resultado.datos, null, 2)
    downloadFile(json, `${consultaNombre}_${Date.now()}.json`, "application/json")
  }

  const exportExcel = () => {
    // Simple HTML table to CSV for Excel compatibility
    if (!resultado.datos?.length) return
    const cols = resultado.columnas
    const header = cols.map((c: string) => `<th>${c}</th>`).join("")
    const rows = resultado.datos.map((row: any) =>
      `<tr>${cols.map((c: string) => `<td>${row[c] ?? ""}</td>`).join("")}</tr>`
    ).join("")
    const html = `<table><thead><tr>${header}</tr></thead><tbody>${rows}</tbody></table>`
    const blob = new Blob([html], { type: "application/vnd.ms-excel" })
    const url = URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    a.download = `${consultaNombre}_${Date.now()}.xls`
    a.click()
    URL.revokeObjectURL(url)
  }

  const downloadFile = (content: string, filename: string, mime: string) => {
    const blob = new Blob([content], { type: mime })
    const url = URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    a.download = filename
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="flex items-center gap-2">
      <button
        onClick={exportCSV}
        className="flex items-center gap-1.5 px-3 py-1.5 text-xs bg-emerald-50 text-emerald-700 rounded-lg border border-emerald-200 hover:bg-emerald-100"
      >
        <FileSpreadsheet className="w-3.5 h-3.5" />
        CSV
      </button>
      <button
        onClick={exportExcel}
        className="flex items-center gap-1.5 px-3 py-1.5 text-xs bg-green-50 text-green-700 rounded-lg border border-green-200 hover:bg-green-100"
      >
        <FileSpreadsheet className="w-3.5 h-3.5" />
        Excel
      </button>
      <button
        onClick={exportJSON}
        className="flex items-center gap-1.5 px-3 py-1.5 text-xs bg-blue-50 text-blue-700 rounded-lg border border-blue-200 hover:bg-blue-100"
      >
        <FileText className="w-3.5 h-3.5" />
        JSON
      </button>
    </div>
  )
}
