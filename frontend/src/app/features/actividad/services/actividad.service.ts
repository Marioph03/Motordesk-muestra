import { Injectable, inject } from '@angular/core';

import { HttpClient, HttpParams } from '@angular/common/http';

import { Observable } from 'rxjs';

import { API_URL } from '../../../core/tokens/api.token';

import { Actividad } from '../models/actividad';
import { ActividadPage } from '../models/actividad-page';
import { ActividadFilter } from '../models/actividad-filter';

@Injectable({
  providedIn: 'root'
})
export class ActividadService {

  private http = inject(HttpClient);

  private apiUrl = inject(API_URL);

  getActividades(

    page: number = 1,

    size: number = 10,

    filtro: ActividadFilter = {}

  ): Observable<ActividadPage> {

    let params = new HttpParams()
      .set('page', Math.max(1, page))
      .set('size', size);

    if (filtro.usuario_id) {

      params = params.set(
        'usuario_id',
        filtro.usuario_id
      );

    }

    if (filtro.modulo) {

      params = params.set(
        'modulo',
        filtro.modulo
      );

    }

    if (filtro.accion) {

      params = params.set(
        'accion',
        filtro.accion
      );

    }

    if (filtro.fecha_desde) {

      params = params.set(
        'fecha_desde',
        filtro.fecha_desde
      );

    }

    if (filtro.fecha_hasta) {

      params = params.set(
        'fecha_hasta',
        filtro.fecha_hasta
      );

    }

    return this.http.get<ActividadPage>(
      `${this.apiUrl}/actividad/`,
      {
        params
      }
    );

  }

  getActividad(
    id: number
  ): Observable<Actividad> {

    return this.http.get<Actividad>(
      `${this.apiUrl}/actividad/${id}`
    );

  }

}
/** Cliente HTTP de la auditoría de actividad del sistema. */
