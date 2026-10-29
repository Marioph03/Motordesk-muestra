export interface ManoObra {
  id: number;
  orden_id: number;
  concepto: string;
  codigo_mano_obra?: string | null;
  horas: number;
  precio_hora: number;
  total: number;
  cubierto_garantia: boolean;
}
/** Trabajo de mano de obra persistido dentro de una orden de reparación. */
