import { Component, Inject, OnInit, inject } from '@angular/core';
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

import { MatButtonModule } from '@angular/material/button';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatCheckboxModule } from '@angular/material/checkbox';

import { Proveedor } from '../../models/proveedor';
import { ProveedorCreate } from '../../models/proveedor-create';
import { ProveedorUpdate } from '../../models/proveedor-update';
import { ProveedoresService } from '../../services/proveedores.service';
import { NotificationService } from '../../../../shared/services/notification';

interface DialogData {
  proveedor?: Proveedor;
}

@Component({
  selector: 'app-proveedor-dialog',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    MatDialogModule,
    MatButtonModule,
    MatFormFieldModule,
    MatInputModule,
    MatCheckboxModule
  ],
  templateUrl: './proveedor-dialog.html',
  styleUrl: './proveedor-dialog.scss'
})
export class ProveedorDialog implements OnInit {

  private fb = inject(FormBuilder);

  private proveedoresService = inject(ProveedoresService);

  private dialogRef = inject(MatDialogRef<ProveedorDialog>);

  private notification = inject(NotificationService);

  isEditMode = false;

  form = this.fb.nonNullable.group({

    nombre: [
      '',
      Validators.required
    ],

    cif: [
      '',
      Validators.required
    ],

    telefono: [''],

    email: ['', Validators.email],

    direccion: [''],

    ciudad: [''],

    provincia: [''],

    codigo_postal: [''],

    observaciones: [''],

    activo: [true]

  });

  constructor(
    @Inject(MAT_DIALOG_DATA)
    public data: DialogData
  ) {}

  ngOnInit(): void {

    this.isEditMode = !!this.data.proveedor;

    if (this.data.proveedor) {

      this.form.setValue({

        nombre: this.data.proveedor.nombre,

        cif: this.data.proveedor.cif,

        telefono: this.data.proveedor.telefono ?? '',

        email: this.data.proveedor.email ?? '',

        direccion: this.data.proveedor.direccion ?? '',

        ciudad: this.data.proveedor.ciudad ?? '',

        provincia: this.data.proveedor.provincia ?? '',

        codigo_postal: this.data.proveedor.codigo_postal ?? '',

        observaciones: this.data.proveedor.observaciones ?? '',

        activo: this.data.proveedor.activo

      });

    }

  }

  guardar(): void {

    if (this.form.invalid) {

      this.form.markAllAsTouched();

      return;

    }

    if (this.isEditMode) {

      const proveedor: ProveedorUpdate = this.form.getRawValue();

      this.proveedoresService
        .updateProveedor(
          this.data.proveedor!.id,
          proveedor
        )
        .subscribe({

          next: () => {
            this.notification.success('Proveedor actualizado correctamente');
            this.dialogRef.close(true);
          },

          error: err => this.notification.showHttpError(err)

        });

    } else {

      const proveedor: ProveedorCreate = this.form.getRawValue();

      this.proveedoresService
        .createProveedor(proveedor)
        .subscribe({

          next: () => {
            this.notification.success('Proveedor creado correctamente');
            this.dialogRef.close(true);
          },

          error: err => this.notification.showHttpError(err)

        });

    }

  }

  cancelar(): void {

    this.dialogRef.close(false);

  }

}
/** Diálogo de alta y edición rápida de proveedores del catálogo. */
