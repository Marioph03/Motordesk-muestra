export interface ManoObraCreate {
  concepto: string;
  codigo_mano_obra?: string | null;
  horas: number;
  precio_hora: number;
  cubierto_garantia?: boolean;
}
/** Datos enviados para imputar un nuevo trabajo de mano de obra. */
