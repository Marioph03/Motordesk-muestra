import { Cliente } from './../models/cliente';
import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';

import { Observable } from 'rxjs';

import { API_URL } from '../../../core/tokens/api.token';
import { ClientePage } from '../models/cliente-page';
import { ClienteCreate } from '../models/cliente-create';

@Injectable({
  providedIn: 'root'
})
export class ClientesService {

  private http = inject(HttpClient);

  private apiUrl = inject(API_URL);

  getClientes(
  page: number = 1,
  size: number = 10,
  q: string = ''
  ): Observable<ClientePage> {

  let params = new HttpParams()
    .set('page', Math.max(1, page))
    .set('size', size);

    if (q.trim()) {
    params = params.set('q', q.trim());
    }

    return this.http.get<ClientePage>(
      `${this.apiUrl}/clientes/`,
      {
        params
      }
    );

  }

  createCliente(
  cliente: ClienteCreate
  ) {

    return this.http.post(
      `${this.apiUrl}/clientes/`,
      cliente
    );
  }

  getCliente(id: number) {

    return this.http.get<Cliente>(
      `${this.apiUrl}/clientes/${id}`
    );
  }

  updateCliente(
    id: number,
    cliente: ClienteCreate
    ) {
    return this.http.put(
      `${this.apiUrl}/clientes/${id}`,
      cliente
    );
  }

  deleteCliente(id: number) {

  return this.http.delete(
    `${this.apiUrl}/clientes/${id}`
  );

  }

  getClientesSelect() {
  return this.http.get<Cliente[]>(
    `${this.apiUrl}/clientes/select`
  );

  }

}
/** Cliente HTTP del módulo Clientes; el backend conserva la validación real. */
