import { inject, Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

import { API_URL } from '../../../core/tokens/api.token';
import { ConfiguracionNotificaciones } from '../models/configuracion-notificaciones';

@Injectable({ providedIn: 'root' })
export class ConfiguracionNotificacionesService {
  private readonly http = inject(HttpClient);
  private readonly apiUrl = `${inject(API_URL)}/configuracion/notificaciones`;

  getConfiguracion(): Observable<ConfiguracionNotificaciones> {
    return this.http.get<ConfiguracionNotificaciones>(this.apiUrl);
  }

  actualizar(
    datos: Omit<ConfiguracionNotificaciones, 'id'>,
  ): Observable<ConfiguracionNotificaciones> {
    return this.http.put<ConfiguracionNotificaciones>(this.apiUrl, datos);
  }
}
/** Cliente HTTP de preferencias que activan alertas del Dashboard. */
