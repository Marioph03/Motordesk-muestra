export interface CitaCreate {
  cliente_id: number;
  vehiculo_id: number;
  usuarios_ids?: number[];

  fecha_inicio: string;
  fecha_fin: string;

  motivo: string;
  observaciones?: string | null;
}
/** Datos mínimos enviados al backend para solicitar una nueva cita. */
