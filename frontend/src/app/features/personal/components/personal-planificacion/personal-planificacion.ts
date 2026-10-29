import { CommonModule } from '@angular/common';
import { ChangeDetectorRef, Component, OnInit, inject } from '@angular/core';
import { finalize, timeout } from 'rxjs';

import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';

import { UsuarioPlanificacion } from '../../models/planificacion-personal';
import { PersonalService } from '../../services/personal.service';
import { NotificationService } from '../../../../shared/services/notification';


@Component({
  selector: 'app-personal-planificacion',
  standalone: true,
  imports: [
    CommonModule,
    MatButtonModule,
    MatCardModule,
    MatIconModule,
  ],
  templateUrl: './personal-planificacion.html',
  styleUrl: './personal-planificacion.scss',
})
export class PersonalPlanificacion implements OnInit {
  private readonly personalService = inject(PersonalService);
  private readonly notification = inject(NotificationService);
  private readonly cdr = inject(ChangeDetectorRef);

  inicioSemana = this.obtenerInicioSemana(new Date());
  diasSemana: Date[] = [];
  planificacion: UsuarioPlanificacion[] = [];
  cargando = false;

  ngOnInit(): void {
    this.actualizarDiasSemana();
    this.cargarPlanificacion();
  }

  get finSemana(): Date {
    const fin = new Date(this.inicioSemana);
    fin.setDate(fin.getDate() + 7);
    return fin;
  }

  get finSemanaVisible(): Date {
    return new Date(this.finSemana.getTime() - 1);
  }

  semanaAnterior(): void {
    this.inicioSemana.setDate(this.inicioSemana.getDate() - 7);
    this.inicioSemana = new Date(this.inicioSemana);
    this.actualizarDiasSemana();
    this.cargarPlanificacion();
  }

  semanaSiguiente(): void {
    this.inicioSemana.setDate(this.inicioSemana.getDate() + 7);
    this.inicioSemana = new Date(this.inicioSemana);
    this.actualizarDiasSemana();
    this.cargarPlanificacion();
  }

  irSemanaActual(): void {
    this.inicioSemana = this.obtenerInicioSemana(new Date());
    this.actualizarDiasSemana();
    this.cargarPlanificacion();
  }

  getBloquesDia(
    usuario: UsuarioPlanificacion,
    dia: Date
  ) {
    const inicioDia = new Date(dia);
    const finDia = new Date(dia);
    finDia.setDate(finDia.getDate() + 1);

    return usuario.bloques.filter(bloque =>
      new Date(bloque.inicio) < finDia
      && new Date(bloque.fin) > inicioDia
    );
  }

  claseBloque(tipo: string): string {
    return `bloque-${tipo.toLowerCase()}`;
  }

  iconoBloque(tipo: string): string {
    if (tipo === 'CITA') return 'event';
    if (tipo === 'VACACIONES') return 'beach_access';
    if (tipo === 'AUSENCIA') return 'person_off';
    return 'event_busy';
  }

  private cargarPlanificacion(): void {
    this.cargando = true;

    this.personalService.getPlanificacion(
      this.inicioSemana.toISOString(),
      this.finSemana.toISOString()
    ).pipe(
      timeout(8_000),
      finalize(() => {
        this.cargando = false;
        this.cdr.markForCheck();
      })
    ).subscribe({
      next: planificacion => {
        this.planificacion = planificacion;
      },
      error: error => {
        this.notification.showHttpError(error);
      }
    });
  }

  private actualizarDiasSemana(): void {
    this.diasSemana = Array.from({ length: 7 }, (_, indice) => {
      const dia = new Date(this.inicioSemana);
      dia.setDate(dia.getDate() + indice);
      return dia;
    });
  }

  private obtenerInicioSemana(fecha: Date): Date {
    const inicio = new Date(fecha);
    const dia = inicio.getDay();
    inicio.setDate(inicio.getDate() + (dia === 0 ? -6 : 1 - dia));
    inicio.setHours(0, 0, 0, 0);
    return inicio;
  }
}
/** Calendario de planificación que cruza citas, órdenes y ausencias por persona. */
