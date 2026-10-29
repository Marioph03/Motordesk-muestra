export interface ConfiguracionNotificaciones {
  id: number;
  stock_bajo: boolean;
  pedidos_pendientes: boolean;
  garantias_pendientes: boolean;
  presupuestos_pendientes: boolean;
  citas_proximas: boolean;
  ausencias_personal: boolean;
}
/** Interruptores que habilitan cada categoría de alerta del Dashboard. */
