import { Component, inject } from '@angular/core';

import {
  MAT_DIALOG_DATA,
  MatDialogModule,
  MatDialogRef
} from '@angular/material/dialog';

import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';


export interface ConfirmDeleteFileData {
  nombre: string;
}


@Component({
  selector: 'app-confirm-delete-file-dialog',
  standalone: true,

  imports: [
    MatDialogModule,
    MatButtonModule,
    MatIconModule
  ],

  template: `
    <h2 mat-dialog-title>
      Eliminar archivo
    </h2>

    <mat-dialog-content>

      <p>
        ¿Seguro que quieres eliminar
        <strong>{{ data.nombre }}</strong>?
      </p>

      <p>
        Esta acción no se puede deshacer.
      </p>

    </mat-dialog-content>

    <mat-dialog-actions align="end">

      <button
        mat-button
        type="button"
        (click)="cancelar()"
      >
        Cancelar
      </button>

      <button
        mat-flat-button
        type="button"
        (click)="confirmar()"
      >
        <mat-icon>delete</mat-icon>
        Eliminar
      </button>

    </mat-dialog-actions>
  `
})
export class ConfirmDeleteFileDialogComponent {

  readonly data =
    inject<ConfirmDeleteFileData>(MAT_DIALOG_DATA);

  private dialogRef =
    inject(MatDialogRef<ConfirmDeleteFileDialogComponent>);


  cancelar(): void {

    this.dialogRef.close(false);

  }


  confirmar(): void {

    this.dialogRef.close(true);

  }

}
/** Confirmación explícita antes de eliminar un adjunto de una orden. */
