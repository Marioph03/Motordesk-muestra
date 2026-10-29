export interface Cita {
  id: number;

  cliente_id: number;
  vehiculo_id: number;

  fecha_inicio: string;
  fecha_fin: string;

  motivo: string;
  observaciones?: string | null;

  estado: string;

  orden_generada_id?: number | null;
  fecha_confirmacion?: string | null;
  canal_confirmacion?: string | null;
  fecha_recordatorio?: string | null;
  canal_recordatorio?: string | null;
  fecha_reprogramacion?: string | null;
  fecha_inicio_anterior?: string | null;
  fecha_fin_anterior?: string | null;

  cliente: ClienteCita;
  vehiculo: VehiculoCita;
  usuarios_asignados: UsuarioCita[];

  created_at: string;
  updated_at: string;
}

export interface UsuarioCita {
  id: number;
  nombre: string;
  apellidos: string;
  rol: string;
}

export interface ClienteCita {
  id: number;
  nombre: string;
  apellidos?: string | null;
}

export interface VehiculoCita {
  id: number;
  marca?: string | null;
  modelo?: string | null;
  matricula?: string | null;
}
/** Cita de agenda enriquecida con cliente, vehículo y personal asignado. */
