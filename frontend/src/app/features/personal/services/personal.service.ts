import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { HttpParams } from '@angular/common/http';

import { API_URL } from '../../../core/tokens/api.token';
import { Personal } from '../models/personal';
import { AusenciaPersonal } from '../models/ausencia-personal';
import { UsuarioPlanificacion } from '../models/planificacion-personal';
import { ResumenOperativoPersonal } from '../models/resumen-operativo-personal';
import { RegistroJornada } from '../models/registro-jornada';

export interface PersonalUpdate {
  nombre: string;
  apellidos: string;
  email: string;
  rol: string;
  activo: boolean;
}

export interface PersonalCreate extends PersonalUpdate {
  password: string;
}

export interface DisponibilidadPersonal {
  usuario_id: number;
  nombre: string;
  apellidos: string;
  rol: string;
  disponible: boolean;
  motivo?: string | null;
  conflicto_tipo?: string | null;
  conflicto_id?: number | null;
  conflicto_referencia?: string | null;
}

// Alias temporal para los componentes que ya consumían este contrato.
export type DisponibilidadUsuario = DisponibilidadPersonal;

@Injectable({ providedIn: 'root' })
export class PersonalService {
  private readonly http = inject(HttpClient);
  private readonly baseApiUrl = inject(API_URL);
  private readonly apiUrl = `${this.baseApiUrl}/usuarios`;

  getPersonal() {
    return this.http.get<Personal[]>(`${this.apiUrl}/`);
  }

  getUsuario(usuarioId: number) {
    return this.http.get<Personal>(`${this.apiUrl}/${usuarioId}`);
  }

  actualizarUsuario(usuarioId: number, datos: PersonalUpdate) {
    return this.http.patch<Personal>(`${this.apiUrl}/${usuarioId}`, datos);
  }

  crearUsuario(datos: PersonalCreate) {
    return this.http.post<Personal>(`${this.apiUrl}/`, datos);
  }

  getAusencias() {
    return this.http.get<AusenciaPersonal[]>(
      `${this.baseApiUrl}/ausencias-personal`
    );
  }

  getDisponibilidad(
    fechaInicio: string,
    fechaFin: string,
    excluirCitaId?: number,
    excluirOrdenId?: number
  ) {
    let params = new HttpParams()
      .set('fecha_inicio', fechaInicio)
      .set('fecha_fin', fechaFin);

    if (excluirCitaId != null) {
      params = params.set('excluir_cita_id', excluirCitaId);
    }

    if (excluirOrdenId != null) {
      params = params.set('excluir_orden_id', excluirOrdenId);
    }

    return this.http.get<DisponibilidadUsuario[]>(
      `${this.baseApiUrl}/personal/disponibilidad`,
      { params }
    );
  }

  getPlanificacion(
    fechaInicio: string,
    fechaFin: string
  ) {
    const params = new HttpParams()
      .set('fecha_inicio', fechaInicio)
      .set('fecha_fin', fechaFin);

    return this.http.get<UsuarioPlanificacion[]>(
      `${this.baseApiUrl}/personal/planificacion`,
      { params }
    );
  }

  getResumenOperativo(
    usuarioId: number
  ) {
    return this.http.get<ResumenOperativoPersonal>(
      `${this.apiUrl}/${usuarioId}/resumen-operativo`
    );
  }

  getRegistrosJornada(mes: string) {
    return this.http.get<RegistroJornada[]>(`${this.baseApiUrl}/personal/jornadas`, { params: { mes } });
  }

  marcarJornada(usuario_id: number, fecha: string, presente: boolean) {
    return this.http.post<RegistroJornada>(`${this.baseApiUrl}/personal/jornadas/marcar`, { usuario_id, fecha, presente });
  }

  actualizarHorarioJornada(usuarioId: number, hora_entrada: string, hora_salida: string) {
    return this.http.patch(`${this.baseApiUrl}/personal/jornadas/horario/${usuarioId}`, { hora_entrada, hora_salida });
  }

  descargarRegistroJornada(mes: string) {
    return this.http.get(`${this.baseApiUrl}/personal/jornadas/pdf`, { params: { mes }, responseType: 'blob' });
  }
}
/** Cliente HTTP de personal, disponibilidad y resumen operativo individual. */
