import {
  Component,
  inject
} from '@angular/core';

import {
  FormBuilder,
  ReactiveFormsModule,
  Validators
} from '@angular/forms';

import {
  MAT_DIALOG_DATA,
  MatDialogModule,
  MatDialogRef
} from '@angular/material/dialog';

import { MatButtonModule } from '@angular/material/button';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';


export interface StockMovimientoDialogData {
  titulo: string;
  requiereMotivo: boolean;
}


@Component({
  selector: 'app-stock-movimiento-dialog',

  standalone: true,

  imports: [
    ReactiveFormsModule,

    MatDialogModule,
    MatButtonModule,
    MatFormFieldModule,
    MatInputModule
  ],

  template: `
    <h2 mat-dialog-title>
      {{ data.titulo }}
    </h2>

    <mat-dialog-content>

      <form
        [formGroup]="form"
        class="dialog-form">

        <mat-form-field appearance="outline">

          <mat-label>
            Cantidad
          </mat-label>

          <input
            matInput
            type="number"
            step="0.01"
            formControlName="cantidad">

        </mat-form-field>

        <mat-form-field
          appearance="outline">

          <mat-label>
            Motivo
          </mat-label>

          <textarea
            matInput
            rows="3"
            formControlName="motivo">
          </textarea>

        </mat-form-field>

      </form>

    </mat-dialog-content>

    <mat-dialog-actions align="end">

      <button
        mat-button
        type="button"
        (click)="cancelar()">

        Cancelar

      </button>

      <button
        mat-flat-button
        color="primary"
        type="button"
        [disabled]="form.invalid"
        (click)="confirmar()">

        Confirmar

      </button>

    </mat-dialog-actions>
  `,

  styles: [`
    .dialog-form {
      display: flex;
      flex-direction: column;
      gap: 12px;
      min-width: 360px;
      padding-top: 8px;
    }
  `]
})
export class StockMovimientoDialog {

  private fb = inject(FormBuilder);

  private dialogRef =
    inject(
      MatDialogRef<StockMovimientoDialog>
    );

  data =
    inject<StockMovimientoDialogData>(
      MAT_DIALOG_DATA
    );


  form = this.fb.group({

    cantidad: [
      1,
      [
        Validators.required,
        Validators.min(0.01)
      ]
    ],

    motivo: [
      '',
      this.data.requiereMotivo
        ? Validators.required
        : []
    ]

  });


  cancelar(): void {

    this.dialogRef.close();

  }


  confirmar(): void {

    if (this.form.invalid) {

      this.form.markAllAsTouched();

      return;

    }

    this.dialogRef.close({

      cantidad:
        this.form.value.cantidad!,

      motivo:
        this.form.value.motivo
        ?.trim()
        || undefined

    });

  }

}
/** Diálogo de ajuste manual que exige dejar trazabilidad del movimiento. */
