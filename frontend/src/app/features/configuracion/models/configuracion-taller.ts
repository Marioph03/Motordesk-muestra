export interface ConfiguracionTaller {
  id: number;
  nombre_comercial?: string | null;
  razon_social?: string | null;
  nif_cif?: string | null;
  telefono?: string | null;
  email?: string | null;
  web?: string | null;
  direccion?: string | null;
  codigo_postal?: string | null;
  localidad?: string | null;
  provincia?: string | null;
  pais?: string | null;
  logo_url?: string | null;
}
/** Identidad y datos de contacto corporativos editables desde Configuración. */
