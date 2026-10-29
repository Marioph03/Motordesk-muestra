import { Actividad } from './actividad';

export interface ActividadPage {

  items: Actividad[];

  total: number;

  page: number;

  size: number;

  pages: number;

}
/** Resultado paginado de eventos de actividad para la interfaz de auditoría. */
