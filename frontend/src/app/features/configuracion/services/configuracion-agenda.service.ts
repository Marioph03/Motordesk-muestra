import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

import { API_URL } from '../../../core/tokens/api.token';
import { CierreAgenda, ConfiguracionAgenda } from '../models/configuracion-agenda';

@Injectable({ providedIn: 'root' })
export class ConfiguracionAgendaService {
  private readonly http = inject(HttpClient);
  private readonly apiUrl = `${inject(API_URL)}/configuracion/agenda`;

  getConfiguracion(): Observable<ConfiguracionAgenda> {
    return this.http.get<ConfiguracionAgenda>(this.apiUrl);
  }

  actualizar(datos: Omit<ConfiguracionAgenda, 'id'>): Observable<ConfiguracionAgenda> {
    return this.http.put<ConfiguracionAgenda>(this.apiUrl, datos);
  }

  getCierres(): Observable<CierreAgenda[]> {
    return this.http.get<CierreAgenda[]>(`${this.apiUrl}/cierres`);
  }

  crearCierre(datos: Pick<CierreAgenda, 'fecha' | 'motivo' | 'observaciones'>): Observable<CierreAgenda> {
    return this.http.post<CierreAgenda>(`${this.apiUrl}/cierres`, datos);
  }

  eliminarCierre(cierreId: number): Observable<void> {
    return this.http.delete<void>(`${this.apiUrl}/cierres/${cierreId}`);
  }
}
/** Cliente HTTP de horario, cierres y duración predeterminada de citas. */
