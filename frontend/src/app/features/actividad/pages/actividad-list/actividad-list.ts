import {
  ChangeDetectorRef,
  Component,
  OnInit,
  ViewChild,
  inject
} from '@angular/core';

import { FormsModule } from '@angular/forms';

import { MatTableDataSource, MatTableModule } from '@angular/material/table';
import { MatPaginatorModule, PageEvent } from '@angular/material/paginator';
import { MatSort, MatSortModule } from '@angular/material/sort';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatChipsModule } from '@angular/material/chips';

import { ActividadService } from '../../services/actividad.service';
import { ActividadPage } from '../../models/actividad-page';
import { ActividadFilter } from '../../models/actividad-filter';

import { NotificationService } from '../../../../shared/services/notification';
import { MatIconModule } from '@angular/material/icon';
import { DatePipe } from '@angular/common';
import { MatSelectModule } from '@angular/material/select';
import { MatButtonModule } from '@angular/material/button';
import { MatDatepickerModule } from '@angular/material/datepicker';
import { MatNativeDateModule } from '@angular/material/core';

@Component({
  selector: 'app-actividad-list',
  standalone: true,
  imports: [
    FormsModule,
    MatTableModule,
    MatPaginatorModule,
    MatSortModule,
    MatFormFieldModule,
    MatInputModule,
    MatProgressSpinnerModule,
    MatIconModule,
    DatePipe,
    MatChipsModule,
    MatSelectModule,
    MatButtonModule,
    MatDatepickerModule,
    MatNativeDateModule
  ],
  templateUrl: './actividad-list.html',
  styleUrl: './actividad-list.scss'
})
export class ActividadList implements OnInit {

  private actividadService = inject(ActividadService);

  private notification = inject(NotificationService);

  private readonly changeDetector = inject(ChangeDetectorRef);

  actividades?: ActividadPage;

  dataSource = new MatTableDataSource();

  @ViewChild(MatSort)
  sort!: MatSort;

  loading = false;

  page = 1;

  size = 10;

  filtro: ActividadFilter = {};

  displayedColumns = [
  'fecha',
  'usuario',
  'modulo',
  'accion',
  'descripcion'
  ];

  modulos = [
    'AUTENTICACION',
    'CLIENTES',
    'VEHICULOS',
    'PROVEEDORES',
    'USUARIOS',
    'EMPRESA',
    'ORDENES',
    'MANO_OBRA',
    'PIEZAS',
    'ARCHIVOS_ORDEN',
    'FACTURAS',
    'LINEAS_FACTURA',
    'COBROS',
    'VERIFACTU',
    'WHATSAPP'
  ];

  acciones = [
    'CREAR',
    'ACTUALIZAR',
    'ELIMINAR',
    'DESACTIVAR',
    'INICIO_SESION',
    'ENVIAR_EMAIL',
    'ENVIAR_WHATSAPP',
    'EMITIR_FACTURA',
    'ANULAR_FACTURA',
    'ACTUALIZAR_DESDE_ORDEN',
    'GENERAR_VERIFACTU',
    'GENERAR_ANULACION_VERIFACTU',
    'ENVIAR_AEAT_TEST',
    'CREAR_GARANTIA',
    'INICIAR_REVISION',
    'APROBAR_GARANTIA',
    'RECHAZAR_GARANTIA',
    'INICIAR_REPARACION',
    'RESOLVER_GARANTIA',
    'ENVIAR_PRESUPUESTO',
    'ACEPTAR_PRESUPUESTO',
    'RECHAZAR_PRESUPUESTO',
    'CONVERTIR_EN_ORDEN'
  ];

  ngOnInit(): void {

    this.cargarActividades();

  }

  cargarActividades(): void {

    this.loading = true;

    this.actividadService
      .getActividades(
        this.page,
        this.size,
        this.filtro
      )
      .subscribe({

        next: data => {

          this.actividades = data;

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

    this.cargarActividades();

  }

  getActionColor(accion: string): string {

  switch (accion) {

    case 'CREAR':
      return 'green';

    case 'ACTUALIZAR':
      return 'orange';

    case 'ELIMINAR':
      return 'red';

    case 'DESACTIVAR':
      return 'gray';

    case 'INICIO_SESION':
      return 'blue';

    default:
      if (accion.startsWith('FALLO_')) return '#c62828';
      return '#607d8b';

  }
  }

  getModuleIcon(modulo: string): string {

  switch (modulo) {

    case 'CLIENTES':
      return 'people';

    case 'VEHICULOS':
      return 'directions_car';

    case 'ORDENES':
      return 'build';

    case 'FACTURAS':
      return 'description';

    case 'PROVEEDORES':
      return 'local_shipping';

    case 'USUARIOS':
      return 'group';

    case 'COBROS':
      return 'payments';

    case 'VERIFACTU':
      return 'verified';

    case 'AUTENTICACION':
      return 'login';

    case 'MANO_OBRA':
    case 'PIEZAS':
      return 'construction';

    case 'EMPRESA':
      return 'business';

    default:
      return 'folder';

  }

  }

  buscar(): void {

  this.page = 1;

  this.cargarActividades();

  }

  limpiarFiltros(): void {

  this.filtro = {};

  this.page = 1;

  this.cargarActividades();

  }

}
/** Vista de actividad auditable con filtros, paginación y detalle temporal. */
