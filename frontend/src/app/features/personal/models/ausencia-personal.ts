export interface AusenciaPersonal {
  id: number;

  usuario_id: number;

  tipo: string;

  fecha_inicio: string;
  fecha_fin: string;

  observaciones?: string | null;

  created_at: string;
  updated_at: string;
}
/** Intervalo de ausencia que afecta a la disponibilidad de una persona. */
