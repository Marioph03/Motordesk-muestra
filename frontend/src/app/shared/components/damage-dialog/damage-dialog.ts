import { Component, inject } from '@angular/core';

import {
  MAT_DIALOG_DATA,
  MatDialogModule,
  MatDialogRef
} from '@angular/material/dialog';

import { MatRadioButton, MatRadioModule } from '@angular/material/radio';
import { MatButtonModule } from '@angular/material/button';
import { FormsModule } from '@angular/forms';

@Component({
  selector: 'app-damage-dialog',
  standalone: true,
  imports: [
    FormsModule,
    MatDialogModule,
    MatRadioButton,
    MatRadioModule,
    MatButtonModule
  ],
  templateUrl: './damage-dialog.html',
  styleUrl: './damage-dialog.scss'
})
export class DamageDialog {

  readonly dialogRef = inject(MatDialogRef<DamageDialog>);

  readonly data = inject(MAT_DIALOG_DATA);

  selected = '';

  cancelar() {

    this.dialogRef.close();

  }

  guardar() {

    this.dialogRef.close(this.selected);

  }

}
/** Diálogo reutilizable para registrar daños observados en el vehículo. */
