import {
  ChangeDetectorRef,
  Component,
  OnInit,
  ViewChild,
  inject
} from '@angular/core';

import { Router, RouterLink } from '@angular/router';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

import { MatTableDataSource, MatTableModule } from '@angular/material/table';
import { MatPaginatorModule, PageEvent } from '@angular/material/paginator';
import { MatSort, MatSortModule } from '@angular/material/sort';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatChipsModule } from '@angular/material/chips';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';

import { FacturasService } from '../../services/facturas.service';
import { FacturaPage } from '../../models/factura-page';
import { FacturaFilter } from '../../models/factura-filter';
import { ClientesService } from '../../../clientes/services/clientes.service';
import { Cliente } from '../../../clientes/models/cliente';
import { AutocompleteSelect } from '../../../../shared/components/autocomplete-select/autocomplete-select';

import { NotificationService } from '../../../../shared/services/notification';
import { MatDialog } from '@angular/material/dialog';
import { ConfirmDialog } from '../../../../shared/components/confirm-dialog/confirm-dialog';

import { DatePipe, DecimalPipe } from '@angular/common';

@Component({
  selector: 'app-facturas-list',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    MatTableModule,
    MatPaginatorModule,
    MatSortModule,
    MatButtonModule,
    MatIconModule,
    MatProgressSpinnerModule,
    MatChipsModule,
    MatTooltipModule,
    MatFormFieldModule,
    MatInputModule,
    MatSelectModule,
    AutocompleteSelect,
    DatePipe,
    DecimalPipe,
    RouterLink
  ],
  templateUrl: './facturas-list.html',
  styleUrl: './facturas-list.scss'
})
export class FacturasList implements OnInit {

  private facturasService = inject(FacturasService);
  private clientesService = inject(ClientesService);

  private notification = inject(NotificationService);

  private router = inject(Router);

  private dialog = inject(MatDialog);

  private readonly changeDetector = inject(ChangeDetectorRef);

  facturas?: FacturaPage;

  dataSource = new MatTableDataSource();

  @ViewChild(MatSort)
  sort!: MatSort;

  loading = false;

  page = 1;

  size = 10;

  filtro: FacturaFilter = {};

  clientes: Cliente[] = [];

  tiposDocumento = ['FACTURA', 'PROFORMA', 'PRESUPUESTO', 'ALBARAN', 'ABONO'];

  etiquetaCliente = (cliente: Cliente): string => [
    cliente.apellidos,
    cliente.nombre,
    cliente.dni,
    cliente.telefono,
    cliente.email,
  ].filter(valor => Boolean(valor?.trim())).join(' · ');

  displayedColumns = [
    'numero',
    'tipo',
    'fecha',
    'cliente',
    'estado',
    'total',
    'acciones'
  ];

  getTipoFacturaLabel(tipo: string): string {
    return ({
      REPARACION: 'Reparaci\u00f3n',
      PRESUPUESTO: 'Presupuesto',
      GARANTIA: 'Garant\u00eda',
      RECAMBIO: 'Recambio',
      VENTAS_COMISIONES: 'Ventas y comisiones',
    } as Record<string, string>)[tipo] ?? tipo;
  }

  ngOnInit(): void {

    this.cargarFacturas();
    this.cargarClientes();

  }

  cargarFacturas(): void {

    this.loading = true;

    this.facturasService
      .getFacturas(
        this.page,
        this.size,
        this.filtro
      )
      .subscribe({

        next: data => {

          this.facturas = data;

          this.dataSource.data = data.items;

          this.dataSource.sort = this.sort;

          this.loading = false;
          this.actualizarVista();

        },

        error: err => {

          this.loading = false;
          this.actualizarVista();

          this.notification.showHttpError(err);

          console.error(err);

        }

      });

  }

  private actualizarVista(): void {
    this.changeDetector.markForCheck();
    this.changeDetector.detectChanges();
  }

  cambiarPagina(
    event: PageEvent
  ): void {

    this.page = event.pageIndex + 1;

    this.size = event.pageSize;

    this.cargarFacturas();

  }

  buscar(): void {
    this.page = 1;
    this.cargarFacturas();
  }

  limpiarFiltros(): void {
    this.filtro = {};
    this.page = 1;
    this.cargarFacturas();
  }

  nombreCliente(cliente: Cliente): string {
    return [cliente.apellidos, cliente.nombre].filter(Boolean).join(', ');
  }

  private cargarClientes(): void {
    this.clientesService.getClientesSelect().subscribe({
      next: clientes => this.clientes = clientes,
      error: err => this.notification.showHttpError(err)
    });
  }

  editar(
    id: number
  ): void {

    this.router.navigate([
      '/facturas',
      id
    ]);

  }

  eliminar(id: number): void {

    this.dialog.open(ConfirmDialog, {
      data: {
        title: 'Eliminar factura',
        message: '¿Seguro que deseas eliminar esta factura?'
      }
    }).afterClosed().subscribe(result => {
      if (!result) {
        return;
      }
      this.facturasService
        .deleteFactura(id)
        .subscribe({
          next: () => {
            this.notification.success('Factura eliminada correctamente');
            this.cargarFacturas();
          },
          error: err => {
            this.notification.showHttpError(err);
            console.error(err);
          }
        });
    });

  }

  getEstadoClass(
    estado: string
  ): string {

    if (!estado) return 'info';

    const normalized = estado.trim().toLowerCase().replace(/\s+/g, '-');

    if (normalized === 'pagada') return 'success';
    if (normalized === 'pendiente') return 'warning';
    if (normalized === 'cancelada') return 'danger';

    return 'info';

  }

}
/** Listado de facturas con filtros y enlaces a acciones fiscales permitidas. */
