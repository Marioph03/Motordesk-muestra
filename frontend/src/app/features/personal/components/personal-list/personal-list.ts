import { AusenciaPersonal } from '../../models/ausencia-personal';
import {
  ChangeDetectorRef,
  Component,
  OnInit,
  inject
} from '@angular/core';
import { timeout } from 'rxjs';
import { RouterLink } from '@angular/router';
import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';
import { MatChipsModule } from '@angular/material/chips';
import { MatIconModule } from '@angular/material/icon';
import { MatTableModule } from '@angular/material/table';

import { NotificationService } from '../../../../shared/services/notification';
import { Personal } from '../../models/personal';
import { PersonalService } from '../../services/personal.service';
import { AuthService } from '../../../../core/auth/auth.service';

@Component({
  selector: 'app-personal-list',
  standalone: true,
  imports: [RouterLink, MatButtonModule, MatCardModule, MatChipsModule, MatIconModule, MatTableModule],
  templateUrl: './personal-list.html',
  styleUrl: './personal-list.scss'
})
export class PersonalList implements OnInit {
  private readonly personalService = inject(PersonalService);
  private readonly notification = inject(NotificationService);
  private readonly cdr = inject(ChangeDetectorRef);
  readonly authService = inject(AuthService);

  readonly displayedColumns = [
    'nombre',
    'rol',
    'estado',
    'disponibilidad',
    'acciones'
  ];
  personal: Personal[] = [];
  ausencias: AusenciaPersonal[] = [];
  cargando = true;

  ngOnInit(): void {
    this.personalService.getPersonal().pipe(
      timeout(8_000)
    ).subscribe({
      next: personal => {
        this.personal = personal;
        this.cargando = false;
        this.cdr.markForCheck();
        this.cargarAusencias();
      },
      error: error => {
        this.cargando = false;
        this.cdr.markForCheck();
        this.notification.showHttpError(error);
      }
    });
  }

  estaAusenteHoy(
  usuarioId: number
): boolean {

  const ahora = new Date();

  return this.ausencias.some(
    ausencia => {

      if (
        ausencia.usuario_id !== usuarioId
      ) {
        return false;
      }

      const inicio =
        new Date(
          ausencia.fecha_inicio
        );

      const fin =
        new Date(
          ausencia.fecha_fin
        );

      return (
        ahora >= inicio
        &&
        ahora < fin
      );

    }
  );
  }

  getAusenciaActual(
  usuarioId: number
): AusenciaPersonal | undefined {

  const ahora = new Date();

  return this.ausencias.find(
    ausencia =>
      ausencia.usuario_id === usuarioId
      &&
      ahora >= new Date(
        ausencia.fecha_inicio
      )
      &&
      ahora < new Date(
        ausencia.fecha_fin
      )
  );

  }

  private cargarAusencias(): void {
    this.personalService.getAusencias().pipe(
      timeout(8_000)
    ).subscribe({
      next: ausencias => {
        this.ausencias = ausencias;
        this.cdr.markForCheck();
      },
      error: error => {
        this.cdr.markForCheck();
        this.notification.showHttpError(error);
      }
    });
  }
}
/** Listado del equipo con estado, rol y disponibilidad actual. */
