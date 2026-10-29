export interface FacturaLineaCreate {

  origen: string;

  descripcion: string;

  cantidad: number;

  precio_unitario: number;

  descuento_porcentaje: number;

  iva: number;

  categoria_fiscal?: 'VENTA_SERVICIO' | 'COMISION_SUJETA' | 'COMISION_EXENTA';

  motivo_exencion?: string | null;

}
/** Datos enviados al añadir una línea a una factura en borrador. */
