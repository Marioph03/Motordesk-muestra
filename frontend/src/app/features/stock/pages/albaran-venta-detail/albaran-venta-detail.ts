import { ChangeDetectorRef, Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatTableModule } from '@angular/material/table';
import { AlbaranVentaService } from '../../services/albaran-venta.service';
import { AlbaranVenta } from '../../models/albaran-venta';
import { NotificationService } from '../../../../shared/services/notification';

@Component({
  selector: 'app-albaran-venta-detail', standalone: true,
  imports: [CommonModule, RouterLink, MatButtonModule, MatCardModule, MatIconModule, MatProgressSpinnerModule, MatTableModule],
  templateUrl: './albaran-venta-detail.html', styleUrl: './albaran-venta-detail.scss',
})
export class AlbaranVentaDetail implements OnInit {
  private readonly route = inject(ActivatedRoute);
  private readonly service = inject(AlbaranVentaService);
  private readonly notification = inject(NotificationService);
  private readonly cdr = inject(ChangeDetectorRef);
  albaran?: AlbaranVenta;
  cargando = true;
  descargando = false;
  columnas = ['referencia', 'descripcion', 'cantidad', 'precio', 'descuento', 'total'];

  ngOnInit(): void {
    const id = Number(this.route.snapshot.paramMap.get('id'));
    if (!Number.isInteger(id) || id <= 0) { this.cargando = false; this.cdr.detectChanges(); this.notification.error('Albarán no válido.'); return; }
    this.service.obtener(id).subscribe({
      next: a => { this.albaran = a; this.cargando = false; this.actualizarVista(); },
      error: e => { this.cargando = false; this.actualizarVista(); this.notification.showHttpError(e); },
    });
  }

  verPdf(): void {
    if (!this.albaran || this.descargando) return;
    this.descargando = true;
    this.service.descargarPdf(this.albaran.id).subscribe({
      next: pdf => { this.descargando = false; this.actualizarVista(); const url = URL.createObjectURL(pdf); window.open(url, '_blank', 'noopener'); setTimeout(() => URL.revokeObjectURL(url), 60_000); },
      error: e => { this.descargando = false; this.actualizarVista(); this.notification.showHttpError(e); },
    });
  }

  nombreCliente(): string { return [this.albaran?.cliente?.apellidos, this.albaran?.cliente?.nombre].filter(Boolean).join(', ') || '-'; }
  private actualizarVista(): void { this.cdr.markForCheck(); this.cdr.detectChanges(); }
}
