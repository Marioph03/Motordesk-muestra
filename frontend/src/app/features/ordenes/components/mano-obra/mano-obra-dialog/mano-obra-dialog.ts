import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
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

import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { MatCheckboxModule } from '@angular/material/checkbox';

import { ManoObraService } from '../../../services/mano-obra.service';
import { ManoObraCreate } from '../../../models/mano-obra-create';
import {
  MatDialogActions,
  MatDialogContent,
  MatDialogTitle,
} from '@angular/material/dialog';

@Component({
  selector: 'app-mano-obra-dialog',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    MatDialogModule,
    MatFormFieldModule,
    MatInputModule,
    MatButtonModule, MatCheckboxModule,
    MatDialogContent,
    MatDialogActions,
    MatDialogTitle
  ],
  templateUrl: './mano-obra-dialog.html',
  styleUrl: './mano-obra-dialog.scss'
})
export class ManoObraDialog {

  private fb = inject(FormBuilder);

  private manoObraService = inject(ManoObraService);

  readonly data = inject(MAT_DIALOG_DATA);

  private dialogRef = inject(MatDialogRef<ManoObraDialog>);

  isEditMode = !!this.data.linea;

  constructor() {

  if (this.isEditMode) {

    this.form.patchValue({

  concepto: this.data.linea.concepto,
  codigo_mano_obra: this.data.linea.codigo_mano_obra ?? '',
  horas: this.data.linea.horas,
  precio_hora: this.data.linea.precio_hora,
  descuento_porcentaje: this.data.linea.descuento_porcentaje
  ,cubierto_garantia: this.data.linea.cubierto_garantia ?? false

  });

  }

  }

  form = this.fb.nonNullable.group({
  concepto: ['', Validators.required],
  codigo_mano_obra: [''],
  horas: [1, [Validators.required, Validators.min(0.01)]],
  precio_hora: [0, [Validators.required, Validators.min(0)]],
  descuento_porcentaje: [
    0,
    [
      Validators.min(0),
      Validators.max(100)
    ]
  ],
  cubierto_garantia: [false]
});

  get importeSinIva(): number {
    const horas = Number(this.form.value.horas ?? 0);
    const precioHora = Number(this.form.value.precio_hora ?? 0);
    const descuento = Number(
      this.form.value.descuento_porcentaje ?? 0
    );

    return horas * precioHora * (1 - descuento / 100);
  }

  guardar(): void {

  if (this.form.invalid) {

    this.form.markAllAsTouched();

    return;

  }

  const datos = this.form.getRawValue();

  const peticion = this.isEditMode

    ? this.manoObraService.update(
        this.data.ordenId,
        this.data.linea.id,
        datos
      )

    : this.manoObraService.create(
        this.data.ordenId,
        datos
      );

  peticion.subscribe({

    next: linea => this.dialogRef.close(linea),

    error: err => console.error(err)

  });

}

  cancelar(): void {

  this.dialogRef.close();

  }

}
/** Diálogo de edición de trabajo de mano de obra dentro de una orden. */
