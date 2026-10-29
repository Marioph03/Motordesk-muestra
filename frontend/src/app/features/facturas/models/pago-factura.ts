export interface PagoFactura {
  id: number;
  factura_id: number;
  importe: number;
  metodo_pago: string;
  referencia?: string | null;
  observaciones?: string | null;
  fecha_pago: string;
  created_at: string;
}
/** Pago persistido de una factura, utilizado para saldo pendiente y cobros. */
