import { Component } from '@angular/core';
import { MatListModule } from '@angular/material/list';
import { RouterLink, RouterLinkActive } from '@angular/router';
import { MatIconModule } from '@angular/material/icon';
import { inject } from '@angular/core';
import { Router } from '@angular/router';
import { AuthService } from '../../../core/auth/auth.service';
import { MatDividerModule } from '@angular/material/divider';
import { API_URL } from '../../../core/tokens/api.token';

@Component({
  selector: 'app-sidebar',
  standalone: true,
  imports: [
    MatListModule,
    RouterLink,
    RouterLinkActive,
    MatIconModule
  ],
  templateUrl: './sidebar.html',
  styleUrl: './sidebar.scss'
})
export class Sidebar {

readonly authService = inject(AuthService);

private router = inject(Router);
private readonly apiUrl = inject(API_URL);

logout(): void {
  // La invalidación del token actual es local porque los JWT son stateless.
  // La invalidación global de sesiones requerirá una tabla de sesiones o una
  // versión de token en el backend.
  this.authService.logout();

  this.router.navigate(['/login']);

}

get nombreUsuario(): string {
  return this.authService.usuarioActual()?.nombre ?? 'Usuario';
}

get rolUsuario(): string {
  return this.authService.usuarioActual()?.rol ?? '';
}

get inicialesUsuario(): string {
  const usuario = this.authService.usuarioActual();
  return `${usuario?.nombre?.[0] ?? ''}${usuario?.apellidos?.[0] ?? ''}`.toUpperCase() || 'MD';
}

get avatarUrl(): string | null {
  // Las imágenes locales se devuelven como rutas relativas por el backend;
  // las remotas se mantienen intactas para no duplicar el host de la API.
  const avatar = this.authService.usuarioActual()?.avatar_url;
  return avatar ? (avatar.startsWith('http') ? avatar : `${this.apiUrl}${avatar}`) : null;
}

get usuarioId(): number | null {
  return this.authService.usuarioActual()?.id ?? null;
}

}
/** Navegación lateral, perfil contextual y cierre de sesión del usuario actual. */
