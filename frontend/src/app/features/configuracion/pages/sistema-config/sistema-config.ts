import { ChangeDetectorRef, Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { finalize } from 'rxjs';

import { BackupInfo, EstadoServicio, EstadoSistema } from '../../models/sistema';
import { SistemaService } from '../../services/sistema.service';
import { NotificationService } from '../../../../shared/services/notification';

@Component({
  selector: 'app-sistema-config',
  standalone: true,
  imports: [CommonModule, MatButtonModule, MatCardModule, MatIconModule, MatProgressSpinnerModule],
  templateUrl: './sistema-config.html',
  styleUrl: './sistema-config.scss',
})
export class SistemaConfig implements OnInit {
  private readonly sistemaService = inject(SistemaService);
  private readonly notification = inject(NotificationService);
  private readonly changeDetector = inject(ChangeDetectorRef);

  estado?: EstadoSistema;
  backup?: BackupInfo;
  cargando = false;
  creandoBackup = false;
  descargandoBackup = false;
  restableciendo = false;

  ngOnInit(): void { this.cargar(); }

  cargar(): void {
    this.cargando = true;
    let pendientes = 2;
    const finalizar = () => {
      pendientes -= 1;
      if (pendientes === 0) this.cargando = false;
      this.actualizarVista();
    };

    this.sistemaService.getEstado().subscribe({
      next: estado => { this.estado = estado; finalizar(); },
      error: error => { this.notification.showHttpError(error); finalizar(); },
    });
    this.sistemaService.getUltimoBackup().subscribe({
      next: backup => { this.backup = backup; finalizar(); },
      error: error => { this.notification.showHttpError(error); finalizar(); },
    });
    this.actualizarVista();
  }

  crearBackup(): void {
    if (this.creandoBackup) return;
    this.creandoBackup = true;
    this.actualizarVista();
    this.sistemaService.crearBackup().subscribe({
      next: respuesta => {
        this.creandoBackup = false;
        this.notification.success(respuesta.message || 'Copia de seguridad creada.');
        this.cargarBackup();
        this.actualizarVista();
      },
      error: error => {
        this.creandoBackup = false;
        this.notification.showHttpError(error);
        this.actualizarVista();
      },
    });
  }

  descargarBackup(): void {
    if (!this.backup?.disponible || this.descargandoBackup) return;
    this.descargandoBackup = true;
    this.actualizarVista();
    this.sistemaService.descargarBackup().subscribe({
      next: blob => {
        this.descargandoBackup = false;
        const url = window.URL.createObjectURL(blob);
        const enlace = document.createElement('a');
        enlace.href = url;
        enlace.download = this.backup?.nombre_archivo || 'motordesk-backup.dump';
        enlace.click();
        window.URL.revokeObjectURL(url);
        this.actualizarVista();
      },
      error: error => {
        this.descargandoBackup = false;
        this.notification.showHttpError(error);
        this.actualizarVista();
      },
    });
  }

  restablecerDatos(): void {
    if (this.restableciendo) return;
    const primerAviso = 'Se eliminarán clientes, vehículos, órdenes, facturas, compras, almacén y el resto de datos de prueba. Se conservarán empresa, usuarios, permisos, configuración e integraciones. ¿Continuar?';
    if (!confirm(primerAviso) || !confirm('Última confirmación: esta acción no se puede deshacer. ¿Restablecer los datos ahora?')) return;
    this.restableciendo = true;
    this.actualizarVista();
    this.sistemaService.restablecerDatos().pipe(finalize(() => { this.restableciendo = false; this.actualizarVista(); })).subscribe({
      next: respuesta => { this.notification.success(respuesta.message); this.cargar(); },
      error: error => this.notification.showHttpError(error),
    });
  }

  claseEstado(servicio?: EstadoServicio): string {
    const estado = servicio?.estado?.toUpperCase() ?? 'DESCONOCIDO';
    if (['OPERATIVO', 'CONFIGURADO', 'CONECTADO'].includes(estado)) return 'status-ok';
    if (['ERROR', 'DESCONECTADO'].includes(estado)) return 'status-error';
    return 'status-warning';
  }

  iconoEstado(servicio?: EstadoServicio): string {
    const clase = this.claseEstado(servicio);
    return clase === 'status-ok' ? 'check_circle' : clase === 'status-error' ? 'error' : 'warning';
  }

  formatearTamano(bytes?: number | null): string {
    if (bytes === null || bytes === undefined) return '-';
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 ** 2) return `${(bytes / 1024).toFixed(1)} KB`;
    if (bytes < 1024 ** 3) return `${(bytes / 1024 ** 2).toFixed(1)} MB`;
    return `${(bytes / 1024 ** 3).toFixed(2)} GB`;
  }

  private cargarBackup(): void {
    this.sistemaService.getUltimoBackup().subscribe({
      next: backup => { this.backup = backup; this.actualizarVista(); },
      error: error => this.notification.showHttpError(error),
    });
  }

  private actualizarVista(): void {
    this.changeDetector.markForCheck();
    this.changeDetector.detectChanges();
  }
}
/** Herramientas de mantenimiento y descarga de copias de seguridad autorizadas. */
