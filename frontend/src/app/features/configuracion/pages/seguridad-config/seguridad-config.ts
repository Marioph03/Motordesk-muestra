import { ChangeDetectorRef, Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { AbstractControl, FormBuilder, ReactiveFormsModule, ValidationErrors, Validators } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';

import { SeguridadUsuario } from '../../models/seguridad';
import { SeguridadService } from '../../services/seguridad.service';
import { NotificationService } from '../../../../shared/services/notification';

@Component({
  selector: 'app-seguridad-config',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    MatButtonModule,
    MatCardModule,
    MatFormFieldModule,
    MatIconModule,
    MatInputModule,
    MatProgressSpinnerModule,
  ],
  templateUrl: './seguridad-config.html',
  styleUrl: './seguridad-config.scss',
})
export class SeguridadConfig implements OnInit {
  private readonly fb = inject(FormBuilder);
  private readonly seguridadService = inject(SeguridadService);
  private readonly notification = inject(NotificationService);
  private readonly changeDetector = inject(ChangeDetectorRef);

  usuario?: SeguridadUsuario;
  cargando = false;
  guardando = false;
  mostrarActual = false;
  mostrarNueva = false;
  mostrarRepetida = false;

  readonly form = this.fb.nonNullable.group(
    {
      password_actual: ['', Validators.required],
      password_nueva: ['', [Validators.required, Validators.minLength(8)]],
      repetir_password: ['', [Validators.required, Validators.minLength(8)]],
    },
    { validators: SeguridadConfig.passwordsIguales },
  );

  ngOnInit(): void {
    this.cargarUsuario();
  }

  cargarUsuario(): void {
    this.cargando = true;
    this.actualizarVista();

    this.seguridadService.getMiCuenta().subscribe({
      next: usuario => {
        this.usuario = usuario;
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

  cambiarPassword(): void {
    if (this.form.invalid || this.guardando) {
      this.form.markAllAsTouched();
      return;
    }

    const datos = this.form.getRawValue();
    this.guardando = true;
    this.actualizarVista();

    this.seguridadService.cambiarPassword({
      password_actual: datos.password_actual,
      password_nueva: datos.password_nueva,
    }).subscribe({
      next: respuesta => {
        this.guardando = false;
        this.form.reset();
        this.notification.success(respuesta.message || 'Contraseña actualizada correctamente.');
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
    this.changeDetector.markForCheck();
    this.changeDetector.detectChanges();
  }

  private static passwordsIguales(control: AbstractControl): ValidationErrors | null {
    const nueva = control.get('password_nueva')?.value;
    const repetida = control.get('repetir_password')?.value;

    if (!nueva || !repetida) {
      return null;
    }

    return nueva === repetida ? null : { passwordsNoCoinciden: true };
  }
}
/** Ajustes de credenciales de la sesión actual; no administra sesiones ajenas. */
