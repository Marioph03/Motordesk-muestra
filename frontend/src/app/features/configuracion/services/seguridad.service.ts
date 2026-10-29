import { inject, Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

import { API_URL } from '../../../core/tokens/api.token';
import { CambiarPasswordRequest, SeguridadUsuario } from '../models/seguridad';

@Injectable({ providedIn: 'root' })
export class SeguridadService {
  private readonly http = inject(HttpClient);
  private readonly apiUrl = `${inject(API_URL)}/configuracion/seguridad`;

  getMiCuenta(): Observable<SeguridadUsuario> {
    return this.http.get<SeguridadUsuario>(`${this.apiUrl}/mi-cuenta`);
  }

  cambiarPassword(datos: CambiarPasswordRequest): Observable<{ message: string }> {
    return this.http.post<{ message: string }>(`${this.apiUrl}/cambiar-password`, datos);
  }
}
/** Cliente HTTP de datos de seguridad y cambio de contraseña de la sesión actual. */
