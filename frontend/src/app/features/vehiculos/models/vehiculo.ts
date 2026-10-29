import { ClienteSimple } from './cliente-simple';

export interface Vehiculo {

  id: number;

  codigo?: string;

  cliente_id: number;

  cliente: ClienteSimple;

  matricula: string;

  bastidor?: string;

  marca: string;

  modelo: string;

  version?: string;

  anio?: number;

  fecha_matriculacion?: string;

  color?: string;

  combustible?: string;

  transmision?: string;

  kilometros?: number;

  observaciones?: string;

}
/** Vehículo y datos del propietario utilizados en la operación de taller. */
