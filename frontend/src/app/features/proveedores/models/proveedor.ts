export interface Proveedor {

  id: number;

  codigo?: string;

  nombre: string;

  cif: string;

  telefono?: string;

  email?: string;

  direccion?: string;

  ciudad?: string;

  provincia?: string;

  codigo_postal?: string;

  observaciones?: string;

  activo: boolean;

  created_at: string;

  updated_at: string;

}
/** Proveedor de recambios y su información de contacto y estado. */
