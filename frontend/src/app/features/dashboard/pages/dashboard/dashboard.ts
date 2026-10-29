import { CommonModule } from '@angular/common';

import {
  ChangeDetectorRef,
  Component,
  DestroyRef,
  inject,
  OnInit
} from '@angular/core';

import {
  NavigationEnd,
  Router,
  RouterLink
} from '@angular/router';

import { filter } from 'rxjs';

import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';

import {
  takeUntilDestroyed
} from '@angular/core/rxjs-interop';

import {
  timeout
} from 'rxjs/operators';

import {
  DashboardService
} from '../../../../core/services/dashboard.service';

import {
  DashboardFacturacionMes,
  DashboardResponse
} from '../../../../core/models/dashboard';

import {
  AuthService
} from '../../../../core/auth/auth.service';


@Component({
  selector: 'app-dashboard',

  standalone: true,

  imports: [
    CommonModule,
    MatCardModule,
    MatButtonModule,
    MatIconModule,
    RouterLink
  ],

  templateUrl: './dashboard.html',
  styleUrl: './dashboard.scss'
})
export class Dashboard implements OnInit {

  // =====================================================
  // SERVICIOS
  // =====================================================

  private readonly dashboardService =
    inject(DashboardService);

  private readonly changeDetector =
    inject(ChangeDetectorRef);

  private readonly destroyRef =
    inject(DestroyRef);

  private readonly router =
    inject(Router);


  readonly authService =
    inject(AuthService);


  // =====================================================
  // ESTADO
  // =====================================================

  dashboard: DashboardResponse | null =
    null;

  cargando = true;

  errorCarga = false;

  private enDashboard = false;


  // =====================================================
  // CICLO DE VIDA
  // =====================================================

  ngOnInit(): void {

    this.enDashboard = this.esRutaDashboard(
      this.router.url
    );

    this.cargarDashboard();

    this.router.events
      .pipe(
        filter(
          (evento): evento is NavigationEnd =>
            evento instanceof NavigationEnd
        ),
        takeUntilDestroyed(this.destroyRef)
      )
      .subscribe(evento => {

        const esDashboard = this.esRutaDashboard(
          evento.urlAfterRedirects
        );

        if (esDashboard && !this.enDashboard) {
          this.cargarDashboard();
        }

        this.enDashboard = esDashboard;
      });

  }


  // =====================================================
  // CARGA DEL DASHBOARD
  // =====================================================

  cargarDashboard(): void {

    console.log(
      '[Dashboard] Iniciando carga...'
    );

    /*
     * Reiniciamos siempre el estado.
     *
     * No bloqueamos con:
     *
     * if (this.cargando) return;
     *
     * porque queremos que el botón
     * "Reintentar" pueda volver a
     * ejecutar correctamente la carga.
     */

    this.cargando = true;
    this.errorCarga = false;
    this.dashboard = null;

    /*
     * Forzamos actualización inmediata.
     *
     * Esto también nos protege si la
     * aplicación está utilizando una
     * configuración zoneless.
     */

    this.actualizarVista();


    this.dashboardService
      .getDashboard()
      .pipe(

        /*
         * Si por cualquier motivo la
         * petición queda colgada, no
         * tendremos el loading infinito.
         */

        timeout(30000),

        /*
         * Angular elimina automáticamente
         * la suscripción cuando destruye
         * el componente.
         */

        takeUntilDestroyed(
          this.destroyRef
        )

      )
      .subscribe({

        // ===============================================
        // RESPUESTA CORRECTA
        // ===============================================

        next: (
          data: DashboardResponse
        ) => {

          console.log(
            '[Dashboard] Respuesta recibida:',
            data
          );


          /*
           * Primero guardamos los datos.
           */

          this.dashboard =
            data;


          /*
           * Después quitamos loading.
           *
           * Lo hacemos AQUÍ y no únicamente
           * mediante finalize().
           */

          this.cargando =
            false;

          this.errorCarga =
            false;


          console.log(
            '[Dashboard] Estado después de cargar:',
            {
              cargando:
                this.cargando,

              errorCarga:
                this.errorCarga,

              dashboard:
                this.dashboard
            }
          );


          /*
           * Forzamos la actualización
           * visual del template.
           */

          this.actualizarVista();

        },


        // ===============================================
        // ERROR
        // ===============================================

        error: err => {

          console.error(
            '[Dashboard] Error cargando dashboard:',
            err
          );


          this.dashboard =
            null;

          this.cargando =
            false;

          this.errorCarga =
            true;


          this.actualizarVista();

        },


        // ===============================================
        // COMPLETADO
        // ===============================================

        complete: () => {

          console.log(
            '[Dashboard] Petición completada.'
          );

          /*
           * Por seguridad:
           *
           * HttpClient completa después de
           * emitir la respuesta.
           *
           * Si por alguna razón cargando
           * siguiera activo, lo apagamos.
           */

          if (this.cargando) {

            this.cargando =
              false;

            this.actualizarVista();

          }

        }

      });

  }


