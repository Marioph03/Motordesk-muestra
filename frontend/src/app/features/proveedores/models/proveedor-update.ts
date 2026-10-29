export interface ProveedorUpdate {

  nombre?: string;

  cif?: string;

  telefono?: string;

  email?: string;

  direccion?: string;

  ciudad?: string;

  provincia?: string;

  codigo_postal?: string;

  observaciones?: string;

  activo?: boolean;

}
/** Cambios parciales permitidos sobre un proveedor existente. */
