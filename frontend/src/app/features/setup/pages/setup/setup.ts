import { CommonModule } from '@angular/common';
import { Component, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { MatButtonModule } from '@angular/material/button';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { finalize } from 'rxjs';

import {
  BootstrapInicialRequest,
  BootstrapService
} from '../../../../core/services/bootstrap.service';
import { AuthService } from '../../../../core/auth/auth.service';


@Component({
  selector: 'app-setup',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    MatButtonModule,
    MatFormFieldModule,
    MatIconModule,
    MatInputModule
  ],
  templateUrl: './setup.html',
  styleUrl: './setup.scss'
})
export class Setup {

  private readonly bootstrapService = inject(BootstrapService);
  private readonly authService = inject(AuthService);
  private readonly router = inject(Router);

  pasoActual = 1;
  cargando = false;
  error = '';

  datos: BootstrapInicialRequest = {
    nombre_empresa: '',
    nombre_comercial: '',
    nif: '',
    direccion: '',
    codigo_postal: '',
    ciudad: '',
    provincia: '',
    telefono: '',
    email_empresa: '',

    nombre_admin: '',
    apellidos_admin: '',
    email_admin: '',
    password_admin: '',

    iva_defecto: 21,
    regimen_fiscal: null,
    serie_facturas: 'F',
    serie_pruebas: 'TP'
  };


  siguientePaso(): void {
    this.error = '';

    if (this.pasoActual === 1) {
      if (!this.validarEmpresa()) {
        this.error = 'Completa todos los datos del taller.';
        return;
      }

      this.pasoActual = 2;
      return;
    }

    if (this.pasoActual === 2) {
      if (!this.validarAdministrador()) {
        this.error = 'Completa correctamente los datos del administrador.';
        return;
      }

      this.pasoActual = 3;
    }
  }


  pasoAnterior(): void {
    this.error = '';

    if (this.pasoActual > 1) {
      this.pasoActual--;
    }
  }


  finalizar(): void {
    this.error = '';

    if (!this.validarPasoFacturacion()) {
      return;
    }

    this.cargando = true;

    this.bootstrapService
      .inicializar(this.datos)
      .pipe(
        finalize(() => {
          this.cargando = false;
        })
      )
      .subscribe({
        next: () => {
          // Abrimos la primera sesión con las credenciales que acabamos de
          // crear. Así no hay que reescribirlas ni existe un salto de estado
          // entre el asistente y la pantalla de acceso.
          this.iniciarSesionAdministrador();
        },

        error: (error) => {
          this.error =
            error?.error?.detail ??
            'No se ha podido completar la configuración inicial.';
        }
      });
  }


  irAlLogin(): void {
    this.router.navigate(['/login']);
  }


  private iniciarSesionAdministrador(): void {
    this.cargando = true;

    this.authService.login({
      email: this.datos.email_admin.trim(),
      password: this.datos.password_admin,
    }).pipe(
      finalize(() => {
        this.cargando = false;
      })
    ).subscribe({
      next: respuesta => {
        this.authService.saveToken(respuesta.access_token);
        this.authService.establecerUsuarioActual(respuesta.usuario);
        void this.router.navigate(['/dashboard']);
      },
      error: error => {
        // La configuración ya se guardó. El mensaje real permite detectar un
        // problema de instalación sin ocultarlo tras un 401 genérico. No
        // reenviamos automáticamente al login para que el mensaje permanezca
        // visible y el usuario pueda pulsar el acceso cuando quiera.
        this.error = error?.error?.detail
          ?? 'La configuración se completó, pero no se pudo abrir la sesión.';
        this.pasoActual = 4;
      }
    });
  }


  private validarEmpresa(): boolean {
    return Boolean(
      this.datos.nombre_empresa.trim() &&
      this.datos.nombre_comercial.trim() &&
      this.datos.nif.trim() &&
      this.datos.direccion.trim() &&
      this.datos.codigo_postal.trim() &&
      this.datos.ciudad.trim() &&
      this.datos.provincia.trim() &&
      this.datos.telefono.trim() &&
      this.datos.email_empresa.trim()
    );
  }


  private validarAdministrador(): boolean {
    return Boolean(
      this.datos.nombre_admin.trim() &&
      this.datos.apellidos_admin.trim() &&
      this.datos.email_admin.trim() &&
      this.datos.password_admin.length >= 8
    );
  }


  private validarPasoFacturacion(): boolean {
    if (
      this.datos.iva_defecto < 0 ||
      this.datos.iva_defecto > 100
    ) {
      this.error = 'El IVA debe estar entre 0 y 100.';
      return false;
    }

    if (!this.datos.serie_facturas.trim()) {
      this.error = 'Introduce una serie para las facturas.';
      return false;
    }

    if (!this.datos.serie_pruebas.trim()) {
      this.error = 'Introduce una serie para las facturas de prueba.';
      return false;
    }

    return true;
  }

}
