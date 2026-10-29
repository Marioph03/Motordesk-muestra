import { Orden } from './orden';

export interface OrdenPage {

  items: Orden[];

  total: number;

  page: number;

  size: number;

  pages: number;

}
/** Resultado paginado de órdenes de reparación para el listado principal. */
