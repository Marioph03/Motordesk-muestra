import { Permiso } from './permiso';

export interface Rol {
  id: number;
  nombre: string;
  descripcion?: string | null;
  activo: boolean;
  permisos: Permiso[];
}

export interface RolGuardar {
  nombre?: string;
  descripcion?: string | null;
  activo?: boolean;
  permisos_ids?: number[];
}
/** Rol administrable con sus permisos efectivos y estado de activación. */
