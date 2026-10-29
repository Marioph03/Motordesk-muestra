import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';

import { Observable } from 'rxjs';

import { Cita } from '../models/cita';
import { CitaCreate } from '../models/cita-create';
import { CitaUpdate } from '../models/cita-update';
import { API_URL } from '../../../core/tokens/api.token';


@Injectable({
  providedIn: 'root'
})
export class CitasService {

  private http = inject(HttpClient);

  private apiUrl =
    `${inject(API_URL)}/citas`;


  getCitas(): Observable<Cita[]> {

    return this.http.get<Cita[]>(
      this.apiUrl
    );

  }


  getCita(
    citaId: number
  ): Observable<Cita> {

    return this.http.get<Cita>(
      `${this.apiUrl}/${citaId}`
    );

  }


  getCitasPorRango(
    fechaInicio: string,
    fechaFin: string
  ): Observable<Cita[]> {

    const params = new HttpParams()
      .set(
        'fecha_inicio',
        fechaInicio
      )
      .set(
        'fecha_fin',
        fechaFin
      );

    return this.http.get<Cita[]>(
      `${this.apiUrl}/rango`,
      { params }
    );

  }


  crearCita(
    cita: CitaCreate
  ): Observable<Cita> {

    return this.http.post<Cita>(
      this.apiUrl,
      cita
    );

  }


  actualizarCita(
    citaId: number,
    cita: CitaUpdate
  ): Observable<Cita> {

    return this.http.patch<Cita>(
      `${this.apiUrl}/${citaId}`,
      cita
    );

  }


  eliminarCita(
    citaId: number
  ): Observable<void> {

    return this.http.delete<void>(
      `${this.apiUrl}/${citaId}`
    );

  }

  crearOrdenDesdeCita(citaId: number): Observable<{ id: number; numero: string }> {
    return this.http.post<{ id: number; numero: string }>(`${this.apiUrl}/${citaId}/crear-orden`, {});
  }

  crearPresupuestoDesdeCita(citaId: number): Observable<{ id: number; numero: string }> {
    return this.http.post<{ id: number; numero: string }>(`${this.apiUrl}/${citaId}/crear-presupuesto`, {});
  }

  enviarConfirmacionEmail(citaId: number): Observable<Cita> {
    return this.http.post<Cita>(`${this.apiUrl}/${citaId}/enviar-confirmacion-email`, {});
  }

  avisarReprogramacionEmail(citaId: number): Observable<Cita> {
    return this.http.post<Cita>(`${this.apiUrl}/${citaId}/avisar-reprogramacion-email`, {});
  }

  confirmarCita(citaId: number): Observable<Cita> {
    return this.http.post<Cita>(`${this.apiUrl}/${citaId}/confirmar`, {});
  }

  marcarEnTaller(citaId: number): Observable<Cita> {
    return this.http.post<Cita>(`${this.apiUrl}/${citaId}/en-taller`, {});
  }

  completarCita(citaId: number): Observable<Cita> {
    return this.http.post<Cita>(`${this.apiUrl}/${citaId}/completar`, {});
  }

  cancelarCita(citaId: number): Observable<Cita> {
    return this.http.post<Cita>(`${this.apiUrl}/${citaId}/cancelar`, {});
  }

  marcarNoPresentado(citaId: number): Observable<Cita> {
    return this.http.post<Cita>(`${this.apiUrl}/${citaId}/no-presentado`, {});
  }

}
/** Cliente HTTP de citas, disponibilidad y flujo de agenda. */
