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

import { ConfiguracionTaller } from '../../models/configuracion-taller';
import { ConfiguracionTallerService } from '../../services/configuracion-taller.service';
import { NotificationService } from '../../../../shared/services/notification';

@Component({
  selector: 'app-taller-config',
  standalone: true,
  imports: [
    CommonModule, ReactiveFormsModule, MatButtonModule, MatCardModule,
    MatDividerModule, MatFormFieldModule, MatIconModule, MatInputModule,
    MatProgressSpinnerModule
  ],
  templateUrl: './taller-config.html',
  styleUrl: './taller-config.scss'
})
export class TallerConfig implements OnInit {
  private readonly fb = inject(FormBuilder);
  private readonly configuracionService = inject(ConfiguracionTallerService);
  private readonly notification = inject(NotificationService);
  private readonly changeDetector = inject(ChangeDetectorRef);

  configuracion?: ConfiguracionTaller;
  cargando = false;
  guardando = false;
  subiendoLogo = false;
  logoPreview: string | null = null;

  readonly form = this.fb.group({
    nombre_comercial: [''],
    razon_social: [''],
    nif_cif: [''],
    telefono: [''],
    email: ['', Validators.email],
    web: [''],
    direccion: [''],
    codigo_postal: [''],
    localidad: [''],
    provincia: [''],
    pais: ['España']
  });

  ngOnInit(): void {
    this.cargarConfiguracion();
  }

  cargarConfiguracion(): void {
    this.cargando = true;
    this.actualizarVista();
    this.configuracionService.getConfiguracion().subscribe({
      next: configuracion => {
        this.configuracion = configuracion;
        this.form.patchValue({
          nombre_comercial: configuracion.nombre_comercial ?? '',
          razon_social: configuracion.razon_social ?? '',
          nif_cif: configuracion.nif_cif ?? '',
          telefono: configuracion.telefono ?? '',
          email: configuracion.email ?? '',
          web: configuracion.web ?? '',
          direccion: configuracion.direccion ?? '',
          codigo_postal: configuracion.codigo_postal ?? '',
          localidad: configuracion.localidad ?? '',
          provincia: configuracion.provincia ?? '',
          pais: configuracion.pais ?? 'España'
        });
        this.logoPreview = this.configuracionService.getLogoUrl(configuracion.logo_url);
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

  guardar(): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }
    this.guardando = true;
    const valor = this.form.getRawValue();
    this.configuracionService.actualizar(valor).subscribe({
      next: configuracion => {
        this.configuracion = configuracion;
        this.guardando = false;
        this.notification.success('Configuración del taller guardada.');
        this.actualizarVista();
      },
      error: error => {
        this.guardando = false;
        this.notification.showHttpError(error);
        this.actualizarVista();
      }
    });
  }

  seleccionarLogo(evento: Event): void {
    const input = evento.target as HTMLInputElement;
    const archivo = input.files?.[0];
    input.value = '';
    if (!archivo) {
      return;
    }
    if (!['image/jpeg', 'image/png', 'image/webp'].includes(archivo.type)) {
      this.notification.error('Selecciona un logo JPG, PNG o WEBP.');
      return;
    }
    if (archivo.size > 5 * 1024 * 1024) {
      this.notification.error('El logo no puede superar los 5 MB.');
      return;
    }

    this.subiendoLogo = true;
    this.configuracionService.subirLogo(archivo).subscribe({
      next: configuracion => {
        this.configuracion = configuracion;
        this.logoPreview = this.configuracionService.getLogoUrl(configuracion.logo_url);
        this.subiendoLogo = false;
        this.notification.success('Logo actualizado correctamente.');
        this.actualizarVista();
      },
      error: error => {
        this.subiendoLogo = false;
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
/** Configuración de identidad corporativa y carga del logo del taller. */
