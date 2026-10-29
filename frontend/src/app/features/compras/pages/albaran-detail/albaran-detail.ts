import { ChangeDetectorRef, Component, DestroyRef, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { timeout } from 'rxjs/operators';

import { AlbaranProveedor } from '../../models/albaran-proveedor';
import { AlbaranProveedorService } from '../../services/albaran-proveedor.service';
import { NotificationService } from '../../../../shared/services/notification';
import { AuthService } from '../../../../core/auth/auth.service';

@Component({
  selector: 'app-albaran-detail',
  standalone: true,
  imports: [CommonModule, RouterLink, MatButtonModule, MatCardModule, MatIconModule, MatProgressSpinnerModule],
  templateUrl: './albaran-detail.html',
  styleUrl: './albaran-detail.scss',
})
export class AlbaranDetail implements OnInit {
  private readonly route = inject(ActivatedRoute);
  private readonly service = inject(AlbaranProveedorService);
  private readonly notification = inject(NotificationService);
  private readonly changeDetector = inject(ChangeDetectorRef);
  private readonly destroyRef = inject(DestroyRef);
  readonly authService = inject(AuthService);

  albaran?: AlbaranProveedor;
  cargando = false;
  confirmando = false;
  anulando = false;

  ngOnInit(): void {
    const id = Number(this.route.snapshot.paramMap.get('id'));
    if (!Number.isInteger(id) || id <= 0) {
      this.notification.error('Albarán no válido.');
      return;
    }
    this.cargar(id);
  }

  cargar(id: number): void {
    this.cargando = true;
    this.actualizarVista();
    this.service.getById(id).pipe(timeout(30_000), takeUntilDestroyed(this.destroyRef)).subscribe({
      next: albaran => { this.albaran = albaran; this.cargando = false; this.actualizarVista(); },
      error: error => { this.cargando = false; this.actualizarVista(); this.notification.showHttpError(error); },
    });
  }

  confirmar(): void {
    if (!this.albaran || this.albaran.estado !== 'BORRADOR' || this.confirmando) return;
    const aceptar = window.confirm(
      '¿Confirmar la recepción de este albarán?\n\nLas cantidades entrarán inmediatamente en el stock. Una vez confirmado no podrá modificarse.',
    );
    if (!aceptar) return;
    this.confirmando = true;
    this.service.confirmar(this.albaran.id).subscribe({
      next: albaran => {
        this.albaran = albaran;
        this.confirmando = false;
        this.notification.success('Recepción confirmada y stock actualizado.');
      },
      error: error => { this.confirmando = false; this.notification.showHttpError(error); },
    });
  }

  anular(): void {
    if (!this.albaran || this.albaran.estado !== 'BORRADOR' || this.anulando) return;
    if (!window.confirm(`¿Anular el albarán ${this.albaran.numero_interno}?`)) return;
    this.anulando = true;
    this.service.anular(this.albaran.id).subscribe({
      next: albaran => { this.albaran = albaran; this.anulando = false; this.notification.success('Albarán anulado.'); },
      error: error => { this.anulando = false; this.notification.showHttpError(error); },
    });
  }

  verPdf(): void {
    if (!this.albaran) return;
    window.open(this.service.pdfUrl(this.albaran.id), '_blank', 'noopener');
  }

  totalUnidades(): number {
    return this.albaran?.lineas.reduce((total, linea) => total + Number(linea.cantidad_recibida ?? 0), 0) ?? 0;
  }

  totalCoste(): number {
    return this.albaran?.lineas.reduce((total, linea) => total + Number(linea.cantidad_recibida ?? 0) * Number(linea.coste_unitario ?? 0), 0) ?? 0;
  }

  claseEstado(): string {
    return `estado-${this.albaran?.estado.toLowerCase().replace(/_/g, '-') ?? 'desconocido'}`;
  }

  private actualizarVista(): void {
    this.changeDetector.markForCheck();
    this.changeDetector.detectChanges();
  }
}
/** Detalle de albarán: revisión de líneas y confirmación trazable de entrada. */
