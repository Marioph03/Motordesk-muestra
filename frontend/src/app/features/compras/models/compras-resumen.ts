export interface ComprasResumen {
  pedidos_total: number;
  pedidos_pendientes: number;
  albaranes_total: number;
  albaranes_borrador: number;
  facturas_total: number;
  facturas_pendientes: number;
  facturas_proximas_vencer: number;
  devoluciones_total: number;
  devoluciones_pendientes: number;
}
/** Indicadores de compra disponibles para la pantalla de resumen. */
