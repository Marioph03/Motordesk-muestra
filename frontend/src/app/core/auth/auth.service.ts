import { Injectable, inject, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';

import { Observable, tap } from 'rxjs';

import { API_URL } from '../tokens/api.token';

import { LoginRequest } from '../models/login';
import { TokenResponse } from '../models/token';
import { UsuarioActual } from '../models/usuario-actual';

@Injectable({
  providedIn: 'root'
})
export class AuthService {

    private readonly TOKEN_KEY = 'access_token';
    private readonly usuarioSignal = signal<UsuarioActual | null>(null);
    private expirationTimer?: ReturnType<typeof setTimeout>;

    readonly usuarioActual = this.usuarioSignal.asReadonly();

    private http = inject(HttpClient);
    private router = inject(Router);
    private apiUrl = inject(API_URL);

    constructor() {
      this.programarCaducidadSesion();
    }

    login(login: LoginRequest) {

    return this.http.post<TokenResponse>(
    `${this.apiUrl}/auth/login`,
    login
  );

}

    register(datos: {
      nombre: string;
      apellidos: string;
      email: string;
      password: string;
    }) {
      return this.http.post<TokenResponse>(
        `${this.apiUrl}/auth/register`,
        datos
      );
    }

    cargarUsuarioActual(): Observable<UsuarioActual> {
      return this.http.get<UsuarioActual>(
        `${this.apiUrl}/auth/me`
      ).pipe(
        tap(usuario => this.usuarioSignal.set(usuario))
      );
    }

    subirAvatar(archivo: File): Observable<UsuarioActual> {
      const datos = new FormData();
      datos.append('archivo', archivo);

      return this.http.post<UsuarioActual>(
        `${this.apiUrl}/auth/me/avatar`,
        datos
      ).pipe(
        tap(usuario => this.usuarioSignal.set(usuario))
      );
    }

    establecerUsuarioActual(usuario: UsuarioActual): void {
      this.usuarioSignal.set(usuario);
    }

    tienePermiso(codigo: string): boolean {
      const usuario = this.usuarioActual();

      if (!usuario) {
        return false;
      }

      const rol = usuario.rol?.toUpperCase();

      if (rol === 'ADMIN' || rol === 'ADMINISTRADOR') {
        return true;
      }

      return usuario.permisos?.includes(codigo) ?? false;
    }

    tieneAlgunPermiso(permisos: string[]): boolean {
      return permisos.some(
        permiso => this.tienePermiso(permiso)
      );
    }

    saveToken(token: string): void {
        localStorage.setItem(
            this.TOKEN_KEY,
            token
        );
        this.programarCaducidadSesion();
    }

    getToken(): string | null {
        return localStorage.getItem(
            this.TOKEN_KEY
        );
    }

    logout(): void {
        this.cancelarCaducidadProgramada();
        localStorage.removeItem(
            this.TOKEN_KEY
        );
        this.usuarioSignal.set(null);
    }

    isLogged(): boolean {
        const token = this.getToken();

        if (!token) {
          return false;
        }

        if (this.tokenHaCaducado(token)) {
          this.logout();
          return false;
        }

        return true;
    }

    finalizarSesionCaducada(): void {
      this.logout();
      void this.router.navigate(
        ['/login'],
        {
          queryParams: {
            sesion: 'caducada'
          }
        }
      );
    }

    private programarCaducidadSesion(): void {
      this.cancelarCaducidadProgramada();

      const token = this.getToken();
      const expiracion = token
        ? this.obtenerExpiracionToken(token)
        : null;

      if (!expiracion) {
        return;
      }

      const espera = expiracion - Date.now();

      if (espera <= 0) {
        this.finalizarSesionCaducada();
        return;
      }

      // Un JWT de MotorDesk dura 6 h; aun así limitamos el temporizador al
      // máximo seguro de JavaScript para evitar desbordamientos futuros.
      this.expirationTimer = setTimeout(
        () => this.finalizarSesionCaducada(),
        Math.min(espera, 2_147_483_647)
      );
    }

    private cancelarCaducidadProgramada(): void {
      if (this.expirationTimer) {
        clearTimeout(this.expirationTimer);
        this.expirationTimer = undefined;
      }
    }

    private tokenHaCaducado(token: string): boolean {
      const expiracion = this.obtenerExpiracionToken(token);
      return expiracion !== null && expiracion <= Date.now();
    }

    private obtenerExpiracionToken(token: string): number | null {
      try {
        const payload = token.split('.')[1];

        if (!payload) {
          return null;
        }

        const base64 = payload
          .replace(/-/g, '+')
          .replace(/_/g, '/')
          .padEnd(
            Math.ceil(payload.length / 4) * 4,
            '='
          );

        const datos = JSON.parse(atob(base64)) as { exp?: number };

        return typeof datos.exp === 'number'
          ? datos.exp * 1000
          : null;
      } catch {
        // No usamos el contenido del JWT como mecanismo de seguridad: el
        // backend siempre valida firma y caducidad. Esto solo mejora la UX.
        return null;
      }
    }

}
/** Gestiona sesión JWT, perfil actual y redirección segura por expiración. */
