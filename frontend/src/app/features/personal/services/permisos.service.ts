import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';

import { API_URL } from '../../../core/tokens/api.token';
import { Permiso } from '../models/permiso';
import { Rol, RolGuardar } from '../models/rol';

@Injectable({
  providedIn: 'root'
})
export class PermisosService {
  private readonly http = inject(HttpClient);
  private readonly apiUrl = `${inject(API_URL)}/permisos`;

  getPermisos() {
    return this.http.get<Permiso[]>(this.apiUrl);
  }

  getRoles() {
    return this.http.get<Rol[]>(`${this.apiUrl}/roles`);
  }

  getRol(rolId: number) {
    return this.http.get<Rol>(`${this.apiUrl}/roles/${rolId}`);
  }

  crearRol(datos: Required<RolGuardar>) {
    return this.http.post<Rol>(`${this.apiUrl}/roles`, datos);
  }

  actualizarRol(rolId: number, datos: RolGuardar) {
    return this.http.patch<Rol>(`${this.apiUrl}/roles/${rolId}`, datos);
  }
}
/** Cliente HTTP de permisos y roles; la autorización real la decide el backend. */
