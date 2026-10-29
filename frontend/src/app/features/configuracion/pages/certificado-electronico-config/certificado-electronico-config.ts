import { ChangeDetectorRef, Component, OnInit, inject } from '@angular/core';
import { DatePipe } from '@angular/common';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';

import { CertificadoElectronicoEstado } from '../../models/certificado-electronico';
import { CertificadoElectronicoService } from '../../services/certificado-electronico.service';
import { NotificationService } from '../../../../shared/services/notification';

@Component({
  selector: 'app-certificado-electronico-config',
  standalone: true,
  imports: [DatePipe, ReactiveFormsModule, MatButtonModule, MatCardModule, MatFormFieldModule, MatIconModule, MatInputModule, MatProgressSpinnerModule],
  templateUrl: './certificado-electronico-config.html',
  styleUrl: './certificado-electronico-config.scss',
})
export class CertificadoElectronicoConfig implements OnInit {
  private readonly fb = inject(FormBuilder);
  private readonly service = inject(CertificadoElectronicoService);
  private readonly notification = inject(NotificationService);
  private readonly changeDetector = inject(ChangeDetectorRef);

  cargando = true;
  subiendo = false;
  eliminando = false;
  certificado?: CertificadoElectronicoEstado;
  archivoSeleccionado?: File;
  readonly form = this.fb.nonNullable.group({ password: ['', Validators.required] });

  ngOnInit(): void { this.cargar(); }

  seleccionarArchivo(evento: Event): void {
    const input = evento.target as HTMLInputElement;
    const archivo = input.files?.[0];
    if (!archivo) return;
    const extension = archivo.name.toLowerCase().split('.').pop();
    if (!['p12', 'pfx'].includes(extension ?? '')) {
      this.notification.error('Selecciona un certificado .p12 o .pfx.');
      input.value = '';
      return;
    }
    if (archivo.size > 10 * 1024 * 1024) {
      this.notification.error('El certificado no puede superar 10 MB.');
      input.value = '';
      return;
    }
    this.archivoSeleccionado = archivo;
    this.actualizarVista();
  }

  subir(): void {
    if (!this.archivoSeleccionado || this.form.invalid || this.subiendo) {
      this.form.markAllAsTouched();
      return;
    }
    this.subiendo = true;
    this.service.subir(this.archivoSeleccionado, this.form.controls.password.value).subscribe({
      next: () => {
        this.archivoSeleccionado = undefined;
        this.form.reset();
        this.notification.success('Certificado electrónico guardado y validado.');
        this.cargar();
      },
      error: error => {
        this.subiendo = false;
        this.notification.showHttpError(error);
        this.actualizarVista();
      },
    });
  }

  eliminar(): void {
    if (this.eliminando || !window.confirm('¿Eliminar el certificado electrónico? No podrás realizar envíos a AEAT hasta configurar otro.')) return;
    this.eliminando = true;
    this.service.eliminar().subscribe({
      next: () => {
        this.certificado = { configurado: false, activo: false, caducado: false };
        this.eliminando = false;
        this.notification.success('Certificado electrónico eliminado.');
        this.actualizarVista();
      },
      error: error => {
        this.eliminando = false;
        this.notification.showHttpError(error);
        this.actualizarVista();
      },
    });
  }

  private cargar(): void {
    this.cargando = true;
    this.service.obtenerEstado().subscribe({
      next: certificado => {
        this.certificado = certificado;
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

  private actualizarVista(): void { this.changeDetector.markForCheck(); }
}
