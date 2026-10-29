import { KeyValuePipe } from '@angular/common';
import { ChangeDetectorRef, Component, OnInit, inject } from '@angular/core';
import { finalize, timeout } from 'rxjs';
import { ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { MatDividerModule } from '@angular/material/divider';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';

import { AuthService } from '../../../../core/auth/auth.service';
import { NotificationService } from '../../../../shared/services/notification';
import { Permiso } from '../../models/permiso';
import { Rol } from '../../models/rol';
import { PermisosService } from '../../services/permisos.service';

@Component({
  selector: 'app-rol-form',
  standalone: true,
  imports: [
    ReactiveFormsModule,
    KeyValuePipe,
    RouterLink,
    MatButtonModule,
    MatCardModule,
    MatCheckboxModule,
    MatDividerModule,
    MatFormFieldModule,
    MatIconModule,
    MatInputModule
  ],
  templateUrl: './rol-form.html',
  styleUrl: './rol-form.scss'
})
export class RolForm implements OnInit {
  private readonly fb = inject(FormBuilder);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly permisosService = inject(PermisosService);
  private readonly notification = inject(NotificationService);
  private readonly cdr = inject(ChangeDetectorRef);
  readonly authService = inject(AuthService);

  readonly form = this.fb.nonNullable.group({
    nombre: ['', [Validators.required, Validators.maxLength(50)]],
    descripcion: [''],
    activo: [true]
  });

  permisos: Permiso[] = [];
  permisosSeleccionados = new Set<number>();
  rol?: Rol;
  rolId?: number;
  cargando = true;
  guardando = false;

  get isEditMode(): boolean {
    return this.rolId !== undefined;
  }

  get permisosPorModulo(): Record<string, Permiso[]> {
    const grupos: Record<string, Permiso[]> = {};

    for (const permiso of this.permisos) {
      if (!grupos[permiso.modulo]) {
        grupos[permiso.modulo] = [];
      }

      grupos[permiso.modulo].push(permiso);
    }

    return grupos;
  }

  ngOnInit(): void {
    const id = this.route.snapshot.paramMap.get('id');
    this.rolId = id ? Number(id) : undefined;

    this.permisosService.getPermisos().pipe(
      timeout(8_000),
      finalize(() => {
        if (!this.isEditMode) this.cargando = false;
        this.cdr.markForCheck();
        this.cdr.detectChanges();
      })
    ).subscribe({
      next: permisos => {
        this.permisos = permisos;
        this.cargarRolSiProcede();
      },
      error: err => {
        this.cargando = false;
        this.notification.showHttpError(err);
      }
    });
  }

  tienePermiso(permisoId: number): boolean {
    return this.permisosSeleccionados.has(permisoId);
  }

  togglePermiso(permisoId: number): void {
    if (!this.puedeGestionar || this.esAdmin) {
      return;
    }

    if (this.permisosSeleccionados.has(permisoId)) {
      this.permisosSeleccionados.delete(permisoId);
    } else {
      this.permisosSeleccionados.add(permisoId);
    }
  }

  get esAdmin(): boolean {
    return this.rol?.nombre === 'ADMIN';
  }

  get puedeGestionar(): boolean {
    return this.authService.tienePermiso('permisos.gestionar');
  }

  guardar(): void {
    if (!this.puedeGestionar || this.form.invalid || this.guardando) {
      return;
    }

    this.guardando = true;
    const valor = this.form.getRawValue();
    const datos = {
      nombre: valor.nombre.trim().toUpperCase(),
      descripcion: valor.descripcion.trim() || null,
      activo: valor.activo,
      permisos_ids: Array.from(this.permisosSeleccionados)
    };

    const solicitud = this.isEditMode
      ? this.permisosService.actualizarRol(this.rolId!, datos)
      : this.permisosService.crearRol(datos);

    solicitud.pipe(finalize(() => this.guardando = false)).subscribe({
      next: rol => {
        this.notification.success('Rol guardado correctamente.');
        void this.router.navigate(['/personal/roles', rol.id]);
      },
      error: err => {
        this.notification.showHttpError(err);
      }
    });
  }

  private cargarRolSiProcede(): void {
    if (!this.isEditMode) {
      this.cargando = false;
      return;
    }

    this.permisosService.getRol(this.rolId!).pipe(
      timeout(8_000),
      finalize(() => {
        this.cargando = false;
        this.cdr.markForCheck();
      })
    ).subscribe({
      next: rol => {
        this.rol = rol;
        this.form.setValue({
          nombre: rol.nombre,
          descripcion: rol.descripcion ?? '',
          activo: rol.activo
        });
        this.permisosSeleccionados = new Set(
          rol.permisos.map(permiso => permiso.id)
        );
      },
      error: err => {
        this.notification.showHttpError(err);
      }
    });
  }
}
/** Formulario de rol que agrupa permisos por módulo y protege el rol ADMIN. */
