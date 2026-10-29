import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatTableModule } from '@angular/material/table';

import { DevolucionProveedor } from '../../models/devolucion-proveedor';
import { DevolucionProveedorService } from '../../services/devolucion-proveedor.service';
import { NotificationService } from '../../../../shared/services/notification';

@Component({ selector: 'app-devoluciones-list', standalone: true, imports: [CommonModule, RouterLink, MatButtonModule, MatCardModule, MatIconModule, MatTableModule], templateUrl: './devoluciones-list.html', styleUrl: './devoluciones-list.scss' })
export class DevolucionesList implements OnInit {
  private readonly service = inject(DevolucionProveedorService);
  private readonly notification = inject(NotificationService);
  devoluciones: DevolucionProveedor[] = [];
  loading = false;
  error = '';
  readonly displayedColumns = ['numero', 'fecha', 'motivo', 'estado', 'resolucion', 'albaran', 'acciones'];
  ngOnInit(): void { this.cargar(); }
  cargar(): void {
    this.loading = true;
    this.error = '';
    this.service.listar().subscribe({
      next: devoluciones => {
        this.devoluciones = devoluciones;
        this.loading = false;
      },
      error: error => {
        this.loading = false;
        this.error = error?.error?.detail ?? 'No se han podido cargar las devoluciones.';
        this.notification.showHttpError(error);
      },
    });
  }
  claseEstado(estado: string): string { return `estado-${estado.toLowerCase().replace(/_/g, '-')}`; }
  claseResolucion(resolucion: string): string { return `resolucion-${resolucion.toLowerCase().replace(/_/g, '-')}`; }
}
/** Listado de devoluciones a proveedor y su seguimiento operativo. */
