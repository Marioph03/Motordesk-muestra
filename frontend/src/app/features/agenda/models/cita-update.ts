export interface CitaUpdate {
  cliente_id?: number;
  vehiculo_id?: number;
  usuarios_ids?: number[];

  fecha_inicio?: string;
  fecha_fin?: string;

  motivo?: string;
  observaciones?: string | null;

}
/** Cambios parciales permitidos en una cita ya existente. */
