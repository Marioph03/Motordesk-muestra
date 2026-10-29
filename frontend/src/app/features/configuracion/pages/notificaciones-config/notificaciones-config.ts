import { ChangeDetectorRef, Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, ReactiveFormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSlideToggleModule } from '@angular/material/slide-toggle';

import { ConfiguracionNotificaciones } from '../../models/configuracion-notificaciones';
import { ConfiguracionNotificacionesService } from '../../services/configuracion-notificaciones.service';
import { NotificationService } from '../../../../shared/services/notification';

@Component({
  selector: 'app-notificaciones-config',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    MatButtonModule,
    MatCardModule,
    MatIconModule,
    MatProgressSpinnerModule,
    MatSlideToggleModule,
  ],
  templateUrl: './notificaciones-config.html',
  styleUrl: './notificaciones-config.scss',
})
export class NotificacionesConfig implements OnInit {
  private readonly fb = inject(FormBuilder);
  private readonly configService = inject(ConfiguracionNotificacionesService);
  private readonly notification = inject(NotificationService);
  private readonly changeDetector = inject(ChangeDetectorRef);

  cargando = false;
  guardando = false;

  readonly form = this.fb.nonNullable.group({
    stock_bajo: true,
    pedidos_pendientes: true,
    garantias_pendientes: true,
    presupuestos_pendientes: true,
    citas_proximas: true,
    ausencias_personal: true,
  });

  ngOnInit(): void {
    this.cargarConfiguracion();
  }

  cargarConfiguracion(): void {
    this.cargando = true;
    this.actualizarVista();

    this.configService.getConfiguracion().subscribe({
      next: configuracion => {
        this.form.patchValue(configuracion);
        this.cargando = false;
        this.actualizarVista();
      },
      error: error => {
        this.cargando = false;
        this.notification.showHttpError(error);
        this.actualizarVista();
      },
    });
  }

  guardar(): void {
    if (this.guardando) {
      return;
    }

    this.guardando = true;
    this.actualizarVista();

    const datos: Omit<ConfiguracionNotificaciones, 'id'> = this.form.getRawValue();
    this.configService.actualizar(datos).subscribe({
      next: configuracion => {
        this.form.patchValue(configuracion);
        this.guardando = false;
        this.notification.success('Configuración de notificaciones guardada.');
        this.actualizarVista();
      },
      error: error => {
        this.guardando = false;
        this.notification.showHttpError(error);
        this.actualizarVista();
      },
    });
  }

  private actualizarVista(): void {
    this.changeDetector.markForCheck();
    this.changeDetector.detectChanges();
  }
}
/** Selector de categorías de alertas que se muestran en el Dashboard. */
