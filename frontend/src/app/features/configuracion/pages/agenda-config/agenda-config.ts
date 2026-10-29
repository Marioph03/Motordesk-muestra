import { ChangeDetectorRef, Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSlideToggleModule } from '@angular/material/slide-toggle';
import { MatTableModule } from '@angular/material/table';

import { CierreAgenda, ConfiguracionAgenda } from '../../models/configuracion-agenda';
import { ConfiguracionAgendaService } from '../../services/configuracion-agenda.service';
import { NotificationService } from '../../../../shared/services/notification';

type DiaActivoControl =
  | 'lunes_activo' | 'martes_activo' | 'miercoles_activo' | 'jueves_activo'
  | 'viernes_activo' | 'sabado_activo' | 'domingo_activo';
type HoraControl =
  | 'lunes_inicio' | 'lunes_fin' | 'martes_inicio' | 'martes_fin'
  | 'miercoles_inicio' | 'miercoles_fin' | 'jueves_inicio' | 'jueves_fin'
  | 'viernes_inicio' | 'viernes_fin' | 'sabado_inicio' | 'sabado_fin'
  | 'domingo_inicio' | 'domingo_fin';
type DiaAgenda = { nombre: string; activo: DiaActivoControl; inicio: HoraControl; fin: HoraControl };

@Component({
  selector: 'app-agenda-config',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, MatButtonModule, MatCardModule, MatFormFieldModule, MatIconModule, MatInputModule, MatProgressSpinnerModule, MatSlideToggleModule, MatTableModule],
  templateUrl: './agenda-config.html',
  styleUrl: './agenda-config.scss'
})
export class AgendaConfig implements OnInit {
  private readonly fb = inject(FormBuilder);
  private readonly configService = inject(ConfiguracionAgendaService);
  private readonly notification = inject(NotificationService);
  private readonly changeDetector = inject(ChangeDetectorRef);

  cargando = false;
  guardando = false;
  cierres: CierreAgenda[] = [];
  readonly displayedColumns = ['fecha', 'motivo', 'observaciones', 'acciones'];
  readonly dias: DiaAgenda[] = [
    { nombre: 'Lunes', activo: 'lunes_activo', inicio: 'lunes_inicio', fin: 'lunes_fin' },
    { nombre: 'Martes', activo: 'martes_activo', inicio: 'martes_inicio', fin: 'martes_fin' },
    { nombre: 'Miércoles', activo: 'miercoles_activo', inicio: 'miercoles_inicio', fin: 'miercoles_fin' },
    { nombre: 'Jueves', activo: 'jueves_activo', inicio: 'jueves_inicio', fin: 'jueves_fin' },
    { nombre: 'Viernes', activo: 'viernes_activo', inicio: 'viernes_inicio', fin: 'viernes_fin' },
    { nombre: 'Sábado', activo: 'sabado_activo', inicio: 'sabado_inicio', fin: 'sabado_fin' },
    { nombre: 'Domingo', activo: 'domingo_activo', inicio: 'domingo_inicio', fin: 'domingo_fin' }
  ];

  readonly form = this.fb.group({
    duracion_cita_minutos: [30, [Validators.required, Validators.min(5), Validators.max(480)]],
    lunes_activo: [true], lunes_inicio: ['08:00'], lunes_fin: ['18:00'],
    martes_activo: [true], martes_inicio: ['08:00'], martes_fin: ['18:00'],
    miercoles_activo: [true], miercoles_inicio: ['08:00'], miercoles_fin: ['18:00'],
    jueves_activo: [true], jueves_inicio: ['08:00'], jueves_fin: ['18:00'],
    viernes_activo: [true], viernes_inicio: ['08:00'], viernes_fin: ['18:00'],
    sabado_activo: [false], sabado_inicio: ['09:00'], sabado_fin: ['14:00'],
    domingo_activo: [false], domingo_inicio: ['09:00'], domingo_fin: ['14:00']
  });

  readonly cierreForm = this.fb.group({
    fecha: ['', Validators.required],
    motivo: ['', Validators.required],
    observaciones: ['']
  });

  ngOnInit(): void {
    this.cargarConfiguracion();
    this.cargarCierres();
  }

  cargarConfiguracion(): void {
    this.cargando = true;
    this.actualizarVista();
    this.configService.getConfiguracion().subscribe({
      next: configuracion => {
        this.form.patchValue(configuracion);
        this.cargando = false;
        this.actualizarVista();
      },
      error: error => {
        this.cargando = false;
        this.notification.showHttpError(error);
        this.actualizarVista();
      }
    });
  }

  cargarCierres(): void {
    this.configService.getCierres().subscribe({
      next: cierres => { this.cierres = cierres; this.actualizarVista(); },
      error: error => this.notification.showHttpError(error)
    });
  }

  guardar(): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }
    this.guardando = true;
    this.configService.actualizar(this.form.getRawValue() as Omit<ConfiguracionAgenda, 'id'>).subscribe({
      next: configuracion => {
        this.form.patchValue(configuracion);
        this.guardando = false;
        this.notification.success('Configuración de agenda guardada.');
        this.actualizarVista();
      },
      error: error => {
        this.guardando = false;
        this.notification.showHttpError(error);
        this.actualizarVista();
      }
    });
  }

  crearCierre(): void {
    if (this.cierreForm.invalid) {
      this.cierreForm.markAllAsTouched();
      return;
    }
    const valor = this.cierreForm.getRawValue();
    this.configService.crearCierre({ fecha: valor.fecha!, motivo: valor.motivo!, observaciones: valor.observaciones?.trim() || null }).subscribe({
      next: cierre => {
        this.cierres = [...this.cierres, cierre].sort((a, b) => a.fecha.localeCompare(b.fecha));
        this.cierreForm.reset({ fecha: '', motivo: '', observaciones: '' });
        this.notification.success('Cierre añadido.');
        this.actualizarVista();
      },
      error: error => this.notification.showHttpError(error)
    });
  }

  eliminarCierre(cierre: CierreAgenda): void {
    if (!window.confirm(`¿Eliminar el cierre del ${this.formatearFecha(cierre.fecha)}?`)) {
      return;
    }
    this.configService.eliminarCierre(cierre.id).subscribe({
      next: () => {
        this.cierres = this.cierres.filter(item => item.id !== cierre.id);
        this.notification.success('Cierre eliminado.');
        this.actualizarVista();
      },
      error: error => this.notification.showHttpError(error)
    });
  }

  formatearFecha(fecha: string): string {
    const [anio, mes, dia] = fecha.slice(0, 10).split('-');
    return `${dia}/${mes}/${anio}`;
  }

  private actualizarVista(): void {
    this.changeDetector.markForCheck();
    this.changeDetector.detectChanges();
  }
}
/** Editor de horarios y cierres que el backend aplica al validar citas. */
