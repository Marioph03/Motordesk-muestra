import { ChangeDetectorRef, Component, OnInit, inject } from '@angular/core';
import { ReactiveFormsModule } from '@angular/forms';
import { FormBuilder, Validators } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSelectModule } from '@angular/material/select';
import { MatSlideToggleModule } from '@angular/material/slide-toggle';

import { ConfiguracionFacturacionService } from '../../services/configuracion-facturacion.service';
import { ModoFacturacion } from '../../models/configuracion-facturacion';
import { NotificationService } from '../../../../shared/services/notification';

@Component({
  selector: 'app-facturacion-config',
  standalone: true,
  imports: [ReactiveFormsModule, MatButtonModule, MatCardModule, MatFormFieldModule, MatIconModule, MatInputModule, MatProgressSpinnerModule, MatSelectModule, MatSlideToggleModule],
  templateUrl: './facturacion-config.html',
  styleUrl: './facturacion-config.scss',
})
export class FacturacionConfig implements OnInit {
  private readonly fb = inject(FormBuilder);
  private readonly service = inject(ConfiguracionFacturacionService);
  private readonly notification = inject(NotificationService);
  private readonly changeDetector = inject(ChangeDetectorRef);

  cargando = true;
  guardando = false;
  readonly form = this.fb.nonNullable.group({
    modo_facturacion: ['PRUEBAS' as ModoFacturacion, Validators.required],
    serie_pruebas: ['TP', [Validators.required, Validators.maxLength(20)]],
    serie_facturas: ['F', [Validators.required, Validators.maxLength(20)]],
    permitir_envio_aeat: [false],
  });

  get esModoPruebas(): boolean {
    return this.form.controls.modo_facturacion.value === 'PRUEBAS';
  }

  ngOnInit(): void {
    this.service.obtener().subscribe({
      next: configuracion => {
        this.form.patchValue(configuracion);
        this.cargando = false;
        this.actualizarVista();
      },
      error: error => {
        this.cargando = false;
        this.notification.showHttpError(error);
        this.actualizarVista();
      },
    });
  }

  guardar(): void {
    if (this.form.invalid || this.guardando) {
      this.form.markAllAsTouched();
      return;
    }
    this.guardando = true;
    const datos = this.form.getRawValue();
    if (datos.modo_facturacion === 'PRUEBAS') {
      datos.permitir_envio_aeat = false;
    }
    this.service.actualizar(datos).subscribe({
      next: configuracion => {
        this.form.patchValue(configuracion);
        this.guardando = false;
        this.notification.success('Configuración de facturación guardada.');
        this.actualizarVista();
      },
      error: error => {
        this.guardando = false;
        this.notification.showHttpError(error);
        this.actualizarVista();
      },
    });
  }

  private actualizarVista(): void {
    // Seguro durante ngOnInit y compatible con la detección zoneless.
    this.changeDetector.markForCheck();
  }
}
/** Configuración fiscal de series y modo de pruebas o VERI*FACTU. */
