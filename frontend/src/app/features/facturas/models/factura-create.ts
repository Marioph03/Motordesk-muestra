export interface FacturaCreate {

  tipo_documento: string;

  tipo_factura: string;

  cliente_id: number;

  vehiculo_id?: number;

  orden_id?: number;

  descuento_porcentaje: number;

  iva: number;

  observaciones?: string;

}
/** Datos de borrador necesarios para crear una factura desde una orden o garantía. */
