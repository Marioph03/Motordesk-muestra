import { Vehiculo } from './vehiculo';

export interface VehiculoPage {

  items: Vehiculo[];

  total: number;

  page: number;

  size: number;

}
/** Resultado paginado de vehículos con la información necesaria para listados. */
