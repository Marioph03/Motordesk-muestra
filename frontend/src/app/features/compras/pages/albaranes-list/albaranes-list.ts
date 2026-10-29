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

import { AlbaranProveedor } from '../../models/albaran-proveedor';
import { AlbaranProveedorService } from '../../services/albaran-proveedor.service';
import { NotificationService } from '../../../../shared/services/notification';

@Component({
  selector: 'app-albaranes-list',
  standalone: true,
  imports: [
    CommonModule,
    RouterLink,
    MatButtonModule,
    MatCardModule,
    MatIconModule,
    MatTableModule,
    MatTooltipModule,
  ],
  templateUrl: './albaranes-list.html',
  styleUrl: './albaranes-list.scss',
})
export class AlbaranesList implements OnInit {
  private readonly service = inject(AlbaranProveedorService);
  private readonly notification = inject(NotificationService);
  private readonly changeDetector = inject(ChangeDetectorRef);
  private readonly destroyRef = inject(DestroyRef);

  albaranes: AlbaranProveedor[] = [];
  loading = false;
  displayedColumns = ['numero', 'numero_proveedor', 'fecha', 'estado', 'pedido', 'acciones'];

  ngOnInit(): void {
    this.cargar();
  }

  cargar(): void {
    this.loading = true;
    this.actualizarVista();
    this.service.listar().pipe(timeout(30_000), takeUntilDestroyed(this.destroyRef)).subscribe({
      next: albaranes => { this.albaranes = albaranes; this.loading = false; this.actualizarVista(); },
      error: error => {
        this.loading = false;
        this.actualizarVista();
        this.notification.showHttpError(error);
      },
    });
  }

  private actualizarVista(): void {
    this.changeDetector.markForCheck();
    this.changeDetector.detectChanges();
  }

  confirmar(albaran: AlbaranProveedor): void {
    if (albaran.estado !== 'BORRADOR') return;
    if (!window.confirm(`¿Confirmar el albarán ${albaran.numero_interno}? Las cantidades recibidas entrarán en stock.`)) return;

    this.service.confirmar(albaran.id).subscribe({
      next: () => {
        this.notification.success('Albarán confirmado y stock actualizado.');
        this.cargar();
      },
      error: error => this.notification.showHttpError(error),
    });
  }

  anular(albaran: AlbaranProveedor): void {
    if (albaran.estado !== 'BORRADOR') return;
    if (!window.confirm(`¿Anular ${albaran.numero_interno}?`)) return;

    this.service.anular(albaran.id).subscribe({
      next: () => {
        this.notification.success('Albarán anulado.');
        this.cargar();
      },
      error: error => this.notification.showHttpError(error),
    });
  }

  claseEstado(estado: string): string {
    return `estado-${estado.toLowerCase().replace(/_/g, '-')}`;
  }
}
/** Listado de albaranes de proveedor y su estado de confirmación. */
