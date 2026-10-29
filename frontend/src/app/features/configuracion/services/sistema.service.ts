import { inject, Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

import { API_URL } from '../../../core/tokens/api.token';
import { BackupInfo, EstadoSistema } from '../models/sistema';

@Injectable({ providedIn: 'root' })
export class SistemaService {
  private readonly http = inject(HttpClient);
  private readonly apiUrl = `${inject(API_URL)}/configuracion/sistema`;

  getEstado(): Observable<EstadoSistema> { return this.http.get<EstadoSistema>(`${this.apiUrl}/estado`); }
  getUltimoBackup(): Observable<BackupInfo> { return this.http.get<BackupInfo>(`${this.apiUrl}/backup`); }
  crearBackup(): Observable<{ message: string; archivo: string }> { return this.http.post<{ message: string; archivo: string }>(`${this.apiUrl}/backup`, {}); }
  descargarBackup(): Observable<Blob> { return this.http.get(`${this.apiUrl}/backup/descargar`, { responseType: 'blob' }); }
  restablecerDatos(): Observable<{ message: string; backup: string }> { return this.http.post<{ message: string; backup: string }>(`${this.apiUrl}/restablecer-datos`, { confirmacion: 'RESTABLECER' }); }
}
/** Cliente HTTP de mantenimiento y descarga de copias de seguridad autorizadas. */
