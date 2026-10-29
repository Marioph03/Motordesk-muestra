import { ChangeDetectorRef, Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterLink } from '@angular/router';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { MatIconModule } from '@angular/material/icon';
import { MatTableModule } from '@angular/material/table';
import { MatTooltipModule } from '@angular/material/tooltip';

import { AlbaranVenta } from '../../models/albaran-venta';
import { AlbaranVentaService } from '../../services/albaran-venta.service';
import { NotificationService } from '../../../../shared/services/notification';
import { ConfirmationService } from '../../../../shared/services/confirmation.service';
import { FacturasService } from '../../../facturas/services/facturas.service';

@Component({
  selector: 'app-albaranes-venta-list',
  standalone: true,
  imports: [CommonModule, RouterLink, MatButtonModule, MatCardModule, MatCheckboxModule, MatIconModule, MatTableModule, MatTooltipModule],
  templateUrl: './albaranes-venta-list.html',
  styleUrl: './albaranes-venta-list.scss',
})
export class AlbaranesVentaList implements OnInit {
  private readonly service = inject(AlbaranVentaService);
  private readonly notification = inject(NotificationService);
  private readonly cdr = inject(ChangeDetectorRef);
  private readonly facturasService = inject(FacturasService);
  private readonly router = inject(Router);
  private readonly confirmation = inject(ConfirmationService);

  albaranes: AlbaranVenta[] = [];
  loading = false;
  facturando = false;
  seleccionados = new Set<number>();
  displayedColumns = ['seleccion', 'numero', 'cliente', 'fecha', 'estado', 'total', 'acciones'];

  ngOnInit(): void { this.cargar(); }

  cargar(): void {
    this.loading = true;
    this.service.listar().subscribe({
      next: albaranes => {
        this.albaranes = albaranes;
        this.seleccionados.clear();
        this.loading = false;
        this.cdr.detectChanges();
      },
      error: error => { this.loading = false; this.notification.showHttpError(error); this.cdr.detectChanges(); },
    });
  }

  confirmar(albaran: AlbaranVenta): void {
    this.confirmation.confirmar({
      title: 'Confirmar albarán de venta',
      message: `Al confirmar ${albaran.numero} se descontará el stock de todas sus líneas. Esta operación no se puede editar después.`,
      confirmText: 'Confirmar y descontar stock',
      confirmColor: 'primary',
    }).subscribe(confirmado => {
      if (!confirmado) return;
      this.service.confirmar(albaran.id).subscribe({
        next: () => { this.notification.success('Albarán confirmado y stock actualizado.'); this.cargar(); },
        error: error => this.notification.showHttpError(error),
      });
    });
  }

  anular(albaran: AlbaranVenta): void {
    this.confirmation.confirmar({
      title: 'Anular albarán de venta',
      message: `¿Deseas anular el albarán ${albaran.numero}?`,
      confirmText: 'Anular albarán',
    }).subscribe(confirmado => {
      if (!confirmado) return;
      this.service.anular(albaran.id).subscribe({
        next: () => { this.notification.success('Albarán anulado.'); this.cargar(); },
        error: error => this.notification.showHttpError(error),
      });
    });
  }

  facturar(albaran: AlbaranVenta): void {
    if (this.facturando || !this.puedeFacturarse(albaran)) return;
    this.confirmation.confirmar({
      title: 'Crear factura de recambio',
      message: `Se creará una factura en borrador a partir del albarán ${albaran.numero}.`,
      confirmText: 'Crear factura',
      confirmColor: 'primary',
    }).subscribe(confirmado => {
      if (!confirmado) return;
      this.facturando = true;
      this.facturasService.crearDesdeAlbaranVenta(albaran.id).subscribe({
        next: factura => {
          this.facturando = false;
          this.notification.success('Factura de recambio creada en borrador.');
          void this.router.navigate(['/facturas', factura.id]);
        },
        error: error => {
          this.facturando = false;
          this.notification.showHttpError(error);
        },
      });
    });
  }

  cambiarSeleccion(albaran: AlbaranVenta, seleccionado: boolean): void {
    if (!this.puedeFacturarse(albaran)) return;
    if (seleccionado) this.seleccionados.add(albaran.id);
    else this.seleccionados.delete(albaran.id);
  }

  puedeFacturarse(albaran: AlbaranVenta): boolean {
    return albaran.estado === 'CONFIRMADO' && !albaran.factura_id;
  }

  facturarSeleccionados(): void {
    const ids = Array.from(this.seleccionados);
    if (this.facturando || ids.length === 0) return;

    const clientes = new Set(
      this.albaranes
        .filter(albaran => this.seleccionados.has(albaran.id))
        .map(albaran => albaran.cliente_id),
    );
    if (clientes.size !== 1) {
      this.notification.error('Selecciona albaranes del mismo cliente.');
      return;
    }

    this.confirmation.confirmar({
      title: 'Crear factura de recambio',
      message: `Se creará una factura en borrador con los ${ids.length} albaranes seleccionados.`,
      confirmText: 'Crear factura',
      confirmColor: 'primary',
    }).subscribe(confirmado => {
      if (!confirmado) return;
      this.facturando = true;
      this.facturasService.crearDesdeAlbaranesVenta(ids).subscribe({
        next: factura => {
          this.facturando = false;
          this.notification.success('Factura de recambio creada en borrador.');
          void this.router.navigate(['/facturas', factura.id]);
        },
        error: error => {
          this.facturando = false;
          this.notification.showHttpError(error);
        },
      });
    });
  }

  nombreCliente(albaran: AlbaranVenta): string {
    return [albaran.cliente?.apellidos, albaran.cliente?.nombre].filter(Boolean).join(', ') || '-';
  }
}
