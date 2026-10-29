import { Component, OnInit, inject, ChangeDetectorRef } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { PageEvent } from '@angular/material/paginator';

import { DatePipe, DecimalPipe } from '@angular/common';

import { MatTableDataSource, MatTableModule } from '@angular/material/table';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatPaginatorModule } from '@angular/material/paginator';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatDialog } from '@angular/material/dialog';
import { MatChipsModule } from '@angular/material/chips';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatSelectModule } from '@angular/material/select';
import { MatCheckboxModule } from '@angular/material/checkbox';

import { OrdenesService } from '../../services/ordenes.service';

import { Orden } from '../../models/orden';
import { OrdenPage } from '../../models/orden-page';

import { NotificationService } from '../../../../shared/services/notification';
import { ConfirmDialog } from '../../../../shared/components/confirm-dialog/confirm-dialog';
import { GenerarFacturaDialog } from '../../../../shared/components/generar-factura-dialog/generar-factura-dialog';
import { FacturasService } from '../../../facturas/services/facturas.service';

@Component({
  selector: 'app-ordenes-list',
  standalone: true,
  imports: [
    FormsModule,
    MatTableModule,
    MatButtonModule,
    MatIconModule,
    MatInputModule,
    MatFormFieldModule,
    MatPaginatorModule,
    MatProgressSpinnerModule,
    DecimalPipe,
    RouterLink,
    DatePipe,
    MatChipsModule,
    MatTooltipModule,
    MatSelectModule
    ,MatCheckboxModule
  ],
  templateUrl: './orden-list.html',
  styleUrl: './orden-list.scss'
})
export class OrdenList implements OnInit {

  private ordenesService = inject(OrdenesService);

  private router = inject(Router);

  private notification = inject(NotificationService);

  private dialog = inject(MatDialog);

  private cdr = inject(ChangeDetectorRef);

  private facturasService = inject(FacturasService);

  dataSource = new MatTableDataSource<Orden>();

  ordenes?: OrdenPage;

  displayedColumns = [
    'seleccion',
    'tipo',
    'numero',
    'vehiculo',
    'fechaEntrada',
    'estado',
    'importe',
    'acciones'
  ];

  busqueda = '';

  page = 1;

  size = 10;

  loading = false;
  ordenesSeleccionadas = new Set<number>();

  tipoSeleccionado: 'TODOS' | 'OR' | 'PR' = 'TODOS';

  estadoSeleccionado = '';

  get esPresupuestos(): boolean {
    return this.tipoSeleccionado === 'PR';
  }
  get esOrdenes(): boolean { return this.tipoSeleccionado === 'OR'; }
  puedeSeleccionar(orden: Orden): boolean { return orden.tipo === 'OR' && orden.estado === 'Cerrada'; }
  cambiarSeleccion(orden: Orden, marcada: boolean): void { marcada ? this.ordenesSeleccionadas.add(orden.id) : this.ordenesSeleccionadas.delete(orden.id); this.ordenesSeleccionadas = new Set(this.ordenesSeleccionadas); }

  get esTodos(): boolean {
    return this.tipoSeleccionado === 'TODOS';
  }

  get titulo(): string {
    if (this.esTodos) return 'Órdenes y presupuestos';
    return this.esPresupuestos ? 'Presupuestos' : 'Órdenes de reparación';
  }

  get tipo(): 'OR' | 'PR' | undefined {
    if (this.tipoSeleccionado === 'OR' || this.tipoSeleccionado === 'PR') {
      return this.tipoSeleccionado;
    }

    return undefined;
  }

  get estadosDisponibles(): string[] {
    if (this.tipoSeleccionado === 'OR') {
      return ['Abierta', 'En proceso', 'Cerrada', 'Facturada', 'Anulada'];
    }
    if (this.tipoSeleccionado === 'PR') {
      return ['Borrador', 'Enviado', 'Aceptado', 'Rechazado'];
    }
    return [
      'Borrador', 'Enviado', 'Aceptado', 'Rechazado',
      'Abierta', 'En proceso', 'Cerrada', 'Facturada', 'Anulada'
    ];
  }

  ngOnInit(): void {

    this.cargarOrdenes();

  }

  cargarOrdenes(): void {

    this.loading = true;

    this.ordenesService
      .getOrdenes(
        this.page,
        this.size,
        this.busqueda,
        this.tipo,
        this.estadoSeleccionado || undefined
      )
      .subscribe({

        next: data => {

          this.ordenes = data;

          this.dataSource.data = data.items;

          this.loading = false;

          this.cdr.detectChanges();

        },

        error: err => {

          this.loading = false;

          this.notification.showHttpError(err);

        }

      });

  }

