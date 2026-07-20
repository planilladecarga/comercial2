/**
 * Tipos TypeScript para el Centro de Comando Comercial
 */

export interface ResumenEjecutivo {
  fecha_actualizacion: string
  cantidad_movimientos: number
  kg_totales: number
  exportaciones_kg: number
  deposito_kg: number
  cantidad_empresas: number
  cantidad_productoras: number
  cantidad_certificadores: number
  cantidad_depositos: number
  cantidad_mercados: number
  cantidad_productos: number
}

export interface Alerta {
  tipo: string
  entidad: string
  nombre: string
  detalle: string
  magnitud?: number
}

export interface AlertasDia {
  clientes_perdidos: Alerta[]
  clientes_nuevos: Alerta[]
  mercados_nuevos: Alerta[]
  mercados_perdidos: Alerta[]
  productores_nuevos: Alerta[]
  productores_inactivos: Alerta[]
  aumentos_importantes: Alerta[]
  disminuciones_importantes: Alerta[]
  cambios_deposito: Alerta[]
}

export interface Oportunidad {
  tipo: string
  ranking: number
  nombre: string
  kg: number
  detalle: string
}

export interface Oportunidades {
  top_20_productores_potenciales: Oportunidad[]
  mercados_no_participa: Oportunidad[]
  productores_competencia: Oportunidad[]
  productores_compartidos: Oportunidad[]
  clientes_potenciales: Oportunidad[]
}

export interface ComparacionEmpresa {
  kg: number
  participacion_pct: number
  mercados_count: number
  clientes_count: number
  productos_count: number
  productores_count: number
}

export interface Competencia {
  empresa_a: string
  empresa_b: string
  kg_a: number
  kg_b: number
  participacion_a: number
  participacion_b: number
  comparacion: {
    a: ComparacionEmpresa
    b: ComparacionEmpresa
  }
}

export interface KPI {
  codigo: string
  nombre: string
  valor: number
  unidad: string
  estado: "critico" | "advertencia" | "ok"
  tendencia: "up" | "down" | "stable"
  detalle: string
}

export interface Indicadores {
  indice_diversificacion: KPI
  indice_riesgo: KPI
  indice_competencia: KPI
  indice_fidelidad: KPI
  indice_crecimiento: KPI
  indice_oportunidad: KPI
}

export interface PaisData {
  pais: string
  kg: number
  participacion_pct: number
  crecimiento_pct: number
}

export interface MapaComercial {
  paises: PaisData[]
  total_kg: number
}

export interface MesData {
  anio: number
  mes: number
  nombre_mes: string
  kg: number
  clientes_count: number
  mercados_count: number
  productores_count: number
}

export interface Evolucion {
  meses: MesData[]
}

export interface RankingItem {
  ranking: number
  nombre: string
  kg: number
  cantidad: number
}

export interface Rankings {
  top_productores: RankingItem[]
  top_depositos: RankingItem[]
  top_certificadores: RankingItem[]
  top_mercados: RankingItem[]
  top_productos: RankingItem[]
}

export interface FiltrosDisponibles {
  anos: number[]
  meses: { mes: number; nombre: string }[]
  productores: { nro: string; nombre: string }[]
  certificadores: { id: number; nombre: string }[]
  depositos: { id: number; nombre: string }[]
  mercados: string[]
  productos: { id: number; nombre: string; categoria: string }[]
  temperaturas: number[]
  tipos_movimiento: string[]
}

export interface Comando360Data {
  resumen: ResumenEjecutivo
  alertas: AlertasDia
  oportunidades: Oportunidades
  competencia: Competencia | null
  indicadores: Indicadores
  mapa: MapaComercial
  evolucion: Evolucion
  rankings: Rankings
  filtros: FiltrosDisponibles
}
