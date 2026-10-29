import { UsuarioSimple } from './usuario_simple';

export interface Actividad {

  id: number;
  usuario: UsuarioSimple;

  empresa_id: number;

  usuario_id: number;

  modulo: string;

  accion: string;

  registro_id?: number;

  descripcion: string;

  ip?: string;

  created_at: string;

}
/** Evento auditable que representa una acción funcional realizada en MotorDesk. */
