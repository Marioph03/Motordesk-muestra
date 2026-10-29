export interface FacturaLineaUpdate {

  descripcion?: string;

  cantidad?: number;

  precio_unitario?: number;

  descuento_porcentaje?: number;

  iva?: number;

  categoria_fiscal?: 'VENTA_SERVICIO' | 'COMISION_SUJETA' | 'COMISION_EXENTA';

  motivo_exencion?: string | null;

}
/** Cambios parciales permitidos sobre una línea de factura editable. */
