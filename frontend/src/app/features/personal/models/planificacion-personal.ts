export interface BloquePlanificacion {
  tipo: string;
  inicio: string;
  fin: string;
  referencia: string;
  id: number;
}

export interface UsuarioPlanificacion {
  usuario_id: number;
  nombre: string;
  apellidos: string;
  rol: string;
  bloques: BloquePlanificacion[];
}
/** Asignaciones y ausencias que componen la planificación visual del equipo. */
