import { ChangeDetectorRef, Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatDividerModule } from '@angular/material/divider';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSlideToggleModule } from '@angular/material/slide-toggle';

import { ConfiguracionDocumentos } from '../../models/configuracion-documentos';
import { ConfiguracionTaller } from '../../models/configuracion-taller';
import { ConfiguracionDocumentosService } from '../../services/configuracion-documentos.service';
import { ConfiguracionTallerService } from '../../services/configuracion-taller.service';
import { NotificationService } from '../../../../shared/services/notification';

@Component({
  selector: 'app-documentos-config',
  standalone: true,
  imports: [
    CommonModule, ReactiveFormsModule, MatButtonModule, MatCardModule,
    MatDividerModule, MatFormFieldModule, MatIconModule, MatInputModule,
    MatProgressSpinnerModule, MatSlideToggleModule
  ],
  templateUrl: './documentos-config.html',
  styleUrl: './documentos-config.scss'
})
export class DocumentosConfig implements OnInit {
  private readonly fb = inject(FormBuilder);
  private readonly configService = inject(ConfiguracionDocumentosService);
  private readonly tallerService = inject(ConfiguracionTallerService);
  private readonly notification = inject(NotificationService);
  private readonly changeDetector = inject(ChangeDetectorRef);

  cargando = false;
  guardando = false;
  taller?: ConfiguracionTaller;
  logoUrl: string | null = null;

  readonly form = this.fb.group({
    mostrar_telefono: [true],
    mostrar_email: [true],
    mostrar_direccion: [true],
    mostrar_nif_cif: [true],
    mostrar_web: [false],
    iban_cobros: ['', [Validators.maxLength(34)]],
    validez_presupuesto_dias: [30, [Validators.required, Validators.min(1), Validators.max(365)]],
    pie_documentos: [''],
    observaciones_presupuesto: [''],
    observaciones_orden: [''],
    observaciones_pedido_compra: ['']
  });

  ngOnInit(): void {
    this.cargarConfiguracion();
    this.cargarTaller();
  }

  cargarConfiguracion(): void {
    this.cargando = true;
    this.actualizarVista();
    this.configService.getConfiguracion().subscribe({
      next: config => {
        this.form.patchValue({
          mostrar_telefono: config.mostrar_telefono,
          mostrar_email: config.mostrar_email,
          mostrar_direccion: config.mostrar_direccion,
          mostrar_nif_cif: config.mostrar_nif_cif,
          mostrar_web: config.mostrar_web,
          iban_cobros: config.iban_cobros ?? '',
          validez_presupuesto_dias: config.validez_presupuesto_dias,
          pie_documentos: config.pie_documentos ?? '',
          observaciones_presupuesto: config.observaciones_presupuesto ?? '',
          observaciones_orden: config.observaciones_orden ?? '',
          observaciones_pedido_compra: config.observaciones_pedido_compra ?? ''
        });
        this.cargando = false;
        this.actualizarVista();
      },
      error: error => {
        this.cargando = false;
        this.notification.showHttpError(error);
        this.actualizarVista();
      }
    });
  }

  cargarTaller(): void {
    this.tallerService.getConfiguracion().subscribe({
      next: taller => {
        this.taller = taller;
        this.logoUrl = this.tallerService.getLogoUrl(taller.logo_url);
        this.actualizarVista();
      },
      error: error => this.notification.showHttpError(error)
    });
  }

  guardar(): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }

    this.guardando = true;
    const datos = this.form.getRawValue();
    const configuracion: Omit<ConfiguracionDocumentos, 'id'> = {
      mostrar_telefono: datos.mostrar_telefono ?? true,
      mostrar_email: datos.mostrar_email ?? true,
      mostrar_direccion: datos.mostrar_direccion ?? true,
      mostrar_nif_cif: datos.mostrar_nif_cif ?? true,
      mostrar_web: datos.mostrar_web ?? false,
      iban_cobros: datos.iban_cobros?.replace(/\s/g, '').toUpperCase() || null,
      validez_presupuesto_dias: Number(datos.validez_presupuesto_dias ?? 30),
      pie_documentos: datos.pie_documentos?.trim() || null,
      observaciones_presupuesto: datos.observaciones_presupuesto?.trim() || null,
      observaciones_orden: datos.observaciones_orden?.trim() || null,
      observaciones_pedido_compra: datos.observaciones_pedido_compra?.trim() || null
    };

    this.configService.actualizar(configuracion).subscribe({
      next: respuesta => {
        this.form.patchValue(respuesta);
        this.guardando = false;
        this.notification.success('Configuración de documentos guardada.');
        this.actualizarVista();
      },
      error: error => {
        this.guardando = false;
        this.notification.showHttpError(error);
        this.actualizarVista();
      }
    });
  }

  private actualizarVista(): void {
    this.changeDetector.markForCheck();
    this.changeDetector.detectChanges();
  }
}
/** Preferencias de documentos con previsualización, reutilizadas por los PDFs. */
