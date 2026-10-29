import { Component, inject } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { MAT_DIALOG_DATA, MatDialogModule, MatDialogRef } from '@angular/material/dialog';
import { MatButtonModule } from '@angular/material/button';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';

@Component({
  selector: 'app-resolver-garantia-dialog',
  standalone: true,
  imports: [ReactiveFormsModule, MatDialogModule, MatButtonModule, MatFormFieldModule, MatInputModule],
  templateUrl: './resolver-garantia-dialog.html',
  styleUrl: './resolver-garantia-dialog.scss'
})
export class ResolverGarantiaDialog {
  private fb = inject(FormBuilder);
  private dialogRef = inject(MatDialogRef<ResolverGarantiaDialog>);
  data = inject(MAT_DIALOG_DATA) as { numero: string };

  form = this.fb.group({
    resolucion: ['', [Validators.required, Validators.maxLength(2000)]]
  });

  confirmar(): void {
    const resolucion = this.form.controls.resolucion.value?.trim();
    if (!resolucion) {
      this.form.controls.resolucion.markAsTouched();
      return;
    }
    this.dialogRef.close(resolucion);
  }
}
/** Diálogo de cierre de garantía que recoge resolución y decisión final. */
