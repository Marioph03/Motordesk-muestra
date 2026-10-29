export interface VehiculoCreate {

  cliente_id: number;

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
/** Datos de alta de vehículo asociados a un cliente existente. */
