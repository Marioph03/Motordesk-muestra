import {
  ChangeDetectorRef,
  Component,
  OnInit,
  inject
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterLink } from '@angular/router';

import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatTableModule } from '@angular/material/table';
import { MatChipsModule } from '@angular/material/chips';
import { MatTabsModule } from '@angular/material/tabs';

import { Cita } from '../../models/cita';
import { CitasService } from '../../services/citas.service';

import {
  NotificationService
} from '../../../../shared/services/notification';


@Component({
  selector: 'app-cita-list',

  standalone: true,

  imports: [
    CommonModule,
    RouterLink,
    MatTabsModule,
    MatButtonModule,
    MatCardModule,
    MatIconModule,
    MatTableModule,
    MatChipsModule
  ],

  templateUrl: './cita-list.html',

  styleUrl: './cita-list.scss'
})
export class CitaList implements OnInit {

  private citasService =
    inject(CitasService);

  private notification =
    inject(NotificationService);

  private router = inject(Router);

  private readonly changeDetector = inject(ChangeDetectorRef);


  citas: Cita[] = [];

  citasSemana: Cita[] = [];

  inicioSemana = new Date();

  finSemana = new Date();

  diasSemana: Date[] = [];

  // Franja de atención: desde las 07:00 hasta las 20:00.
  // La última celda representa el tramo 19:00–20:00.
  readonly horasAgenda = Array.from({ length: 13 }, (_, indice) => indice + 7);

  // Incluye la marca de cierre (20:00) en la columna de horas.
  readonly horasEtiquetas = Array.from({ length: 14 }, (_, indice) => indice + 7);

  private readonly horaInicioAgenda = 7;

  readonly altoHoraAgenda = 70;

  loading = false;

  displayedColumns = [
    'fecha',
    'hora',
    'motivo',
    'estado',
    'acciones'
  ];


  ngOnInit(): void {
      this.calcularSemanaActual();

      this.cargarCitasSemana();

      this.cargarCitas();

  }


  cargarCitas(): void {

    this.loading = true;

    this.citasService
      .getCitas()
      .subscribe({

        next: citas => {

          this.citas = citas;

          this.loading = false;
          this.actualizarVista();

        },

        error: err => {

          this.loading = false;
          this.actualizarVista();

          this.notification.showHttpError(
            err
          );

        }

      });

  }

  get citasHoy(): Cita[] {
    const hoy = new Date();

    return this.citas
      .filter(cita => {
        const fecha = new Date(cita.fecha_inicio);

        return (
          fecha.getFullYear() === hoy.getFullYear()
          && fecha.getMonth() === hoy.getMonth()
          && fecha.getDate() === hoy.getDate()
          && cita.estado !== 'Cancelada'
          && cita.estado !== 'No presentado'
        );
      })
      .sort(
        (a, b) =>
          new Date(a.fecha_inicio).getTime()
          - new Date(b.fecha_inicio).getTime()
      );
  }

  get citasConfirmadasHoy(): number {
    return this.citasHoy.filter(cita => cita.estado === 'Confirmada').length;
  }

  get citasEnTallerHoy(): number {
    return this.citasHoy.filter(cita => cita.estado === 'En taller').length;
  }

  get proximaCitaHoy(): Cita | undefined {
    const ahora = new Date();

    return this.citasHoy.find(
      cita => new Date(cita.fecha_inicio).getTime() >= ahora.getTime()
    );
  }

  getEstadoColor(
    estado: string
  ): string {

    switch (estado) {

      case 'Pendiente':
        return '#ff9800';

      case 'Confirmada':
        return '#2196f3';

      case 'En taller':
        return '#9c27b0';

      case 'Completada':
        return '#4caf50';

      case 'Cancelada':
        return '#f44336';

      case 'No presentado':
        return '#607d8b';

      default:
        return '#607d8b';
    }

  }

