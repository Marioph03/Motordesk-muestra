import { ChangeDetectorRef, Component, DestroyRef, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { timeout } from 'rxjs/operators';

import { FacturaProveedor } from '../../models/factura-proveedor';
import { FacturaProveedorService } from '../../services/factura-proveedor.service';
import { Proveedor } from '../../../proveedores/models/proveedor';
import { ProveedoresService } from '../../../proveedores/services/proveedores.service';
import { NotificationService } from '../../../../shared/services/notification';
import { AuthService } from '../../../../core/auth/auth.service';

@Component({
  selector: 'app-factura-proveedor-detail', standalone: true,
  imports: [CommonModule, FormsModule, RouterLink, MatButtonModule, MatCardModule, MatFormFieldModule, MatIconModule, MatInputModule, MatProgressSpinnerModule],
  templateUrl: './factura-proveedor-detail.html', styleUrl: './factura-proveedor-detail.scss',
})
export class FacturaProveedorDetail implements OnInit {
  private readonly route = inject(ActivatedRoute);
  private readonly service = inject(FacturaProveedorService);
  private readonly proveedoresService = inject(ProveedoresService);
  private readonly notification = inject(NotificationService);
  private readonly changeDetector = inject(ChangeDetectorRef);
  private readonly destroyRef = inject(DestroyRef);
  readonly authService = inject(AuthService);
  factura?: FacturaProveedor;
  proveedor?: Proveedor;
  cargando = false;
  procesandoPago = false;
  subiendoPdf = false;
  archivoSeleccionado?: File;
  fechaPago = this.fechaHoy();

  ngOnInit(): void {
    const id = Number(this.route.snapshot.paramMap.get('id'));
    if (!Number.isInteger(id) || id <= 0) { this.notification.error('Factura de proveedor no válida.'); return; }
    this.cargar(id);
  }
  cargar(id: number): void {
    this.cargando = true;
    this.actualizarVista();
    this.service.obtener(id).pipe(timeout(30_000), takeUntilDestroyed(this.destroyRef)).subscribe({
      next: factura => { this.factura = factura; this.fechaPago = factura.fecha_pago ?? this.fechaHoy(); this.cargando = false; this.actualizarVista(); this.cargarProveedor(factura.proveedor_id); },
      error: error => { this.cargando = false; this.actualizarVista(); this.notification.showHttpError(error); },
    });
  }
  marcarPagada(): void {
    if (!this.factura || this.factura.estado_pago === 'PAGADA' || this.procesandoPago) return;
    if (!window.confirm('¿Marcar esta factura como pagada?')) return;
    this.procesandoPago = true;
    this.service.marcarPagada(this.factura.id, this.fechaPago).subscribe({
      next: factura => { this.factura = factura; this.procesandoPago = false; this.actualizarVista(); this.notification.success('Factura marcada como pagada.'); },
      error: error => { this.procesandoPago = false; this.actualizarVista(); this.notification.showHttpError(error); },
    });
  }
  seleccionarPdf(event: Event): void {
    const archivo = (event.target as HTMLInputElement).files?.[0];
    if (!archivo || !this.factura || this.subiendoPdf) return;
    if (archivo.type !== 'application/pdf' || !archivo.name.toLowerCase().endsWith('.pdf')) {
      this.notification.error('Selecciona un archivo PDF válido.');
      return;
    }
    if (archivo.size > 10 * 1024 * 1024) {
      this.notification.error('El PDF no puede superar los 10 MB.');
      return;
    }
    this.archivoSeleccionado = archivo;
  }
  subirPdf(): void {
    const archivo = this.archivoSeleccionado;
    if (!archivo || !this.factura || this.subiendoPdf) return;
    this.subiendoPdf = true;
    this.service.subirPdf(this.factura.id, archivo).subscribe({
      next: factura => { this.factura = factura; this.archivoSeleccionado = undefined; this.subiendoPdf = false; this.actualizarVista(); this.notification.success('PDF original guardado correctamente.'); },
      error: error => { this.subiendoPdf = false; this.actualizarVista(); this.notification.showHttpError(error); },
    });
  }
  verPdf(): void {
    if (!this.factura?.archivo_pdf) return;
    const ventana = window.open(
      this.service.getPdfUrl(this.factura.id),
      '_blank',
      'noopener,noreferrer'
    );
    if (!ventana) {
      this.notification.error('El navegador ha bloqueado la apertura del PDF.');
    }
  }
  claseEstado(): string { return this.factura?.estado_pago === 'PAGADA' ? 'estado-pagada' : 'estado-pendiente'; }
  private cargarProveedor(id: number): void { this.proveedoresService.getProveedor(id).subscribe({ next: proveedor => { this.proveedor = proveedor; this.actualizarVista(); }, error: () => undefined }); }
  private actualizarVista(): void { this.changeDetector.markForCheck(); this.changeDetector.detectChanges(); }
  private fechaHoy(): string { const fecha = new Date(); return new Date(fecha.getTime() - fecha.getTimezoneOffset() * 60_000).toISOString().slice(0, 10); }
}
/** Detalle de factura proveedor con albaranes, adjunto PDF y estado de pago. */
