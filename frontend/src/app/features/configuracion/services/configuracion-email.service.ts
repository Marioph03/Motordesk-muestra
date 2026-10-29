import { inject, Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { API_URL } from '../../../core/tokens/api.token';

export interface ConfiguracionEmail {
  configurado: boolean;
  activo: boolean;
  proveedor: 'gmail' | 'outlook' | 'personalizado';
  host: string;
  puerto: number;
  seguridad: 'starttls' | 'ssl';
  usuario: string | null;
  remitente: string | null;
  metodo_autenticacion: 'password' | 'google_oauth' | 'microsoft_oauth';
}

export interface ConfiguracionEmailGuardar {
  proveedor: 'gmail' | 'outlook' | 'personalizado';
  host: string;
  puerto: number;
  seguridad: 'starttls' | 'ssl';
  usuario: string;
  remitente?: string;
  password?: string;
  activo: boolean;
}

@Injectable({ providedIn: 'root' })
export class ConfiguracionEmailService {
  private readonly http = inject(HttpClient);
  private readonly url = `${inject(API_URL)}/configuracion/email`;

  obtener() { return this.http.get<ConfiguracionEmail>(this.url); }
  guardar(datos: ConfiguracionEmailGuardar) { return this.http.put<ConfiguracionEmail>(this.url, datos); }
  probar(destinatario: string) { return this.http.post<{ message: string }>(`${this.url}/probar`, { destinatario }); }
  iniciarGoogle() { return this.http.post<{ url: string; estado: string }>(`${this.url}/google/iniciar`, {}); }
  estadoGoogle(estado: string) { return this.http.get<{ estado: string; detalle?: string | null }>(`${this.url}/google/estado/${estado}`); }
  iniciarMicrosoft() { return this.http.post<{ url: string; estado: string }>(`${this.url}/microsoft/iniciar`, {}); }
  estadoMicrosoft(estado: string) { return this.http.get<{ estado: string }>(`${this.url}/microsoft/estado/${estado}`); }
}
