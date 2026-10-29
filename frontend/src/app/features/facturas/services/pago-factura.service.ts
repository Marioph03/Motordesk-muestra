import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';

import { Observable } from 'rxjs';
import { API_URL } from '../../../core/tokens/api.token';

import { PagoFactura } from '../models/pago-factura';
import { PagoFacturaCreate } from '../models/pago-factura-create';
import { PagoFacturaResumen } from '../models/pago-factura-resumen';


@Injectable({
  providedIn: 'root'
})
export class PagoFacturaService {

  private http = inject(HttpClient);

  private apiUrl =
    `${inject(API_URL)}/pagos-factura`;


  getPagos(
    facturaId: number
  ): Observable<PagoFactura[]> {

    return this.http.get<PagoFactura[]>(
      `${this.apiUrl}/factura/${facturaId}`
    );

  }


  getResumen(
    facturaId: number
  ): Observable<PagoFacturaResumen> {

    return this.http.get<PagoFacturaResumen>(
      `${this.apiUrl}/factura/${facturaId}/resumen`
    );

  }


  crearPago(
    facturaId: number,
    pago: PagoFacturaCreate
  ): Observable<PagoFactura> {

    return this.http.post<PagoFactura>(
      `${this.apiUrl}/factura/${facturaId}`,
      pago
    );

  }


  eliminarPago(
    pagoId: number
  ): Observable<void> {

    return this.http.delete<void>(
      `${this.apiUrl}/${pagoId}`
    );

  }

}
/** Cliente de pagos de factura, fuente de la deuda pendiente exacta. */
