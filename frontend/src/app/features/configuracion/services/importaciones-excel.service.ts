import { inject, Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { API_URL } from '../../../core/tokens/api.token';
import { AnalisisExcel, CamposImportacionResponse, MapeoCampo, PreviewImportacion, ResultadoImportacion } from '../models/importacion-excel';

@Injectable({ providedIn: 'root' })
export class ImportacionesExcelService {
  private readonly http = inject(HttpClient);
  private readonly apiUrl = `${inject(API_URL)}/configuracion/importaciones`;

  analizar(archivo: File): Observable<AnalisisExcel> {
    const datos = new FormData();
    datos.append('archivo', archivo);
    return this.http.post<AnalisisExcel>(`${this.apiUrl}/analizar`, datos);
  }

  analizarHoja(archivoTemporal: string, hoja: string): Observable<AnalisisExcel> {
    return this.http.get<AnalisisExcel>(`${this.apiUrl}/analizar/${encodeURIComponent(archivoTemporal)}`, { params: { hoja } });
  }

  getCampos(tipo: string): Observable<CamposImportacionResponse> {
    return this.http.get<CamposImportacionResponse>(`${this.apiUrl}/campos/${tipo}`);
  }

  preview(tipo: string, archivoTemporal: string, hoja: string, mapeo: MapeoCampo[]): Observable<PreviewImportacion> {
    return this.http.post<PreviewImportacion>(`${this.apiUrl}/${tipo}/preview`, { archivo_temporal: archivoTemporal, hoja, mapeo });
  }

  importar(tipo: string, archivoTemporal: string, hoja: string, mapeo: MapeoCampo[]): Observable<ResultadoImportacion> {
    return this.http.post<ResultadoImportacion>(`${this.apiUrl}/${tipo}/confirmar`, {
      archivo_temporal: archivoTemporal,
      hoja,
      mapeo,
      ignorar_duplicados: true,
    });
  }

  exportar(tipo: string): Observable<Blob> {
    return this.http.get(`${this.apiUrl}/exportar/${tipo}`, { responseType: 'blob' });
  }
}
/** Cliente HTTP del análisis, mapeo y confirmación de importaciones Excel. */
