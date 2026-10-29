import { Component, inject } from '@angular/core';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router } from '@angular/router';

import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';

import { AuthService } from '../../../../core/auth/auth.service';
import { TokenResponse } from '../../../../core/models/token';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [
    ReactiveFormsModule,
    MatCardModule,
    MatFormFieldModule,
    MatInputModule,
    MatButtonModule
  ],
  templateUrl: './login.html',
  styleUrl: './login.scss'
})
export class Login {
  private readonly fb = inject(FormBuilder);
  private readonly authService = inject(AuthService);
  private readonly router = inject(Router);

  readonly loginForm: FormGroup = this.fb.nonNullable.group({
    email: ['', [Validators.required, Validators.email]],
    password: ['', Validators.required]
  });

  readonly registerForm: FormGroup = this.fb.nonNullable.group({
    nombre: ['', Validators.required],
    apellidos: ['', Validators.required],
    email: ['', [Validators.required, Validators.email]],
    password: ['', [Validators.required, Validators.minLength(6)]],
    confirmarPassword: ['', Validators.required]
  });

  modoRegistro = false;
  mensajeAcceso = '';
  enviando = false;

  login(): void {
    if (this.loginForm.invalid || this.enviando) {
      this.loginForm.markAllAsTouched();
      return;
    }

    this.enviando = true;
    this.mensajeAcceso = '';
    const credenciales = this.loginForm.getRawValue();

    this.authService.login({
      email: credenciales.email.trim(),
      password: credenciales.password,
    }).subscribe({
      next: response => this.completarAcceso(response),
      error: error => {
        this.enviando = false;
        this.mensajeAcceso =
          'No se ha podido iniciar sesión. Si aún no tienes cuenta, puedes registrarte.';
      }
    });
  }

  mostrarRegistro(): void {
    this.modoRegistro = true;
    this.mensajeAcceso = '';
    this.registerForm.patchValue({
      email: this.loginForm.controls['email'].value
    });
  }

  mostrarInicioSesion(): void {
    this.modoRegistro = false;
    this.mensajeAcceso = '';
  }

  registrar(): void {
    if (this.registerForm.invalid || this.enviando) {
      this.registerForm.markAllAsTouched();
      return;
    }

    const datos = this.registerForm.getRawValue();
    if (datos.password !== datos.confirmarPassword) {
      this.registerForm.controls['confirmarPassword'].setErrors({ mismatch: true });
      return;
    }

    this.enviando = true;
    this.mensajeAcceso = '';
    this.authService.register({
      nombre: datos.nombre.trim(),
      apellidos: datos.apellidos.trim(),
      email: datos.email.trim(),
      password: datos.password
    }).subscribe({
      next: response => this.completarAcceso(response),
      error: error => {
        this.enviando = false;
        this.mensajeAcceso =
          error.error?.detail ?? 'No se ha podido registrar la cuenta.';
      }
    });
  }

  private completarAcceso(response: TokenResponse): void {
    this.authService.saveToken(response.access_token);
    this.authService.establecerUsuarioActual(response.usuario);
    void this.router.navigate(['/dashboard']);
  }
}
/** Entrada pública de login y registro, incluida la recuperación tras sesión caducada. */
