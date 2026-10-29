import { HttpClient } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { Observable } from 'rxjs';

import { API_URL } from '../../../core/tokens/api.token';

import { ManoObra } from '../models/mano-obra';
import { ManoObraCreate } from '../models/mano-obra-create';
import { ManoObraUpdate } from '../models/mano-obra-update';

@Injectable({
  providedIn: 'root'
})
export class ManoObraService {

  private http = inject(HttpClient);

  private apiUrl = inject(API_URL);

  getByOrden(
    ordenId: number
  ): Observable<ManoObra[]> {

    return this.http.get<ManoObra[]>(
      `${this.apiUrl}/ordenes-reparacion/${ordenId}/mano-obra/`
    );

  }

  create(
    ordenId: number,
    manoObra: ManoObraCreate
  ) {

    return this.http.post<ManoObra>(
      `${this.apiUrl}/ordenes-reparacion/${ordenId}/mano-obra/`,
      manoObra
    );

  }

  update(
    ordenId: number,
    lineaId: number,
    manoObra: ManoObraUpdate
  ) {

    return this.http.patch<ManoObra>(
      `${this.apiUrl}/ordenes-reparacion/${ordenId}/mano-obra/${lineaId}`,
      manoObra
    );

  }

  delete(
    ordenId: number,
    lineaId: number
  ) {

    return this.http.delete(
      `${this.apiUrl}/ordenes-reparacion/${ordenId}/mano-obra/${lineaId}`
    );

  }

}
/** Cliente HTTP de trabajos de mano de obra asociados a una orden. */
