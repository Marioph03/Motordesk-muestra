import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

import { API_URL } from '../../../core/tokens/api.token';
import { AlbaranVenta, AlbaranVentaCreate } from '../models/albaran-venta';

@Injectable({ providedIn: 'root' })
export class AlbaranVentaService {
  private readonly http = inject(HttpClient);
  private readonly apiUrl = `${inject(API_URL)}/albaranes-venta`;

  listar(): Observable<AlbaranVenta[]> {
    return this.http.get<AlbaranVenta[]>(this.apiUrl);
  }

  obtener(id: number): Observable<AlbaranVenta> {
    return this.http.get<AlbaranVenta>(`${this.apiUrl}/${id}`);
  }

  crear(datos: AlbaranVentaCreate): Observable<AlbaranVenta> {
    return this.http.post<AlbaranVenta>(this.apiUrl, datos);
  }

  confirmar(id: number): Observable<AlbaranVenta> {
    return this.http.post<AlbaranVenta>(`${this.apiUrl}/${id}/confirmar`, {});
  }

  anular(id: number): Observable<AlbaranVenta> {
    return this.http.post<AlbaranVenta>(`${this.apiUrl}/${id}/anular`, {});
  }

  descargarPdf(id: number): Observable<Blob> {
    return this.http.get(`${this.apiUrl}/${id}/pdf`, { responseType: 'blob' });
  }
}