  // =====================================================
  // USUARIO
  // =====================================================

  get nombreUsuario(): string {

    const usuario =
      this.authService
        .usuarioActual();


    return (
      usuario?.nombre
      ??
      'Usuario'
    );

  }


  // =====================================================
  // ÓRDENES
  // =====================================================

  porcentajeCerradas(): number {

    const abiertas =
      Number(
        this.dashboard
          ?.ordenes_abiertas
        ?? 0
      );


    const cerradas =
      Number(
        this.dashboard
          ?.ordenes_cerradas
        ?? 0
      );


    const total =
      abiertas
      +
      cerradas;


    if (total <= 0) {

      return 0;

    }


    const porcentaje =
      (
        cerradas
        /
        total
      )
      *
      100;


    return Math.round(
      porcentaje
    );

  }


  // =====================================================
  // GRÁFICA DE FACTURACIÓN
  // =====================================================

  readonly guiasGrafica = [0, 1, 2, 3];

  get facturacionMensual(): DashboardFacturacionMes[] {

    return this.dashboard?.facturacion_ultimos_meses ?? [];

  }

  get maximoFacturacionGrafica(): number {

    return Math.max(
      1,
      ...this.facturacionMensual.map(
        mes => Number(mes.total) || 0
      )
    );

  }

  posicionGuia(indice: number): number {

    return 24 + (indice * 58);

  }

  valorGuia(indice: number): number {

    return this.maximoFacturacionGrafica * (3 - indice) / 3;

  }

  posicionX(indice: number): number {

    const cantidad = this.facturacionMensual.length;

    if (cantidad <= 1) {
      return 336;
    }

    return 62 + (indice * (548 / (cantidad - 1)));

  }

  posicionY(total: number): number {

    const proporcion = Math.max(
      0,
      Math.min(1, (Number(total) || 0) / this.maximoFacturacionGrafica)
    );

    return 198 - (proporcion * 174);

  }

  get puntosGrafica(): string {

    return this.facturacionMensual
      .map(
        (mes, indice) =>
          `${this.posicionX(indice)},${this.posicionY(mes.total)}`
      )
      .join(' ');

  }

  get areaGrafica(): string {

    const puntos = this.facturacionMensual;

    if (!puntos.length) {
      return '';
    }

    const linea = puntos.map(
      (mes, indice) =>
        `L ${this.posicionX(indice)} ${this.posicionY(mes.total)}`
    ).join(' ');

    return `M ${this.posicionX(0)} 198 ${linea} L ${this.posicionX(puntos.length - 1)} 198 Z`;

  }


  // =====================================================
  // CLASE CSS PARA ESTADOS
  // =====================================================

  estadoClase(
    estado?: string | null
  ): string {

    if (!estado) {

      return 'estado-desconocido';

    }


    const estadoNormalizado =
      estado
        .trim()
        .toLowerCase()
        .normalize('NFD')
        .replace(
          /[\u0300-\u036f]/g,
          ''
        )
        .replace(
          /[^a-z0-9]+/g,
          '-'
        )
        .replace(
          /^-+|-+$/g,
          ''
        );


    return (
      `estado-${estadoNormalizado}`
    );

  }


  // =====================================================
  // DETECCIÓN DE CAMBIOS
  // =====================================================

  private actualizarVista(): void {

    /*
     * markForCheck() prepara el componente
     * para ser actualizado.
     */

    this.changeDetector
      .markForCheck();


    /*
     * detectChanges() lo actualiza
     * inmediatamente.
     *
     * Esto es especialmente útil si
     * MotorDesk está funcionando con
     * detección de cambios zoneless.
     */

    this.changeDetector
      .detectChanges();

  }

  private esRutaDashboard(ruta: string): boolean {

    return ruta === '/dashboard'
      || ruta.startsWith('/dashboard?');

  }

}
/** Dashboard operativo: presenta indicadores ya calculados por el backend. */
