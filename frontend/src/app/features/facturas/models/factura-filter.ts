/** Filtros disponibles para el listado paginado de facturas. */
export interface FacturaFilter {
  fecha_desde?: string;
  fecha_hasta?: string;
  total_desde?: number;
  total_hasta?: number;
  cliente_id?: number;
  tipo_documento?: string;
}