  calcularSemanaActual(): void {

  const hoy = new Date();

  const dia = hoy.getDay();

  const diferenciaLunes =
    dia === 0
      ? -6
      : 1 - dia;

  this.inicioSemana = new Date(hoy);

  this.inicioSemana.setDate(
    hoy.getDate() + diferenciaLunes
  );

  this.inicioSemana.setHours(
    0,
    0,
    0,
    0
  );

  this.finSemana = new Date(
    this.inicioSemana
  );

  this.finSemana.setDate(
    this.inicioSemana.getDate() + 6
  );

  this.finSemana.setHours(
    23,
    59,
    59,
    999
  );

  this.generarDiasSemana();

  }

cargarCitasSemana(): void {

  this.loading = true;

  this.citasService
    .getCitasPorRango(
      this.inicioSemana.toISOString(),
      this.finSemana.toISOString()
    )
    .subscribe({

      next: citas => {

        this.citasSemana = citas;

        this.loading = false;
        this.actualizarVista();

      },

      error: err => {

        this.loading = false;
        this.actualizarVista();

        this.notification.showHttpError(err);

      }

    });

  }

  semanaAnterior(): void {

  this.inicioSemana.setDate(
    this.inicioSemana.getDate() - 7
  );

  this.finSemana.setDate(
    this.finSemana.getDate() - 7
  );

  this.inicioSemana =
    new Date(this.inicioSemana);

  this.finSemana =
    new Date(this.finSemana);

  this.cargarCitasSemana();

  }

  semanaSiguiente(): void {

  this.inicioSemana.setDate(
    this.inicioSemana.getDate() + 7
  );

  this.finSemana.setDate(
    this.finSemana.getDate() + 7
  );

  this.inicioSemana =
    new Date(this.inicioSemana);

  this.finSemana =
    new Date(this.finSemana);

  this.cargarCitasSemana();

  }

  irSemanaActual(): void {

  this.calcularSemanaActual();

  this.cargarCitasSemana();

  }

  generarDiasSemana(): void {

  this.diasSemana = [];

  for (let i = 0; i < 7; i++) {

    const dia = new Date(
      this.inicioSemana
    );

    dia.setDate(
      this.inicioSemana.getDate() + i
    );

    this.diasSemana.push(dia);

  }

  }

  getCitasDia(
  dia: Date
  ): Cita[] {

  return this.citas.filter(
    cita => {

      const fechaCita =
        new Date(
          cita.fecha_inicio
        );

      return (
        fechaCita.getFullYear() ===
          dia.getFullYear()
        &&
        fechaCita.getMonth() ===
          dia.getMonth()
        &&
        fechaCita.getDate() ===
          dia.getDate()
      );

    }
  );

  }

  getCitasDiaOrdenadas(
  dia: Date
  ): Cita[] {

  return this.citasSemana.filter(
    cita => {
      const fechaCita = new Date(cita.fecha_inicio);

      return (
        fechaCita.getFullYear() === dia.getFullYear()
        && fechaCita.getMonth() === dia.getMonth()
        && fechaCita.getDate() === dia.getDate()
      );
    }
  ).sort(
    (a, b) =>
      new Date(
        a.fecha_inicio
      ).getTime()
      -
      new Date(
        b.fecha_inicio
      ).getTime()
  );

  }

  nuevaCitaEnDia(dia: Date): void {
    const fecha = `${dia.getFullYear()}-${String(dia.getMonth() + 1).padStart(2, '0')}-${String(dia.getDate()).padStart(2, '0')}`;

    void this.router.navigate(
      ['/agenda/nueva'],
      { queryParams: { fecha } }
    );
  }

  nuevaCitaEnHora(dia: Date, hora: number): void {
    const fecha = `${dia.getFullYear()}-${String(dia.getMonth() + 1).padStart(2, '0')}-${String(dia.getDate()).padStart(2, '0')}`;
    const horaInicio = `${String(hora).padStart(2, '0')}:00`;

    void this.router.navigate(
      ['/agenda/nueva'],
      { queryParams: { fecha, horaInicio } }
    );
  }

  getTopCita(cita: Cita): number {
    const inicio = new Date(cita.fecha_inicio);
    const minutosDesdeInicio = (
      (inicio.getHours() - this.horaInicioAgenda) * 60
      + inicio.getMinutes()
    );
    return Math.max(0, (minutosDesdeInicio / 60) * this.altoHoraAgenda);
  }

  getAlturaCita(cita: Cita): number {
    return 52;
  }

  private actualizarVista(): void {
    this.changeDetector.markForCheck();
    this.changeDetector.detectChanges();
  }

}
/** Agenda operativa: visualiza citas y permite transiciones autorizadas de estado. */
