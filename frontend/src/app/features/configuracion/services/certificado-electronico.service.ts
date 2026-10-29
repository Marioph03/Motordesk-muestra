import { inject, Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

import { API_URL } from '../../../core/tokens/api.token';
import { CertificadoElectronicoEstado } from '../models/certificado-electronico';

@Injectable({ providedIn: 'root' })
export class CertificadoElectronicoService {
  private readonly http = inject(HttpClient);
  private readonly apiUrl = `${inject(API_URL)}/configuracion/certificado-electronico`;

  obtenerEstado(): Observable<CertificadoElectronicoEstado> {
    return this.http.get<CertificadoElectronicoEstado>(`${this.apiUrl}/estado`);
  }

  subir(archivo: File, password: string): Observable<unknown> {
    const datos = new FormData();
    datos.append('archivo', archivo);
    datos.append('password', password);
    return this.http.post(this.apiUrl, datos);
  }

  eliminar(): Observable<void> {
    return this.http.delete<void>(this.apiUrl);
  }
}

/** Cliente HTTP del certificado electrónico; la contraseña nunca se conserva. */
