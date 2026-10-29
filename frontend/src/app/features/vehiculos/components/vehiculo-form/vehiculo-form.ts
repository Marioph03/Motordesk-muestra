import { Component, inject, OnInit } from '@angular/core';
import { ClientesService } from '../../../clientes/services/clientes.service';
import { Validators } from '@angular/forms';
import { Cliente } from '../../../clientes/models/cliente';

import {
  FormBuilder,
  FormGroup,
  ReactiveFormsModule,
} from '@angular/forms';
import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { MatSelectModule } from '@angular/material/select';
import { NotificationService } from '../../../../shared/services/notification';
import { ActivatedRoute, Router } from '@angular/router';
import { Vehiculos } from '../../services/vehiculos';
import { AutocompleteSelect } from '../../../../shared/components/autocomplete-select/autocomplete-select';

@Component({
  selector: 'app-vehiculo-form',
  imports: [ReactiveFormsModule,
            MatCardModule,
            MatFormFieldModule,
            MatInputModule,
            MatButtonModule,
            MatSelectModule,
            AutocompleteSelect],
  templateUrl: './vehiculo-form.html',
  styleUrl: './vehiculo-form.scss',
})
export class VehiculoForm implements OnInit{

  private clientesService = inject(ClientesService);

  private fb = inject(FormBuilder);

  clientes: Cliente[] = [];

  etiquetaCliente = (cliente: Cliente): string => {
    // El endpoint de selección puede devolver clientes antiguos sin
    // apellidos o documento. Nunca mostramos "undefined" al usuario.
    const nombreCompleto = [
      cliente.apellidos,
      cliente.nombre,
    ]
      .filter(parte => Boolean(parte?.trim()))
      .join(', ')
      .trim();

    const documento = cliente.dni?.trim();

    return documento
      ? `${nombreCompleto || 'Cliente'} · ${documento}`
      : nombreCompleto || 'Cliente';
  };

  form: FormGroup;

  isEditMode = false;

  /** Modo de consulta: permite revisar datos sin exponer ninguna escritura. */
  isViewMode = false;

  private notification = inject(NotificationService);

  saving = false;

  vehiculoId?: number;

  private router = inject(Router);

  private route = inject(ActivatedRoute);

  private vehiculosService = inject(Vehiculos);

  constructor() {

    this.form = this.fb.nonNullable.group({

      cliente_id: [0, [Validators.required, Validators.min(1)]],

      matricula: ['', Validators.required],

      bastidor: [''],

      marca: ['', Validators.required],

      modelo: ['', Validators.required],

      version: [''],

      fecha_matriculacion: [''],

      color: [''],

      combustible: [''],

      transmision: [''],

      observaciones: ['']

    });
  }

  cargarClientes(): void {

  this.clientesService
  .getClientesSelect()
  .subscribe(clientes => {
    this.clientes = clientes;
  });
}

ngOnInit(): void {

  this.cargarClientes();

  const id = this.route.snapshot.paramMap.get('id');

  if (!id) {
    return;
  }

  this.vehiculoId = Number(id);

  this.isViewMode = this.route.snapshot.data['soloLectura'] === true;

  this.isEditMode = !this.isViewMode;

  this.cargarVehiculo();

}

guardar(): void {

  // Defensa adicional al formulario deshabilitado: la vista nunca debe poder
  // provocar una escritura aunque se invoque el método desde la consola.
  if (this.isViewMode) {
    return;
  }

  if (this.form.invalid) {

    this.form.markAllAsTouched();

    return;

  }

  this.saving = true;

  const request = this.isEditMode

    ? this.vehiculosService.updateVehiculo(
        this.vehiculoId!,
        this.form.getRawValue()
      )

    : this.vehiculosService.createVehiculo(
        this.form.getRawValue()
      );

  request.subscribe({

    next: () => {

      this.saving = false;

      this.notification.success(

        this.isEditMode

          ? 'Vehículo actualizado correctamente'

          : 'Vehículo creado correctamente'

      );

      this.router.navigate(['/vehiculos']);

    },

    error: err => {

      this.saving = false;

      this.notification.showHttpError(err);

    }
  });
}

cancelar(): void {

  this.router.navigate(['/vehiculos']);

}

cargarVehiculo(): void {

  this.vehiculosService
      .getVehiculo(this.vehiculoId!)
      .subscribe({

        next: vehiculo => {

          this.form.patchValue(vehiculo);

          if (this.isViewMode) {
            this.form.disable({ emitEvent: false });
          }

        },

        error: err => {

          console.error(err);

        }

      });

}

}
/** Formulario de vehículo asociado a un cliente, con validaciones de identificación. */
