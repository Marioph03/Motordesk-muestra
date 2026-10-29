import { Factura } from './factura';

export interface FacturaPage {

  items: Factura[];

  total: number;

  page: number;

  size: number;

  pages: number;

}
/** Resultado paginado del listado de facturas y sus metadatos de navegación. */
