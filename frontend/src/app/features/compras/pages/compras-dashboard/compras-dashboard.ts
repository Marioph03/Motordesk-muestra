import { ChangeDetectorRef, Component, DestroyRef, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { timeout } from 'rxjs/operators';

import { ComprasResumen } from '../../models/compras-resumen';
import { ComprasDashboardService } from '../../services/compras-dashboard.service';
import { NotificationService } from '../../../../shared/services/notification';

@Component({
  selector: 'app-compras-dashboard',
  standalone: true,
  imports: [CommonModule, RouterLink, MatCardModule, MatIconModule, MatProgressSpinnerModule],
  templateUrl: './compras-dashboard.html',
  styleUrl: './compras-dashboard.scss',
})
export class ComprasDashboard implements OnInit {
  private readonly service = inject(ComprasDashboardService);
  private readonly notification = inject(NotificationService);
  private readonly changeDetector = inject(ChangeDetectorRef);
  private readonly destroyRef = inject(DestroyRef);

  resumen: ComprasResumen | null = null;
  cargando = false;

  ngOnInit(): void { this.cargar(); }

  cargar(): void {
    this.cargando = true;
    this.actualizarVista();
    this.service.getResumen().pipe(timeout(30_000), takeUntilDestroyed(this.destroyRef)).subscribe({
      next: resumen => { this.resumen = resumen; this.cargando = false; this.actualizarVista(); },
      error: error => { this.cargando = false; this.actualizarVista(); this.notification.showHttpError(error); },
    });
  }

  get hayAlertas(): boolean {
    return !!this.resumen && (
      this.resumen.pedidos_pendientes > 0 ||
      this.resumen.albaranes_borrador > 0 ||
      this.resumen.facturas_proximas_vencer > 0 ||
      this.resumen.devoluciones_pendientes > 0
    );
  }

  private actualizarVista(): void {
    this.changeDetector.markForCheck();
    this.changeDetector.detectChanges();
  }
}
/** Resumen de compras para controlar pedidos, recepciones y facturas proveedor. */
