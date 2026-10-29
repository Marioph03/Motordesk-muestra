import { Component, inject, OnInit } from '@angular/core';
import { NavigationEnd, Router, RouterOutlet } from '@angular/router';
import { filter } from 'rxjs';

import { AuthService } from '../../../core/auth/auth.service';

import { Sidebar } from '../../components/sidebar/sidebar';
import { Topbar } from '../../components/topbar/topbar';
import { MotorAIAssistant } from '../../../shared/components/motor-ai-assistant/motor-ai-assistant';

@Component({
  selector: 'app-main-layout',
  standalone: true,
  imports: [
    RouterOutlet,
    Sidebar,
    Topbar,
    MotorAIAssistant
  ],
  templateUrl: './main-layout.html',
  styleUrl: './main-layout.scss'
})
export class MainLayout implements OnInit {

  private readonly authService = inject(AuthService);
  private readonly router = inject(Router);
  sidebarColapsada = false;
  sidebarMovilAbierta = false;

  ngOnInit(): void {
    // Carga el perfil una vez al entrar en la zona protegida. El interceptor
    // gestionará un 401 caducado; otros errores no deben bloquear el layout.
    this.authService.cargarUsuarioActual().subscribe({
      error: () => this.authService.logout()
    });

    this.router.events.pipe(
      filter((evento): evento is NavigationEnd => evento instanceof NavigationEnd)
    ).subscribe(() => this.cerrarSidebarMovil());
  }

  alternarSidebar(): void {
    // En móvil se superpone el menú; en escritorio se conserva el espacio y se
    // alterna el estado colapsado. Son comportamientos distintos a propósito.
    if (window.matchMedia('(max-width: 700px)').matches) {
      this.sidebarMovilAbierta = !this.sidebarMovilAbierta;
      return;
    }

    this.sidebarColapsada = !this.sidebarColapsada;
  }

  cerrarSidebarMovil(): void {
    this.sidebarMovilAbierta = false;
  }

}
/** Carcasa autenticada que coordina navegación responsive, contenido e IA global. */
