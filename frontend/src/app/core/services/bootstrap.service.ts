import { inject, Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

import { API_URL } from '../tokens/api.token';


export interface BootstrapStatus {
  requiere_configuracion: boolean;
}


export interface BootstrapInicialRequest {
  // Empresa
  nombre_empresa: string;
  nombre_comercial: string;
  nif: string;
  direccion: string;
  codigo_postal: string;
  ciudad: string;
  provincia: string;
  telefono: string;
  email_empresa: string;

  // Administrador
  nombre_admin: string;
  apellidos_admin: string;
  email_admin: string;
  password_admin: string;

  // Facturacion inicial
  iva_defecto: number;
  regimen_fiscal: string | null;
  serie_facturas: string;
  serie_pruebas: string;
}


export interface BootstrapInicialResponse {
  configurado: boolean;
  empresa_id: number;
  usuario_id: number;
  mensaje: string;
}


@Injectable({
  providedIn: 'root'
})
export class BootstrapService {

  private readonly http = inject(HttpClient);
  private readonly apiUrl = inject(API_URL);


  obtenerEstado(): Observable<BootstrapStatus> {
    return this.http.get<BootstrapStatus>(
      `${this.apiUrl}/bootstrap/status`
    );
  }


  inicializar(
    datos: BootstrapInicialRequest
  ): Observable<BootstrapInicialResponse> {

    return this.http.post<BootstrapInicialResponse>(
      `${this.apiUrl}/bootstrap/inicializar`,
      datos
    );
  }

}
