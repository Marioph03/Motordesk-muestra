import { ChangeDetectorRef, Component, OnInit, inject } from '@angular/core';
import { finalize, timeout } from 'rxjs';
import { CommonModule } from '@angular/common';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatChipsModule } from '@angular/material/chips';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';
import { MatDividerModule } from '@angular/material/divider';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatSlideToggleModule } from '@angular/material/slide-toggle';
import { MatTableModule } from '@angular/material/table';

import { AuthService } from '../../../../core/auth/auth.service';
import { NotificationService } from '../../../../shared/services/notification';
import { AusenciaPersonal } from '../../models/ausencia-personal';
import { Personal } from '../../models/personal';
import { Rol } from '../../models/rol';
import { AusenciasPersonalService } from '../../services/ausencias-personal.service';
import {
  PersonalCreate,
  PersonalService,
  PersonalUpdate
} from '../../services/personal.service';
import { PermisosService } from '../../services/permisos.service';
import { AusenciaPersonalDialog } from '../ausencia-personal-dialog/ausencia-personal-dialog';
import { ResumenOperativoPersonal } from '../../models/resumen-operativo-personal';

@Component({
  selector: 'app-personal-form',
  standalone: true,
  imports: [
    CommonModule, ReactiveFormsModule, RouterLink, MatButtonModule,
    MatCardModule, MatChipsModule, MatDialogModule, MatDividerModule,
    MatFormFieldModule, MatIconModule, MatInputModule, MatSelectModule,
    MatSlideToggleModule, MatTableModule
  ],
  templateUrl: './personal-form.html',
  styleUrl: './personal-form.scss'
})
export class PersonalForm implements OnInit {
  private readonly fb = inject(FormBuilder);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly personalService = inject(PersonalService);
  private readonly ausenciasService = inject(AusenciasPersonalService);
  private readonly permisosService = inject(PermisosService);
  private readonly notification = inject(NotificationService);
  private readonly dialog = inject(MatDialog);
  private readonly cdr = inject(ChangeDetectorRef);
  readonly authService = inject(AuthService);

  readonly displayedColumns = ['tipo', 'inicio', 'fin', 'observaciones', 'acciones'];
  readonly form = this.fb.nonNullable.group({
    nombre: ['', Validators.required],
    apellidos: ['', Validators.required],
    email: ['', [Validators.required, Validators.email]],
    rol: ['', Validators.required],
    activo: [true],
    password: ['', [Validators.minLength(6)]]
  });

  usuarioId?: number;
  usuario?: Personal;
  roles: Rol[] = [];
  ausencias: AusenciaPersonal[] = [];
  resumenOperativo?: ResumenOperativoPersonal;
  cargando = true;
  guardando = false;

  get puedeEditar(): boolean {
    return this.authService.tienePermiso('personal.editar');
  }

  get esNuevo(): boolean {
    return this.usuarioId === undefined;
  }

  ngOnInit(): void {
    const idParam = this.route.snapshot.paramMap.get('id');

    if (idParam === null) {
      this.cargando = false;
      this.cargarRoles();
      return;
    }

    const id = Number(idParam);
    if (!Number.isInteger(id) || id <= 0) {
      void this.router.navigate(['/personal']);
      return;
    }

    this.usuarioId = id;
    this.cargarUsuario();
    this.cargarAusencias();
    this.cargarResumenOperativo();
    this.cargarRoles();
  }

  cargarUsuario(): void {
    if (!this.usuarioId) return;
    this.personalService.getUsuario(this.usuarioId).pipe(
      timeout(8_000),
      finalize(() => {
        this.cargando = false;
        this.cdr.markForCheck();
      })
    ).subscribe({
      next: usuario => {
        this.usuario = usuario;
        this.form.patchValue({
          nombre: usuario.nombre, apellidos: usuario.apellidos,
          email: usuario.email, rol: usuario.rol, activo: usuario.activo
        });
      },
      error: error => {
        this.notification.showHttpError(error);
      }
    });
  }

  cargarRoles(): void {
    if (!this.authService.tienePermiso('permisos.gestionar')) return;
    this.permisosService.getRoles().pipe(timeout(8_000)).subscribe({
      next: roles => this.roles = roles.filter(rol => rol.activo),
      error: error => this.notification.showHttpError(error)
    });
  }

