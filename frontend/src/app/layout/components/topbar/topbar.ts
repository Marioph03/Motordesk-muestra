import {
  Component,
  ChangeDetectorRef,
  DestroyRef,
  EventEmitter,
  OnInit,
  Output,
  inject
} from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatMenuModule } from '@angular/material/menu';
import { AuthService } from '../../../core/auth/auth.service';
import { NavigationEnd, Router, RouterLink } from '@angular/router';
import { filter } from 'rxjs';
import { DashboardService } from '../../../core/services/dashboard.service';
import { DashboardResponse } from '../../../core/models/dashboard';
import { API_URL } from '../../../core/tokens/api.token';
import { NotificationService } from '../../../shared/services/notification';

@Component({
  selector: 'app-topbar',
  standalone: true,
  imports: [
    MatButtonModule,
    MatIconModule,
    MatMenuModule,
    RouterLink
  ],
  templateUrl: './topbar.html',
  styleUrl: './topbar.scss'
})
export class Topbar implements OnInit {

  @Output() menuToggle = new EventEmitter<void>();

  readonly authService = inject(AuthService);
  private router = inject(Router);
  private readonly destroyRef = inject(DestroyRef);
  private readonly dashboardService = inject(DashboardService);
  private readonly changeDetector = inject(ChangeDetectorRef);
  private readonly apiUrl = inject(API_URL);
  private readonly notification = inject(NotificationService);

  tituloPagina = 'Dashboard';
  alertas: DashboardResponse | null = null;
  cargandoAlertas = false;

  ngOnInit(): void {
    // Centraliza el título según la ruta activa; cada pantalla no necesita
    // duplicar esta misma lógica.
    this.actualizarTitulo(this.router.url);
    this.router.events.pipe(
      filter((evento): evento is NavigationEnd => evento instanceof NavigationEnd),
      takeUntilDestroyed(this.destroyRef)
    ).subscribe(evento => this.actualizarTitulo(evento.urlAfterRedirects));
  }

  logout(): void {

    this.authService.logout();

    this.router.navigate(['/login']);

  }

  toggleMenu(): void {
    this.menuToggle.emit();
  }

  cargarAlertas(): void {
    // Evita consultas simultáneas al abrir varias veces el menú de alertas.
    if (this.cargandoAlertas) {
      return;
    }

    this.cargandoAlertas = true;

    this.dashboardService
      .getDashboard()
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: resumen => {
          this.alertas = resumen;
          this.cargandoAlertas = false;
          this.actualizarVista();
        },
        error: () => {
          this.cargandoAlertas = false;
          this.actualizarVista();
        }
      });
  }

  get totalAlertas(): number {
    if (!this.alertas) {
      return 0;
    }

    return (
      (this.alertas.stock_bajo ?? 0)
      + (this.alertas.ordenes_abiertas ?? 0)
      + (this.alertas.citas_hoy ?? 0)
      + (this.alertas.cobros_pendientes ?? 0)
    );
  }

  get nombreUsuario(): string {
    return this.authService.usuarioActual()?.nombre ?? 'Usuario';
  }

  get inicialesUsuario(): string {
    const usuario = this.authService.usuarioActual();
    return `${usuario?.nombre?.[0] ?? ''}${usuario?.apellidos?.[0] ?? ''}`.toUpperCase() || 'MD';
  }

  get usuarioId(): number | null {
    return this.authService.usuarioActual()?.id ?? null;
  }

  get avatarUrl(): string | null {
    const avatar = this.authService.usuarioActual()?.avatar_url;
    return avatar ? (avatar.startsWith('http') ? avatar : `${this.apiUrl}${avatar}`) : null;
  }

  seleccionarAvatar(evento: Event): void {
    const input = evento.target as HTMLInputElement;
    const archivo = input.files?.[0];
    input.value = '';

    if (!archivo) {
      return;
    }

    // El backend repite esta validación: la del navegador solo informa antes.
    if (!['image/jpeg', 'image/png', 'image/webp'].includes(archivo.type)) {
      this.notification.error('Selecciona una imagen JPG, PNG o WEBP.');
      return;
    }
    if (archivo.size > 5 * 1024 * 1024) {
      this.notification.error('La imagen no puede superar 5 MB.');
      return;
    }

    this.authService.subirAvatar(archivo).subscribe({
      next: () => {
        this.notification.success('Foto de perfil actualizada correctamente.');
        this.actualizarVista();
      },
      error: error => this.notification.showHttpError(error)
    });
  }

  private actualizarVista(): void {
    // Algunas respuestas HTTP se producen fuera del ciclo de Material; se
    // marca el componente para que avatar y alertas se actualicen al instante.
    this.changeDetector.markForCheck();
  }

  private actualizarTitulo(url: string): void {
    const ruta = url.split('?')[0];
    const titulos: Array<[string, string]> = [
      ['/dashboard', 'Dashboard'],
      ['/ordenes-internas', 'Órdenes internas'],
      ['/clientes', 'Clientes'],
      ['/vehiculos', 'Vehículos'],
      ['/ordenes', 'Órdenes'],
      ['/facturas', 'Facturación'],
      ['/stock', 'Almacén'],
      ['/compras', 'Compras'],
      ['/proveedores', 'Proveedores'],
      ['/agenda', 'Agenda'],
      ['/informes', 'Informes'],
      ['/personal', 'Personal'],
      ['/actividad', 'Auditoría'],
      ['/configuracion', 'Configuración']
    ];
    this.tituloPagina = titulos.find(([prefijo]) => ruta.startsWith(prefijo))?.[1] ?? 'MotorDesk';
    // La barra superior no se destruye al navegar; forzamos su refresco para
    // que nunca conserve el título de la pantalla anterior.
    this.changeDetector.markForCheck();
    this.changeDetector.detectChanges();
  }
}
/** Barra superior: título contextual, acciones rápidas, alertas y perfil. */
