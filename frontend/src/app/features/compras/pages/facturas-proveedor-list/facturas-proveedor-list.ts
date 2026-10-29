import { ChangeDetectorRef, Component, DestroyRef, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatTableModule } from '@angular/material/table';
import { MatTooltipModule } from '@angular/material/tooltip';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { timeout } from 'rxjs/operators';

import { FacturaProveedor } from '../../models/factura-proveedor';
import { FacturaProveedorService } from '../../services/factura-proveedor.service';
import { Proveedor } from '../../../proveedores/models/proveedor';
import { ProveedoresService } from '../../../proveedores/services/proveedores.service';
import { NotificationService } from '../../../../shared/services/notification';

@Component({
  selector: 'app-facturas-proveedor-list', standalone: true,
  imports: [CommonModule, RouterLink, MatButtonModule, MatCardModule, MatIconModule, MatTableModule, MatTooltipModule],
  templateUrl: './facturas-proveedor-list.html', styleUrl: './facturas-proveedor-list.scss',
})
export class FacturasProveedorList implements OnInit {
  private readonly service = inject(FacturaProveedorService);
  private readonly proveedoresService = inject(ProveedoresService);
  private readonly notification = inject(NotificationService);
  private readonly changeDetector = inject(ChangeDetectorRef);
  private readonly destroyRef = inject(DestroyRef);
  facturas: FacturaProveedor[] = [];
  proveedores: Proveedor[] = [];
  loading = false;
  readonly displayedColumns = ['numero', 'tipo', 'proveedor', 'fecha', 'vencimiento', 'total', 'estado', 'pdf', 'acciones'];

  ngOnInit(): void { this.cargar(); this.cargarProveedores(); }
  cargar(): void {
    this.loading = true;
    this.actualizarVista();
    this.service.listar().pipe(timeout(30_000), takeUntilDestroyed(this.destroyRef)).subscribe({
      next: facturas => { this.facturas = facturas; this.loading = false; this.actualizarVista(); },
      error: error => { this.loading = false; this.actualizarVista(); this.notification.showHttpError(error); },
    });
  }
  private cargarProveedores(): void {
    this.proveedoresService.getProveedores().subscribe({
      next: proveedores => { this.proveedores = proveedores; this.actualizarVista(); },
      error: error => this.notification.showHttpError(error),
    });
  }
  nombreProveedor(id: number): string { return this.proveedores.find(item => item.id === id)?.nombre ?? `Proveedor #${id}`; }
  etiquetaTipo(tipo: FacturaProveedor['tipo_gasto']): string { return { COMPRA: 'Compra', SUMINISTRO: 'Suministro', REPARACION: 'Reparacion', OTRO: 'Otro' }[tipo]; }
  claseEstado(estado: string): string { return estado === 'PAGADA' ? 'estado-pagada' : 'estado-pendiente'; }
  private actualizarVista(): void { this.changeDetector.markForCheck(); this.changeDetector.detectChanges(); }
}
/** Listado de facturas recibidas y acceso a su revisión y pago. */
