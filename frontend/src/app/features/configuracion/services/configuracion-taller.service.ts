/** Mantiene la identidad corporativa que reutilizan vistas y documentos PDF. */
import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

import { API_URL } from '../../../core/tokens/api.token';
import { ConfiguracionTaller } from '../models/configuracion-taller';

@Injectable({ providedIn: 'root' })
export class ConfiguracionTallerService {
  private readonly http = inject(HttpClient);
  private readonly backendUrl = inject(API_URL);
  private readonly apiUrl = `${this.backendUrl}/configuracion/taller`;

  getConfiguracion(): Observable<ConfiguracionTaller> {
    return this.http.get<ConfiguracionTaller>(this.apiUrl);
  }

  actualizar(datos: Partial<ConfiguracionTaller>): Observable<ConfiguracionTaller> {
    return this.http.put<ConfiguracionTaller>(this.apiUrl, datos);
  }

  subirLogo(archivo: File): Observable<ConfiguracionTaller> {
    // Multipart deja que el navegador establezca el boundary correcto.
    const datos = new FormData();
    datos.append('archivo', archivo);
    return this.http.post<ConfiguracionTaller>(`${this.apiUrl}/logo`, datos);
  }

  getLogoUrl(logoUrl?: string | null): string | null {
    // El backend guarda rutas públicas relativas; la vista necesita una URL completa.
    if (!logoUrl) {
      return null;
    }
    return logoUrl.startsWith('http://') || logoUrl.startsWith('https://')
      ? logoUrl
      : `${this.backendUrl}${logoUrl}`;
  }
}
