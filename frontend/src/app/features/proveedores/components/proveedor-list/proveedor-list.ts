import {
  Component,
  OnInit,
  ChangeDetectorRef,
  inject
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

import { MatTableModule } from '@angular/material/table';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatDialogModule, MatDialog } from '@angular/material/dialog';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';

import { Proveedor } from '../../models/proveedor';
import { ProveedoresService } from '../../services/proveedores.service';
import { ProveedorDialog } from '../proveedor-dialog/proveedor-dialog';
import { NotificationService } from '../../../../shared/services/notification';

@Component({
  selector: 'app-proveedor-list',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    MatTableModule,
    MatButtonModule,
    MatIconModule,
    MatDialogModule,
    MatFormFieldModule,
    MatInputModule
  ],
  templateUrl: './proveedor-list.html',
  styleUrl: './proveedor-list.scss'
})
export class ProveedorList implements OnInit {

  private proveedoresService = inject(ProveedoresService);

  private dialog = inject(MatDialog);

  private notification = inject(NotificationService);

  proveedores: Proveedor[] = [];

  eliminandoId?: number;

  busqueda = '';

  private cdr = inject(ChangeDetectorRef);

  displayedColumns = [
    'codigo',
    'nombre',
    'cif',
    'telefono',
    'email',
    'activo',
    'acciones'
  ];

  ngOnInit(): void {

    this.cargarProveedores();

  }

  cargarProveedores(): void {

  this.proveedoresService
    .getProveedores()
    .subscribe({

      next: proveedores => {

        this.proveedores = proveedores;

        this.cdr.detectChanges();

      },

      error: err => console.error(err)

    });

  }

  get proveedoresFiltrados(): Proveedor[] {
    const termino = this.normalizar(this.busqueda);
    if (!termino) {
      return this.proveedores;
    }

    return this.proveedores.filter(proveedor =>
      [
        proveedor.codigo,
        proveedor.nombre,
        proveedor.cif,
        proveedor.telefono,
        proveedor.email,
        proveedor.direccion,
        proveedor.ciudad,
        proveedor.provincia,
        proveedor.codigo_postal,
        proveedor.observaciones,
        proveedor.activo ? 'activo' : 'inactivo'
      ].some(valor => this.normalizar(valor).includes(termino))
    );
  }

  limpiarBusqueda(): void {
    this.busqueda = '';
  }

  private normalizar(valor?: string | null): string {
    return (valor ?? '')
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '')
      .toLowerCase();
  }

  nuevoProveedor(): void {

    this.dialog
      .open(ProveedorDialog, {
        width: '860px',
        maxWidth: '96vw'
      })
      .afterClosed()
      .subscribe(result => {

        if (result) {

          this.cargarProveedores();

        }

      });

  }

  editarProveedor(
    proveedor: Proveedor
  ): void {

    this.dialog
      .open(ProveedorDialog, {

        width: '860px',
        maxWidth: '96vw',

        data: {
          proveedor
        }

      })
      .afterClosed()
      .subscribe(result => {

        if (result) {

          this.cargarProveedores();

        }

      });

  }

  eliminarProveedor(
    proveedor: Proveedor
  ): void {

    if (!confirm(`¿Eliminar el proveedor "${proveedor.nombre}"?`)) {

      return;

    }

    this.eliminandoId = proveedor.id;

    this.proveedoresService
      .deleteProveedor(proveedor.id)
      .subscribe({

        next: () => {
          this.eliminandoId = undefined;
          this.notification.success('Proveedor eliminado correctamente');
          this.cargarProveedores();
        },

        error: err => {
          this.eliminandoId = undefined;
          this.notification.showHttpError(err);
          this.cdr.detectChanges();
        }

      });

  }

}
/** Listado de proveedores con acceso a su creación y edición. */
