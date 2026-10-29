import { inject, Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

import { API_URL } from '../../../core/tokens/api.token';
import { ComprasResumen } from '../models/compras-resumen';

@Injectable({ providedIn: 'root' })
export class ComprasDashboardService {
  private readonly http = inject(HttpClient);
  private readonly apiUrl = `${inject(API_URL)}/compras`;

  getResumen(): Observable<ComprasResumen> {
    return this.http.get<ComprasResumen>(`${this.apiUrl}/resumen`);
  }
}
/** Cliente HTTP de indicadores de compras para la vista de resumen. */
