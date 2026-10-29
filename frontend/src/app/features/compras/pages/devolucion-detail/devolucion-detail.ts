import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatSelectModule } from '@angular/material/select';

import { DevolucionProveedor } from '../../models/devolucion-proveedor';
import { DevolucionProveedorService } from '../../services/devolucion-proveedor.service';
import { NotificationService } from '../../../../shared/services/notification';
import { AuthService } from '../../../../core/auth/auth.service';

@Component({ selector: 'app-devolucion-detail', standalone: true, imports: [CommonModule, RouterLink, MatButtonModule, MatCardModule, MatFormFieldModule, MatIconModule, MatSelectModule], templateUrl: './devolucion-detail.html', styleUrl: './devolucion-detail.scss' })
export class DevolucionDetail implements OnInit {
  private readonly route = inject(ActivatedRoute);
  private readonly service = inject(DevolucionProveedorService);
  private readonly notification = inject(NotificationService);
  readonly authService = inject(AuthService);
  devolucion?: DevolucionProveedor;
  loading = false;
  confirmando = false;
  resolviendo = false;
  resolucionSeleccionada = '';
  readonly resoluciones: DevolucionProveedor['resolucion'][] = ['ABONO', 'SUSTITUCION', 'RECHAZADA'];
  ngOnInit(): void { const id = Number(this.route.snapshot.paramMap.get('id')); if (!Number.isInteger(id) || id <= 0) { this.notification.error('Devolución no válida.'); return; } this.cargar(id); }
  cargar(id: number): void { this.loading = true; this.service.getById(id).subscribe({ next: devolucion => { this.devolucion = devolucion; this.resolucionSeleccionada = devolucion.resolucion === 'PENDIENTE' ? '' : devolucion.resolucion; this.loading = false; }, error: error => { this.loading = false; this.notification.showHttpError(error); } }); }
  confirmar(): void { if (!this.devolucion || this.devolucion.estado !== 'BORRADOR' || this.confirmando) return; if (!window.confirm('¿Confirmar esta devolución? Las unidades saldrán del stock del almacén.')) return; this.confirmando = true; this.service.confirmar(this.devolucion.id).subscribe({ next: devolucion => { this.devolucion = devolucion; this.confirmando = false; this.notification.success('Devolución confirmada y stock actualizado.'); }, error: error => { this.confirmando = false; this.notification.showHttpError(error); } }); }
  resolver(): void {
    if (!this.devolucion || this.devolucion.estado !== 'CONFIRMADA' || this.devolucion.resolucion !== 'PENDIENTE' || !this.resolucionSeleccionada || this.resolviendo) return;
    const resolucion = this.resolucionSeleccionada as 'ABONO' | 'SUSTITUCION' | 'RECHAZADA';
    if (!window.confirm(`¿Registrar la resolución como ${resolucion}?`)) return;
    this.resolviendo = true;
    this.service.resolver(this.devolucion.id, resolucion).subscribe({
      next: devolucion => { this.devolucion = devolucion; this.resolviendo = false; this.resolucionSeleccionada = devolucion.resolucion; this.notification.success('Resolución registrada correctamente.'); },
      error: error => { this.resolviendo = false; this.notification.showHttpError(error); },
    });
  }
  claseEstado(): string { return `estado-${this.devolucion?.estado.toLowerCase().replace(/_/g, '-') ?? 'desconocido'}`; }
  claseResolucion(): string { return `resolucion-${this.devolucion?.resolucion.toLowerCase().replace(/_/g, '-') ?? 'pendiente'}`; }
  totalUnidades(): number { return this.devolucion?.lineas.reduce((total, linea) => total + Number(linea.cantidad), 0) ?? 0; }
}
/** Detalle de devolución con sus líneas y transición de confirmación. */
