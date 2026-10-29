/** Cliente HTTP del resumen operativo mostrado al abrir MotorDesk. */
import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';

import { Observable } from 'rxjs';

import { API_URL } from '../tokens/api.token';
import { DashboardResponse } from '../models/dashboard';

@Injectable({
  providedIn: 'root'
})
export class DashboardService {

  private http = inject(HttpClient);

  private apiUrl = inject(API_URL);

  getDashboard(): Observable<DashboardResponse> {
    // La barra final evita depender de la redirección 307 de FastAPI.

    return this.http.get<DashboardResponse>(
      `${this.apiUrl}/dashboard/`
    );

  }

}
