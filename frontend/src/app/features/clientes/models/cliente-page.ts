import { Cliente } from './cliente';

export interface ClientePage {

  items: Cliente[];

  total: number;

  page: number;

  size: number;

  pages: number;

}
/** Página de clientes y metadatos de paginación del API. */
