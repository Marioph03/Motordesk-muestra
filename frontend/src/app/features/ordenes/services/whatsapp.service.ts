import { HttpClient } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { Observable } from 'rxjs';

import { API_URL } from '../../../core/tokens/api.token';


export interface WhatsAppConnectResponse {
  message: string;
}


export interface WhatsAppEstadoResponse {
  conectado: boolean;
  numero_whatsapp?: string | null;
  embedded_signup_disponible: boolean;
  meta_config_id?: string | null;
  meta_app_id?: string | null;
  meta_signup_bridge_url?: string | null;
  configuracion_meta_pendiente?: string[];
}


export interface WhatsAppPlantilla {
  id: number;
  tipo: string;
  nombre_meta: string;
  idioma: string;
  estado: string;
}


export interface WhatsAppPlantillasResponse {
  plantillas: WhatsAppPlantilla[];
}


export interface WhatsAppEnviarPruebaResponse {
  message: string;
  resultado: unknown;
}


@Injectable({
  providedIn: 'root'
})
export class WhatsAppService {

  // =========================================================
  // DEPENDENCIAS
  // =========================================================

  private http =
    inject(HttpClient);

  private apiUrl =
    inject(API_URL);


  // =========================================================
  // CONECTAR WHATSAPP BUSINESS
  // =========================================================

  conectar(
    code: string,
    wabaId: string | null = null,
    phoneNumberId: string | null = null,
    redirectUri: string | null = null,
  ): Observable<WhatsAppConnectResponse> {

    return this.http.post<WhatsAppConnectResponse>(
      `${this.apiUrl}/whatsapp/conectar`,
      {
        code,
        waba_id: wabaId,
        phone_number_id: phoneNumberId,
        redirect_uri: redirectUri,
      }
    );

  }


  // =========================================================
  // OBTENER ESTADO DE WHATSAPP
  // =========================================================

  obtenerEstado(): Observable<WhatsAppEstadoResponse> {

    return this.http.get<WhatsAppEstadoResponse>(
      `${this.apiUrl}/whatsapp/estado`
    );

  }

  desconectar(): Observable<void> {
    return this.http.delete<void>(
      `${this.apiUrl}/configuracion/whatsapp`
    );
  }


  // =========================================================
  // PLANTILLAS DE WHATSAPP
  // =========================================================

  obtenerPlantillas(): Observable<WhatsAppPlantillasResponse> {

    return this.http.get<WhatsAppPlantillasResponse>(
      `${this.apiUrl}/configuracion/whatsapp/plantillas`
    );

  }


  sincronizarPlantillas(): Observable<WhatsAppPlantillasResponse> {

    return this.http.post<WhatsAppPlantillasResponse>(
      `${this.apiUrl}/configuracion/whatsapp/plantillas/sincronizar`,
      {}
    );

  }


  // =========================================================
  // ENVIAR MENSAJE DE PRUEBA
  // =========================================================

  enviarPrueba(
    telefono: string,
    mensaje: string
  ): Observable<WhatsAppEnviarPruebaResponse> {

    return this.http.post<WhatsAppEnviarPruebaResponse>(
      `${this.apiUrl}/whatsapp/enviar-prueba`,
      {
        telefono,
        mensaje
      }
    );

  }

  debug(): Observable<any> {

  return this.http.get<any>(
    `${this.apiUrl}/whatsapp/debug`
  );

  }

  crearPlantilla(tipo: string) {
  return this.http.post<{
    tipo: string;
    estado: string;
    meta_id: string | null;
    mensaje: string;
  }>(
    `${this.apiUrl}/configuracion/whatsapp/plantillas/${tipo}/crear`,
    {}
  );
  }

}
/** Cliente de comunicaciones WhatsApp que delega envío y permisos al backend. */
