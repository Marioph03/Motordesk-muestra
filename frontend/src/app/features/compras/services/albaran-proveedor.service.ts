import { inject, Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

import { API_URL } from '../../../core/tokens/api.token';
import {
  AlbaranProveedor,
  CrearAlbaranProveedor,
  LineaAlbaranDevolvible,
} from '../models/albaran-proveedor';

@Injectable({ providedIn: 'root' })
export class AlbaranProveedorService {
  private readonly http = inject(HttpClient);
  private readonly apiUrl = `${inject(API_URL)}/albaranes-proveedor`;

  listar(): Observable<AlbaranProveedor[]> {
    return this.http.get<AlbaranProveedor[]>(this.apiUrl);
  }

  getById(id: number): Observable<AlbaranProveedor> {
    return this.http.get<AlbaranProveedor>(`${this.apiUrl}/${id}`);
  }

  pdfUrl(id: number): string {
    return `${this.apiUrl}/${id}/pdf`;
  }

  getLineasDevolvibles(albaranId: number): Observable<LineaAlbaranDevolvible[]> {
    return this.http.get<LineaAlbaranDevolvible[]>(
      `${this.apiUrl}/${albaranId}/lineas-devolvibles`,
    );
  }

  crear(datos: CrearAlbaranProveedor): Observable<AlbaranProveedor> {
    return this.http.post<AlbaranProveedor>(this.apiUrl, datos);
  }

  confirmar(id: number): Observable<AlbaranProveedor> {
    return this.http.post<AlbaranProveedor>(`${this.apiUrl}/${id}/confirmar`, {});
  }

  anular(id: number): Observable<AlbaranProveedor> {
    return this.http.post<AlbaranProveedor>(`${this.apiUrl}/${id}/anular`, {});
  }
}
/** Cliente HTTP del ciclo de albaranes de proveedor y sus líneas. */
