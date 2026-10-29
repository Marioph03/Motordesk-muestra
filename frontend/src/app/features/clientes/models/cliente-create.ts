export interface ClienteCreate {

  nombre: string;

  apellidos: string;

  dni: string;

  telefono: string;

  email: string;

  direccion: string;

  ciudad: string;

  provincia: string;

  codigo_postal: string;

  observaciones: string;

  activo: boolean;

}
/** Datos de alta de cliente separados de campos calculados por el backend. */
