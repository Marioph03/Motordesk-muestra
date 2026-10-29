import { HttpClient } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { Observable } from 'rxjs';

import { API_URL } from '../../../core/tokens/api.token';

import { Pieza } from '../models/pieza';
import { PiezaCreate } from '../models/pieza-create';
import { PiezaUpdate } from '../models/pieza-update';

@Injectable({
  providedIn: 'root'
})
export class PiezasService {

  private http = inject(HttpClient);

  private apiUrl = inject(API_URL);

  getByOrden(
    orden_id: number
  ): Observable<Pieza[]> {

    return this.http.get<Pieza[]>(
      `${this.apiUrl}/ordenes-reparacion/${orden_id}/piezas/`
    );

  }

  create(
    ordenId: number,
    pieza: PiezaCreate
  ) {

    return this.http.post<Pieza>(
      `${this.apiUrl}/ordenes-reparacion/${ordenId}/piezas/`,
      pieza
    );

  }

  update(
    ordenId: number,
    piezaId: number,
    pieza: PiezaUpdate
  ) {

    return this.http.patch<Pieza>(
      `${this.apiUrl}/ordenes-reparacion/${ordenId}/piezas/${piezaId}`,
      pieza
    );

  }

  delete(
    ordenId: number,
    piezaId: number
  ) {

    return this.http.delete(
      `${this.apiUrl}/ordenes-reparacion/${ordenId}/piezas/${piezaId}`
    );

  }

}
/** Cliente HTTP de piezas de orden y operaciones de almacén relacionadas. */
