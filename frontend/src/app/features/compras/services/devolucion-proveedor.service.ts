import { inject, Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

import { API_URL } from '../../../core/tokens/api.token';
import { CrearDevolucionProveedor, DevolucionProveedor } from '../models/devolucion-proveedor';

@Injectable({ providedIn: 'root' })
export class DevolucionProveedorService {
  private readonly http = inject(HttpClient);
  private readonly apiUrl = `${inject(API_URL)}/devoluciones-proveedor`;

  listar(): Observable<DevolucionProveedor[]> { return this.http.get<DevolucionProveedor[]>(this.apiUrl); }
  getById(id: number): Observable<DevolucionProveedor> { return this.http.get<DevolucionProveedor>(`${this.apiUrl}/${id}`); }
  crear(datos: CrearDevolucionProveedor): Observable<DevolucionProveedor> { return this.http.post<DevolucionProveedor>(this.apiUrl, datos); }
  confirmar(id: number): Observable<DevolucionProveedor> { return this.http.post<DevolucionProveedor>(`${this.apiUrl}/${id}/confirmar`, {}); }
  resolver(id: number, resolucion: DevolucionProveedor['resolucion']): Observable<DevolucionProveedor> { return this.http.post<DevolucionProveedor>(`${this.apiUrl}/${id}/resolver`, { resolucion }); }
}
/** Cliente HTTP de devoluciones a proveedor y sus confirmaciones de salida. */
