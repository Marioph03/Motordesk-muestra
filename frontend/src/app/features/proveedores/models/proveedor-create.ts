export interface ProveedorCreate {

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

}
/** Datos necesarios para dar de alta un proveedor en el catálogo. */
