import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';

import { API_URL } from '../../../core/tokens/api.token';
import { AusenciaPersonal } from '../models/ausencia-personal';

export interface AusenciaPersonalGuardar {
  usuario_id?: number;
  tipo: string;
  fecha_inicio: string;
  fecha_fin: string;
  observaciones?: string | null;
}

@Injectable({ providedIn: 'root' })
export class AusenciasPersonalService {
  private readonly http = inject(HttpClient);
  private readonly apiUrl = `${inject(API_URL)}/ausencias-personal`;

  getAusenciasUsuario(usuarioId: number) {
    return this.http.get<AusenciaPersonal[]>(this.apiUrl, {
      params: { usuario_id: usuarioId }
    });
  }

  crearAusencia(datos: Required<AusenciaPersonalGuardar>) {
    return this.http.post<AusenciaPersonal>(this.apiUrl, datos);
  }

  actualizarAusencia(
    ausenciaId: number,
    datos: AusenciaPersonalGuardar
  ) {
    const { usuario_id, ...cambios } = datos;
    return this.http.patch<AusenciaPersonal>(
      `${this.apiUrl}/${ausenciaId}`,
      cambios
    );
  }

  eliminarAusencia(ausenciaId: number) {
    return this.http.delete<void>(`${this.apiUrl}/${ausenciaId}`);
  }
}
/** Cliente HTTP del historial de ausencias y vacaciones del equipo. */
