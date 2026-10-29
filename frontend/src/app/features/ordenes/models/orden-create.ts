import { VehicleDamage } from './vehicle-damage';

export interface OrdenCreate {
  tipo: string;
  vehiculo_id: number;
  kilometros_entrada?: number | null;
  descripcion_averia: string;
  estado: string;
  diagnostico?: string;
  observaciones?: string;
  observaciones_internas?: string;
  usuarios_ids?: number[];
  garantia?: boolean;
  garantia_meses?: number | null;
  vehicle_damage?: VehicleDamage;
}
/** Datos iniciales para abrir una orden de reparación. */