  cargarAusencias(): void {
    if (!this.usuarioId) return;
    this.ausenciasService.getAusenciasUsuario(this.usuarioId).pipe(
      timeout(8_000)
    ).subscribe({
      next: ausencias => {
        this.ausencias = ausencias;
        this.cdr.markForCheck();
      },
      error: error => this.notification.showHttpError(error)
    });
  }

  cargarResumenOperativo(): void {
    if (!this.usuarioId) return;

    this.personalService.getResumenOperativo(this.usuarioId).pipe(
      timeout(8_000)
    ).subscribe({
      next: resumen => {
        this.resumenOperativo = resumen;
        this.cdr.markForCheck();
      },
      error: error => this.notification.showHttpError(error)
    });
  }

  guardar(): void {
    if (!this.puedeEditar || this.form.invalid || this.guardando) {
      this.form.markAllAsTouched();
      return;
    }

    const valor = this.form.getRawValue();

    if (this.esNuevo && !valor.password) {
      this.form.controls.password.setErrors({ required: true });
      this.form.controls.password.markAsTouched();
      return;
    }

    this.guardando = true;
    const datosBase: PersonalUpdate = {
      nombre: valor.nombre,
      apellidos: valor.apellidos,
      email: valor.email,
      rol: valor.rol,
      activo: valor.activo
    };

    const solicitud = this.esNuevo
      ? this.personalService.crearUsuario({
        ...datosBase,
        password: valor.password
      } satisfies PersonalCreate)
      : this.personalService.actualizarUsuario(
        this.usuarioId!,
        datosBase
      );

    solicitud.subscribe({
      next: usuario => {
        this.usuario = usuario;
        this.guardando = false;
        this.notification.success(
          this.esNuevo
            ? 'Usuario registrado correctamente.'
            : 'Personal actualizado correctamente.'
        );
        void this.router.navigate(['/personal', usuario.id]);
      },
      error: error => {
        this.guardando = false;
        this.notification.showHttpError(error);
      }
    });
  }

  nuevaAusencia(): void {
    if (!this.usuarioId || !this.puedeEditar) return;
    this.dialog.open(AusenciaPersonalDialog, {
      width: '520px', data: { usuarioId: this.usuarioId }
    }).afterClosed().subscribe(resultado => {
      if (!resultado) return;
      this.ausenciasService.crearAusencia(resultado).subscribe({
        next: () => { this.notification.success('Ausencia registrada.'); this.cargarAusencias(); this.cargarResumenOperativo(); },
        error: error => this.notification.showHttpError(error)
      });
    });
  }

  editarAusencia(ausencia: AusenciaPersonal): void {
    if (!this.puedeEditar) return;
    this.dialog.open(AusenciaPersonalDialog, {
      width: '520px', data: { usuarioId: ausencia.usuario_id, ausencia }
    }).afterClosed().subscribe(resultado => {
      if (!resultado) return;
      this.ausenciasService.actualizarAusencia(ausencia.id, resultado).subscribe({
        next: () => { this.notification.success('Ausencia actualizada.'); this.cargarAusencias(); this.cargarResumenOperativo(); },
        error: error => this.notification.showHttpError(error)
      });
    });
  }

  eliminarAusencia(ausencia: AusenciaPersonal): void {
    if (!this.puedeEditar || !window.confirm('¿Eliminar esta ausencia?')) return;
    this.ausenciasService.eliminarAusencia(ausencia.id).subscribe({
      next: () => { this.notification.success('Ausencia eliminada.'); this.cargarAusencias(); this.cargarResumenOperativo(); },
      error: error => this.notification.showHttpError(error)
    });
  }

  getFechaFinVisible(ausencia: AusenciaPersonal): Date {
    const fechaFin = new Date(ausencia.fecha_fin);

    // Las ausencias nuevas se persisten con fin exclusivo a las 00:00.
    // Para la tabla se presenta el último día que realmente está incluido.
    if (
      fechaFin.getHours() === 0
      && fechaFin.getMinutes() === 0
      && fechaFin.getSeconds() === 0
    ) {
      fechaFin.setDate(fechaFin.getDate() - 1);
    }

    return fechaFin;
  }
}
/** Ficha operativa de una persona: rol, estado, ausencias y actividad asignada. */
