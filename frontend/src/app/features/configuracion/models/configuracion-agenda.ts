export interface ConfiguracionAgenda {
  id: number;
  duracion_cita_minutos: number;
  lunes_activo: boolean; lunes_inicio: string; lunes_fin: string;
  martes_activo: boolean; martes_inicio: string; martes_fin: string;
  miercoles_activo: boolean; miercoles_inicio: string; miercoles_fin: string;
  jueves_activo: boolean; jueves_inicio: string; jueves_fin: string;
  viernes_activo: boolean; viernes_inicio: string; viernes_fin: string;
  sabado_activo: boolean; sabado_inicio: string; sabado_fin: string;
  domingo_activo: boolean; domingo_inicio: string; domingo_fin: string;
}

export interface CierreAgenda {
  id: number;
  fecha: string;
  motivo: string;
  observaciones?: string | null;
}
/** Horario, duración y cierres que determinan cuándo puede reservarse una cita. */
