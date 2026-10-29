/** Acceso a informes agregados y a su exportación PDF para un rango temporal. */
import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';

import { API_URL } from '../../../core/tokens/api.token';
import { InformeGeneral } from '../models/informe-general';

export interface FiltrosInforme {
  cliente_id?: number | null;
  proveedor_id?: number | null;
  gasto_id?: number | null;
}

@Injectable({ providedIn: 'root' })
export class InformesService {
  private readonly http = inject(HttpClient);
  private readonly apiUrl = `${inject(API_URL)}/informes`;

  getResumenGeneral(fechaInicio: string, fechaFin: string, filtros: FiltrosInforme = {}) {
    let params = new HttpParams()
      .set('fecha_inicio', fechaInicio)
      .set('fecha_fin', fechaFin);
    params = this.aplicarFiltros(params, filtros);

    return this.http.get<InformeGeneral>(
      `${this.apiUrl}/resumen-general`,
      { params }
    );
  }

  getPdf(tipo: 'general' | 'facturacion' | 'clientes' | 'compras-gastos', fechaInicio: string, fechaFin: string, filtros: FiltrosInforme = {}) {
    // El blob se abre o descarga desde el componente sin intentar parsearlo como JSON.
    let params = new HttpParams()
      .set('fecha_inicio', fechaInicio)
      .set('fecha_fin', fechaFin);
    params = this.aplicarFiltros(params, filtros);

    const ruta = tipo === 'general' ? 'resumen-general/pdf' : `${tipo}/pdf`;
    return this.http.get(`${this.apiUrl}/${ruta}`, {
      params,
      responseType: 'blob'
    });
  }

  getExcel(tipo: 'facturacion' | 'clientes' | 'compras-gastos', fechaInicio: string, fechaFin: string, filtros: FiltrosInforme = {}) {
    let params = new HttpParams()
      .set('fecha_inicio', fechaInicio)
      .set('fecha_fin', fechaFin);
    params = this.aplicarFiltros(params, filtros);

    return this.http.get(`${this.apiUrl}/${tipo}/excel`, {
      params,
      responseType: 'blob'
    });
  }

  private aplicarFiltros(params: HttpParams, filtros: FiltrosInforme): HttpParams {
    for (const [clave, valor] of Object.entries(filtros)) {
      if (valor) params = params.set(clave, valor);
    }
    return params;
  }
}
