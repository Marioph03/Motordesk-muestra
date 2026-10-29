import { ChangeDetectorRef, Component, OnInit, inject } from '@angular/core';
import { finalize, timeout } from 'rxjs';
import { RouterLink } from '@angular/router';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatChipsModule } from '@angular/material/chips';
import { MatIconModule } from '@angular/material/icon';
import { MatTableModule } from '@angular/material/table';

import { AuthService } from '../../../../core/auth/auth.service';
import { NotificationService } from '../../../../shared/services/notification';
import { Rol } from '../../models/rol';
import { PermisosService } from '../../services/permisos.service';

@Component({
  selector: 'app-rol-list',
  standalone: true,
  imports: [
    RouterLink,
    MatButtonModule,
    MatCardModule,
    MatChipsModule,
    MatIconModule,
    MatTableModule
  ],
  templateUrl: './rol-list.html',
  styleUrl: './rol-list.scss'
})
export class RolList implements OnInit {
  private readonly permisosService = inject(PermisosService);
  private readonly notification = inject(NotificationService);
  private readonly cdr = inject(ChangeDetectorRef);
  readonly authService = inject(AuthService);

  readonly displayedColumns = [
    'nombre',
    'descripcion',
    'permisos',
    'estado',
    'acciones'
  ];

  roles: Rol[] = [];
  cargando = true;

  ngOnInit(): void {
    this.permisosService.getRoles().pipe(
      timeout(8_000),
      finalize(() => {
        this.cargando = false;
        this.cdr.markForCheck();
      })
    ).subscribe({
      next: roles => {
        this.roles = roles;
      },
      error: err => {
        this.notification.showHttpError(err);
      }
    });
  }
}
/** Administración de roles visibles para usuarios con permiso de gestión. */
