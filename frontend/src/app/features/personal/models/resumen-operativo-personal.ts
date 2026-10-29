import { AusenciaPersonal } from './ausencia-personal';

export interface CitaOperativaPersonal {
  id: number;
  fecha_inicio: string;
  fecha_fin: string;
  motivo: string;
  estado: string;
  vehiculo_descripcion: string;
}

export interface OrdenOperativaPersonal {
  id: number;
  numero: string;
  tipo: string;
  estado: string;
  descripcion_averia: string;
}

export interface ResumenOperativoPersonal {
  usuario_id: number;
  citas: CitaOperativaPersonal[];
  ordenes: OrdenOperativaPersonal[];
  ausencias: AusenciaPersonal[];
}
/** Citas, órdenes y próximas ausencias relevantes para una ficha personal. */
