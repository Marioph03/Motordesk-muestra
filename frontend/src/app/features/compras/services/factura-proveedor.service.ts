import { inject, Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

import { API_URL } from '../../../core/tokens/api.token';
import { CrearFacturaProveedor, FacturaProveedor } from '../models/factura-proveedor';

@Injectable({ providedIn: 'root' })
export class FacturaProveedorService {
  private readonly http = inject(HttpClient);
  private readonly apiUrl = `${inject(API_URL)}/facturas-proveedor`;

  listar(): Observable<FacturaProveedor[]> {
    return this.http.get<FacturaProveedor[]>(this.apiUrl);
  }

  obtener(id: number): Observable<FacturaProveedor> {
    return this.http.get<FacturaProveedor>(`${this.apiUrl}/${id}`);
  }

  crear(datos: CrearFacturaProveedor): Observable<FacturaProveedor> {
    return this.http.post<FacturaProveedor>(this.apiUrl, datos);
  }

  marcarPagada(id: number, fechaPago?: string | null): Observable<FacturaProveedor> {
    return this.http.post<FacturaProveedor>(`${this.apiUrl}/${id}/pagar`, {
      fecha_pago: fechaPago || null,
    });
  }

  subirPdf(id: number, archivo: File): Observable<FacturaProveedor> {
    const formData = new FormData();
    formData.append('archivo', archivo);
    return this.http.post<FacturaProveedor>(`${this.apiUrl}/${id}/pdf`, formData);
  }

  descargarPdf(id: number): Observable<Blob> {
    return this.http.get(`${this.apiUrl}/${id}/pdf`, { responseType: 'blob' });
  }

  getPdfUrl(id: number): string {
    return `${this.apiUrl}/${id}/pdf`;
  }
}
/** Cliente HTTP de facturas proveedor, asociación de albaranes y PDF adjunto. */
