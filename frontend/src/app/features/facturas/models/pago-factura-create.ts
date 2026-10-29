export interface PagoFacturaCreate {
  importe: number;
  metodo_pago: string;
  referencia?: string | null;
  observaciones?: string | null;
}
/** Datos necesarios para registrar un cobro sobre una factura. */
