export interface Permiso {
  id: number;
  codigo: string;
  nombre: string;
  modulo: string;
  descripcion?: string | null;
}
/** Permiso granular configurable y agrupado por módulo de MotorDesk. */
