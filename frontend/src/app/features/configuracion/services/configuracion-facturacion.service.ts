import { inject, Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

import { API_URL } from '../../../core/tokens/api.token';
import {
  ConfiguracionFacturacion,
  ConfiguracionFacturacionUpdate,
} from '../models/configuracion-facturacion';

@Injectable({ providedIn: 'root' })
export class ConfiguracionFacturacionService {
  private readonly http = inject(HttpClient);
  private readonly apiUrl = `${inject(API_URL)}/configuracion/facturacion`;

  obtener(): Observable<ConfiguracionFacturacion> {
    return this.http.get<ConfiguracionFacturacion>(this.apiUrl);
  }

  actualizar(datos: ConfiguracionFacturacionUpdate): Observable<ConfiguracionFacturacion> {
    return this.http.put<ConfiguracionFacturacion>(this.apiUrl, datos);
  }
}
/** Cliente HTTP de las preferencias fiscales centralizadas del taller. */