  buscar(): void {

    this.page = 1;

    this.cargarOrdenes();

  }

  limpiarBusqueda(): void {

    this.busqueda = '';

    this.page = 1;

    this.cargarOrdenes();

  }

  seleccionarTipo(tipo: 'TODOS' | 'OR' | 'PR'): void {
    if (this.tipoSeleccionado === tipo) return;
    this.tipoSeleccionado = tipo;
    this.busqueda = '';
    this.estadoSeleccionado = '';
    this.page = 1;
    this.cargarOrdenes();
  }

  filtrarPorEstado(): void {
    this.page = 1;
    this.cargarOrdenes();
  }

  getTipoClass(tipo: string): string {
    switch (tipo) {
      case 'PR':
        return 'tipo-pr';
      case 'GA':
        return 'tipo-ga';
      default:
        return 'tipo-or';
    }
  }

  cambiarPagina(event: PageEvent): void {

    this.page = event.pageIndex + 1;

    this.size = event.pageSize;

    this.cargarOrdenes();

  }

  editar(id: number): void {

    this.router.navigate(['/ordenes', id]);

  }

  eliminar(id: number): void {

    const dialogRef = this.dialog.open(ConfirmDialog, {
      data: {
        title: 'Eliminar orden',
        message: '¿Seguro que deseas eliminar esta orden?'
      }
    });

    dialogRef.afterClosed().subscribe(confirmado => {

      if (!confirmado) {
        return;
      }

      this.ordenesService
        .deleteOrden(id)
        .subscribe({

          next: () => {

            this.notification.success(
              this.esPresupuestos ? 'Presupuesto eliminado correctamente' : 'Orden eliminada correctamente'
            );

            this.cargarOrdenes();

          },

          error: err => {

            this.notification.showHttpError(err);

          }

        });

    });

  }

  getEstadoClass(estado: string): string {

  switch (estado) {

    case 'Borrador':
      return 'estado-borrador';

    case 'En proceso':
      return 'estado-proceso';

    case 'Enviado':
      return 'estado-enviado';

    case 'Aceptado':
      return 'estado-aceptado';

    case 'Rechazado':
      return 'estado-rechazado';

    case 'Abierta':
      return 'estado-abierta';

    case 'Cerrada':
      return 'estado-cerrada';

    case 'Facturada':
      return 'estado-facturada';

    default:
      return '';

  }

}

  generarFactura(
  ordenId: number
  ): void {

  this.dialog.open(
    GenerarFacturaDialog
  ).afterClosed().subscribe(resultado => {

    if (!resultado) {
      return;
    }

    this.facturasService
        .crearDesdeOrden(
          ordenId,
          resultado.tipoDocumento,
          resultado.clienteId
        )
      .subscribe({

        next: factura => {

          this.notification.success(
            'Factura creada correctamente'
          );

          this.router.navigate([
            '/facturas',
            factura.id
          ]);

        },

        error: err => {

          this.notification.showHttpError(err);

          console.error(err);

        }

      });

  });

  }

  generarFacturaConjunta(): void {
    const ids = [...this.ordenesSeleccionadas];
    if (ids.length < 2) return;
    this.dialog.open(GenerarFacturaDialog).afterClosed().subscribe(resultado => {
      if (!resultado) return;
      this.facturasService.crearDesdeOrdenes(ids, resultado.tipoDocumento, resultado.clienteId).subscribe({ next: factura => { this.notification.success('Factura conjunta creada correctamente'); this.ordenesSeleccionadas.clear(); void this.router.navigate(['/facturas', factura.id]); }, error: err => this.notification.showHttpError(err) });
    });
  }

  convertirEnOrden(presupuesto: Orden): void {
    this.dialog.open(ConfirmDialog, {
      data: {
        title: 'Convertir en orden',
        message: `Se creará una orden de reparación con las líneas del presupuesto ${presupuesto.numero}.`
      }
    }).afterClosed().subscribe(confirmado => {
      if (!confirmado) return;

      this.ordenesService.convertirPresupuestoEnOrden(presupuesto.id).subscribe({
        next: orden => {
          this.notification.success(`Presupuesto convertido en ${orden.numero}.`);
          void this.router.navigate(['/ordenes', orden.id]);
        },
        error: err => this.notification.showHttpError(err)
      });
    });
  }

}
/** Listado principal de órdenes con filtros operativos y navegación a la ficha. */
