export interface ArchivoOrden {

  id: number;

  orden_id: number;

  nombre_original: string;

  nombre_archivo: string;

  tipo_mime: string;

  categoria: string;

  tamano: number;

  created_at: string;

}
/** Metadatos de un adjunto almacenado en el expediente de una orden. */
