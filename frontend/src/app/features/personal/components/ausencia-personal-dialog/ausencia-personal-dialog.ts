import { Component, Inject, inject } from '@angular/core';
import { ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import { MAT_DIALOG_DATA, MatDialogModule, MatDialogRef } from '@angular/material/dialog';
import { MatButtonModule } from '@angular/material/button';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';

import { AusenciaPersonal } from '../../models/ausencia-personal';
import { AusenciaPersonalGuardar } from '../../services/ausencias-personal.service';

export interface AusenciaPersonalDialogData {
  usuarioId: number;
  ausencia?: AusenciaPersonal;
}

@Component({
  selector: 'app-ausencia-personal-dialog',
  standalone: true,
  imports: [
    ReactiveFormsModule,
    MatButtonModule,
    MatDialogModule,
    MatFormFieldModule,
    MatInputModule,
    MatSelectModule
  ],
  template: `
    <h2 mat-dialog-title>{{ data.ausencia ? 'Editar ausencia' : 'Nueva ausencia' }}</h2>
    <mat-dialog-content [formGroup]="form">
      <mat-form-field appearance="outline">
        <mat-label>Tipo</mat-label>
        <mat-select formControlName="tipo">
          <mat-option value="VACACIONES">Vacaciones</mat-option>
          <mat-option value="AUSENCIA">Ausencia</mat-option>
          <mat-option value="OTRO">Otro</mat-option>
        </mat-select>
      </mat-form-field>
      <div class="fechas">
        <mat-form-field appearance="outline">
          <mat-label>Fecha de inicio</mat-label>
          <input matInput type="date" formControlName="fecha_inicio">
        </mat-form-field>
        <mat-form-field appearance="outline">
          <mat-label>Fecha de fin</mat-label>
          <input matInput type="date" formControlName="fecha_fin">
          @if (form.controls.fecha_fin.hasError('anterior')) {
            <mat-error>La fecha final no puede ser anterior a la inicial.</mat-error>
          }
        </mat-form-field>
      </div>
      <mat-form-field appearance="outline" class="ancho-completo">
        <mat-label>Observaciones</mat-label>
        <textarea matInput rows="3" formControlName="observaciones"></textarea>
      </mat-form-field>
    </mat-dialog-content>
    <mat-dialog-actions align="end">
      <button mat-button type="button" (click)="cerrar()">Cancelar</button>
      <button mat-flat-button color="primary" type="button" (click)="guardar()">Guardar</button>
    </mat-dialog-actions>
  `,
  styles: [`
    mat-dialog-content { display: grid; gap: 12px; min-width: min(460px, 80vw); }
    .fechas { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
    .ancho-completo { width: 100%; }
    @media (max-width: 550px) { .fechas { grid-template-columns: 1fr; } }
  `]
})
export class AusenciaPersonalDialog {
  private readonly fb = inject(FormBuilder);
  private readonly dialogRef = inject(MatDialogRef<AusenciaPersonalDialog>);

  readonly form = this.fb.nonNullable.group({
    tipo: ['VACACIONES', Validators.required],
    fecha_inicio: ['', Validators.required],
    fecha_fin: ['', Validators.required],
    observaciones: ['']
  });

  constructor(
    @Inject(MAT_DIALOG_DATA) readonly data: AusenciaPersonalDialogData
  ) {
    if (data.ausencia) {
      this.form.patchValue({
        tipo: data.ausencia.tipo,
        fecha_inicio: this.toInputDate(data.ausencia.fecha_inicio),
        fecha_fin: this.toInputDate(
          data.ausencia.fecha_fin,
          true
        ),
        observaciones: data.ausencia.observaciones ?? ''
      });
    }
  }

  cerrar(): void {
    this.dialogRef.close();
  }

  guardar(): void {
    if (this.form.controls.fecha_fin.hasError('anterior')) {
      this.form.controls.fecha_fin.setErrors(null);
    }

    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }

    const valor = this.form.getRawValue();
    const inicio = `${valor.fecha_inicio}T00:00:00`;
    const fechaFin = new Date(`${valor.fecha_fin}T00:00:00`);

    if (fechaFin < new Date(inicio)) {
      this.form.controls.fecha_fin.setErrors({ anterior: true });
      return;
    }

    // El intervalo final es exclusivo: una ausencia del 24 al 31
    // cubre hasta el 01/09 a las 00:00. Así se incluyen ambos días
    // sin depender del último segundo del día.
    fechaFin.setDate(fechaFin.getDate() + 1);

    const resultado: Required<AusenciaPersonalGuardar> = {
      usuario_id: this.data.usuarioId,
      tipo: valor.tipo,
      fecha_inicio: inicio,
      fecha_fin: this.toLocalDateTime(fechaFin),
      observaciones: valor.observaciones.trim() || null
    };

    this.dialogRef.close(resultado);
  }

  private toInputDate(
    fecha: string,
    finExclusivo = false
  ): string {
    const date = new Date(fecha);

    // Las nuevas ausencias se guardan con el fin exclusivo a las 00:00.
    // Al editar se vuelve a presentar el último día incluido al usuario.
    if (
      finExclusivo
      && date.getHours() === 0
      && date.getMinutes() === 0
      && date.getSeconds() === 0
    ) {
      date.setDate(date.getDate() - 1);
    }

    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');

    return `${year}-${month}-${day}`;
  }

  private toLocalDateTime(fecha: Date): string {
    const year = fecha.getFullYear();
    const month = String(fecha.getMonth() + 1).padStart(2, '0');
    const day = String(fecha.getDate()).padStart(2, '0');

    return `${year}-${month}-${day}T00:00:00`;
  }
}
/** Diálogo de alta o edición de ausencia, validada después también en backend. */
