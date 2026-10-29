export interface CertificadoElectronicoEstado {
  configurado: boolean;
  activo: boolean;
  nombre_archivo?: string | null;
  titular?: string | null;
  nif_titular?: string | null;
  emisor?: string | null;
  fecha_validez_desde?: string | null;
  fecha_caducidad?: string | null;
  caducado: boolean;
}

/** Estado no sensible del certificado fiscal configurado para el taller. */
