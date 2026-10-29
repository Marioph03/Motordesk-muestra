import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { API_URL } from '../../../core/tokens/api.token';

import { Proveedor } from '../models/proveedor';
import { ProveedorCreate } from '../models/proveedor-create';
import { ProveedorUpdate } from '../models/proveedor-update';

@Injectable({
  providedIn: 'root'
})
export class ProveedoresService {

  private http = inject(HttpClient);

  private apiUrl = inject(API_URL);

  getProveedores(): Observable<Proveedor[]> {

    return this.http.get<Proveedor[]>(
      `${this.apiUrl}/proveedores/`
    );

  }

  getProveedor(
    id: number
  ): Observable<Proveedor> {

    return this.http.get<Proveedor>(
      `${this.apiUrl}/proveedores/${id}`
    );

  }

  createProveedor(
    proveedor: ProveedorCreate
  ): Observable<Proveedor> {

    return this.http.post<Proveedor>(
      `${this.apiUrl}/proveedores/`,
      proveedor
    );

  }

  updateProveedor(
    id: number,
    proveedor: ProveedorUpdate
  ): Observable<Proveedor> {

    return this.http.patch<Proveedor>(
      `${this.apiUrl}/proveedores/${id}`,
      proveedor
    );

  }

  deleteProveedor(
    id: number
  ) {

    return this.http.delete(
      `${this.apiUrl}/proveedores/${id}`
    );

  }

}
/** Cliente HTTP de proveedores usado por Compras y formularios de catálogo. */
