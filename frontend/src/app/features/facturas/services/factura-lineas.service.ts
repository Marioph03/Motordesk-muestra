import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';

import { Observable } from 'rxjs';

import { API_URL } from '../../../core/tokens/api.token';

import { FacturaLinea } from '../models/factura-linea';
import { FacturaLineaCreate } from '../models/factura-linea-create';
import { FacturaLineaUpdate } from '../models/factura-linea-update';

@Injectable({
  providedIn: 'root'
})
export class FacturaLineasService {

  private http = inject(HttpClient);

  private apiUrl = inject(API_URL);

  getLineas(
    facturaId: number
  ): Observable<FacturaLinea[]> {

    return this.http.get<FacturaLinea[]>(
      `${this.apiUrl}/factura-lineas/factura/${facturaId}`
    );

  }

  createLinea(
    facturaId: number,
    linea: FacturaLineaCreate
  ): Observable<FacturaLinea> {

    return this.http.post<FacturaLinea>(
      `${this.apiUrl}/factura-lineas/factura/${facturaId}`,
      linea
    );

  }

  updateLinea(
    lineaId: number,
    datos: FacturaLineaUpdate
  ): Observable<FacturaLinea> {

    return this.http.patch<FacturaLinea>(
      `${this.apiUrl}/factura-lineas/${lineaId}`,
      datos
    );

  }

  deleteLinea(
    lineaId: number
  ): Observable<void> {

    return this.http.delete<void>(
      `${this.apiUrl}/factura-lineas/${lineaId}`
    );

  }

}
/** Cliente HTTP para editar líneas de factura mientras permanece en borrador. */
