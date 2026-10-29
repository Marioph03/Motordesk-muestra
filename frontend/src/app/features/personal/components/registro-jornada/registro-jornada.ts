import { ChangeDetectorRef, Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { finalize, timeout } from 'rxjs';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatTableModule } from '@angular/material/table';
import { PersonalService } from '../../services/personal.service';
import { RegistroJornada as RegistroJornadaItem } from '../../models/registro-jornada';
import { NotificationService } from '../../../../shared/services/notification';
import { AuthService } from '../../../../core/auth/auth.service';

@Component({
  selector: 'app-registro-jornada', standalone: true,
  imports: [CommonModule, FormsModule, MatButtonModule, MatCardModule, MatCheckboxModule, MatFormFieldModule, MatIconModule, MatInputModule, MatTableModule],
  templateUrl: './registro-jornada.html', styleUrl: './registro-jornada.scss'
})
export class RegistroJornada implements OnInit {
  private readonly personal = inject(PersonalService);
  private readonly notification = inject(NotificationService);
  private readonly cdr = inject(ChangeDetectorRef);
  readonly auth = inject(AuthService);
  registros: RegistroJornadaItem[] = [];
  cargando = true;
  descargando = false;
  procesando = new Set<number>();
  fecha = new Date().toISOString().slice(0, 10);
  mes = this.fecha.slice(0, 7);
  readonly columnas = ['trabajador', 'horario', 'presente', 'registro'];

  ngOnInit(): void { this.cargar(); }
  get registrosDia(): RegistroJornadaItem[] { return this.registros.filter(registro => registro.fecha === this.fecha); }
  get puedeEditar(): boolean { return this.auth.tienePermiso('personal.editar'); }

  cargar(): void {
    this.cargando = true;
    this.personal.getRegistrosJornada(this.mes).pipe(timeout(12_000), finalize(() => {
      this.cargando = false;
      this.cdr.markForCheck();
      this.cdr.detectChanges();
    })).subscribe({
      next: registros => {
        this.registros = registros;
        this.cdr.markForCheck();
      },
      error: error => this.notification.showHttpError(error)
    });
  }

  cambiarFecha(): void {
    const mes = this.fecha.slice(0, 7);
    if (mes !== this.mes) { this.mes = mes; this.cargar(); }
  }

  cambiarMes(): void {
    this.fecha = `${this.mes}-01`;
    this.cargar();
  }

  marcar(registro: RegistroJornadaItem, presente: boolean): void {
    if (this.procesando.has(registro.usuario_id)) return;
    this.procesando.add(registro.usuario_id);
    this.personal.marcarJornada(registro.usuario_id, registro.fecha, presente).pipe(finalize(() => this.procesando.delete(registro.usuario_id))).subscribe({
      next: actualizado => {
        const indice = this.registros.findIndex(item => item.usuario_id === actualizado.usuario_id && item.fecha === actualizado.fecha);
        if (indice >= 0) this.registros[indice] = actualizado;
        this.registros = [...this.registros];
      },
      error: error => this.notification.showHttpError(error)
    });
  }

  guardarHorario(registro: RegistroJornadaItem): void {
    if (!this.puedeEditar) return;
    this.personal.actualizarHorarioJornada(registro.usuario_id, registro.hora_entrada_predeterminada, registro.hora_salida_predeterminada).subscribe({
      next: () => { this.notification.success('Horario predeterminado actualizado.'); this.cargar(); },
      error: error => this.notification.showHttpError(error)
    });
  }

  descargarPdf(): void {
    if (this.descargando) return;
    this.descargando = true;
    this.personal.descargarRegistroJornada(this.mes).pipe(finalize(() => this.descargando = false)).subscribe({
      next: blob => { const url = URL.createObjectURL(blob); window.open(url, '_blank'); setTimeout(() => URL.revokeObjectURL(url), 10_000); },
      error: error => this.notification.showHttpError(error)
    });
  }
}
