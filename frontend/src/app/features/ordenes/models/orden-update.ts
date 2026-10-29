import { VehicleDamage } from './../components/estado-vehiculo/components/vehicle-diagram-3d/vehicle-diagram-3d';

export interface OrdenUpdate {

  vehiculo_id?: number;

  kilometros_entrada?: number | null;

  descripcion_averia?: string;

  estado?: string;

  diagnostico?: string;

  observaciones?: string;

  observaciones_internas?: string;

  descuento_porcentaje?: number;

  tipo?: string;

  garantia?: boolean;

  garantia_meses?: number;

  vehicle_damage?: VehicleDamage;

  usuarios_ids?: number[];

}
/** Cambios parciales permitidos sobre una orden existente. */
