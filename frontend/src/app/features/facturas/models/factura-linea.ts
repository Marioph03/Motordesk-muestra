export interface FacturaLinea {

  id: number;

  factura_id: number;

  origen: string;

  descripcion: string;

  cantidad: number;

  precio_unitario: number;

  descuento_porcentaje: number;

  subtotal: number;

  iva: number;

  categoria_fiscal: 'VENTA_SERVICIO' | 'COMISION_SUJETA' | 'COMISION_EXENTA';

  motivo_exencion?: string | null;

  total: number;

  created_at: string;

  updated_at: string;

}
/** Línea económica de factura con cantidad, impuesto e importe calculado. */
