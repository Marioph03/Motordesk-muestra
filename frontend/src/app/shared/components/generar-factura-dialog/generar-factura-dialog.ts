import { Component, inject, OnInit } from '@angular/core';

import {
  MAT_DIALOG_DATA,
  MatDialogModule,
  MatDialogRef
} from '@angular/material/dialog';

import { FormsModule } from '@angular/forms';

import { MatRadioModule } from '@angular/material/radio';
import { MatButtonModule } from '@angular/material/button';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatSelectModule } from '@angular/material/select';

import { Cliente } from '../../../features/clientes/models/cliente';
import { ClientesService } from '../../../features/clientes/services/clientes.service';

export interface GenerarFacturaResultado {
  tipoDocumento: string;
  clienteId: number;
}

@Component({
  selector: 'app-generar-factura-dialog',
  standalone: true,
  imports: [
    FormsModule,
    MatRadioModule,
    MatButtonModule,
    MatDialogModule,
    MatFormFieldModule,
    MatSelectModule
  ],
  templateUrl: './generar-factura-dialog.html',
  styleUrl: './generar-factura-dialog.scss'
})
export class GenerarFacturaDialog implements OnInit {

  readonly dialogRef = inject(
    MatDialogRef<GenerarFacturaDialog>
  );

  readonly data = inject(MAT_DIALOG_DATA);

  private clientesService = inject(ClientesService);

  tipoDocumento = 'FACTURA';

  clienteId: number | null = null;

  clientes: Cliente[] = [];

  cargandoClientes = true;

  errorClientes = '';

  ngOnInit(): void {

    this.clientesService.getClientesSelect().subscribe({
      next: clientes => {
        this.clientes = clientes;
        this.cargandoClientes = false;
      },
      error: () => {
        this.errorClientes = 'No se han podido cargar los destinatarios.';
        this.cargandoClientes = false;
      }
    });

  }

  nombreCliente(cliente: Cliente): string {

    return [cliente.apellidos, cliente.nombre]
      .filter(Boolean)
      .join(', ');

  }

  cancelar(): void {

    this.dialogRef.close();

  }

  crear(): void {

    if (!this.clienteId) {
      return;
    }

    this.dialogRef.close(
      {
        tipoDocumento: this.tipoDocumento,
        clienteId: this.clienteId
      } satisfies GenerarFacturaResultado
    );

  }

}
/** Diálogo que confirma los datos antes de generar un borrador de factura. */
