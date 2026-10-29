import { Component, inject, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { Router } from '@angular/router';
import { ClientesService } from '../../services/clientes.service';
import { ActivatedRoute } from '@angular/router';
import { NotificationService } from '../../../../shared/services/notification';

@Component({
  selector: 'app-cliente-form',
  imports: [ReactiveFormsModule,
            MatCardModule,
            MatFormFieldModule,
            MatInputModule,
            MatCheckboxModule,
            MatButtonModule,
            ],
  templateUrl: './cliente-form.html',
  standalone: true,
  styleUrl: './cliente-form.scss',
})
export class ClienteForm implements OnInit{

  form: FormGroup;

  private clientesService = inject(ClientesService);

  private router = inject(Router);

  private route = inject(ActivatedRoute);

  private notification = inject(NotificationService);

  clienteId?: number;

  isEditMode = false;

  saving = false;

  constructor(private fb: FormBuilder) {

    this.form = this.fb.nonNullable.group({

        nombre: ['', Validators.required],

        apellidos: [''],

        dni: ['', Validators.required],

        telefono: [''],

        email: ['', Validators.email],

        direccion: [''],

        ciudad: [''],

        provincia: [''],

        codigo_postal: [''],

        observaciones: [''],

        activo: [true]

    });

}

  guardar(): void {

    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }

    this.saving = true;

    const request = this.isEditMode

      ? this.clientesService.updateCliente(
          this.clienteId!,
          this.form.getRawValue()
        )

      : this.clientesService.createCliente(
          this.form.getRawValue()
        );

    request.subscribe({

      next: () => {

        this.saving = false;

        this.notification.success(

        this.isEditMode
          ? 'Cliente actualizado correctamente'
          : 'Cliente creado correctamente'
      );

      this.router.navigate(['/clientes']);

      },

      error: (err) => {

        this.saving = false;

        this.notification.showHttpError(err);

        console.error(err);

      }

    });

  }

  cancelar(): void {

    this.router.navigate(['/clientes']);

  }

  cargarCliente(): void {

  this.clientesService
    .getCliente(this.clienteId!)
    .subscribe({

      next: cliente => {

        this.form.patchValue(cliente);

      },

      error: err => {

        this.notification.showHttpError(err);

        console.error(err);

      }

    });

  }

  ngOnInit(): void {

  const id = this.route.snapshot.paramMap.get('id');

  if (!id) {
    return;
  }

  this.clienteId = Number(id);

  this.isEditMode = true;

  this.cargarCliente();

  }

}
/** Formulario reactivo de alta y edición de clientes, con validación local. */
