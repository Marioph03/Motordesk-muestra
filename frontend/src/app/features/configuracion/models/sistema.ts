export interface EstadoServicio {
  nombre: string;
  estado: string;
  detalle?: string | null;
}

export interface EstadoSistema {
  version: string;
  backend: EstadoServicio;
  base_datos: EstadoServicio;
  whatsapp: EstadoServicio;
  verifactu: EstadoServicio;
}

export interface BackupInfo {
  disponible: boolean;
  nombre_archivo?: string | null;
  fecha?: string | null;
  tamano_bytes?: number | null;
}
/** Estado y operaciones administrativas disponibles en Configuración de sistema. */
