import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

import { API_URL } from '../../../core/tokens/api.token';
import { ConfiguracionDocumentos } from '../models/configuracion-documentos';

@Injectable({ providedIn: 'root' })
export class ConfiguracionDocumentosService {
  private readonly http = inject(HttpClient);
  private readonly apiUrl = `${inject(API_URL)}/configuracion/documentos`;

  getConfiguracion(): Observable<ConfiguracionDocumentos> {
    return this.http.get<ConfiguracionDocumentos>(this.apiUrl);
  }

  actualizar(
    datos: Omit<ConfiguracionDocumentos, 'id'>,
  ): Observable<ConfiguracionDocumentos> {
    return this.http.put<ConfiguracionDocumentos>(this.apiUrl, datos);
  }
}
/** Cliente HTTP de preferencias que se reflejan en documentos generados. */
