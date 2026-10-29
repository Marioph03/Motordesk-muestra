import { Vehiculos } from './../../services/vehiculos';
import {
  ChangeDetectorRef,
  Component,
  DestroyRef,
  OnInit,
  inject
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { PageEvent } from '@angular/material/paginator';

import { VehiculoPage } from '../../models/vehiculo-page';

import { MatTableDataSource, MatTableModule } from '@angular/material/table';
import { Vehiculo } from '../../models/vehiculo';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatPaginatorModule } from '@angular/material/paginator';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatTooltipModule } from '@angular/material/tooltip';
import { NotificationService } from '../../../../shared/services/notification';
import { MatDialog } from '@angular/material/dialog';
import { ConfirmDialog } from '../../../../shared/components/confirm-dialog/confirm-dialog';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { timeout } from 'rxjs/operators';

@Component({
  selector: 'app-vehiculos-list',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    MatTableModule,
    MatButtonModule,
    MatIconModule,
    MatInputModule,
    MatFormFieldModule,
    MatPaginatorModule,
    MatProgressSpinnerModule,
    RouterLink,
    MatTooltipModule
  ],
  templateUrl: './vehiculos-list.html',
  styleUrl: './vehiculos-list.scss'
})
export class VehiculosList implements OnInit {

  private vehiculosService = inject(Vehiculos);

  dataSource = new MatTableDataSource<Vehiculo>();

  vehiculos?: VehiculoPage;

  private router = inject(Router);

  private notification = inject(NotificationService);

  private dialog = inject(MatDialog);

  private readonly changeDetector = inject(ChangeDetectorRef);

  private readonly destroyRef = inject(DestroyRef);

  displayedColumns = [
  'codigo',
  'matricula',
  'marca',
  'modelo',
  'cliente',
  'acciones',
  ];

  busqueda = '';

  page = 1;

  size = 10;

  loading = false;

  ngOnInit(): void {

    console.log('VehiculosList cargado');

    this.cargarVehiculos();

  }

  cargarVehiculos(): void {

    this.loading = true;
    this.actualizarVista();

    this.vehiculosService
      .getVehiculos(
          this.page,
          this.size,
          this.busqueda
      )
      .pipe(
        timeout(30000),
        takeUntilDestroyed(this.destroyRef)
      )
      .subscribe({

          next: data => {

              this.vehiculos = data;

              this.dataSource.data = data.items;

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

  test(): void {
  this.vehiculos = {
    items: [],
    total: 99,
    page: 1,
    size: 10
  };
}

  buscar(): void {

  this.page = 1;

  this.cargarVehiculos();

}

cambiarPagina(event: PageEvent): void {

  this.page = event.pageIndex + 1;

  this.size = event.pageSize;

  this.cargarVehiculos();

}

editar(id: number): void {

  this.router.navigate(['/vehiculos', id]);

}

eliminar(id: number): void {

  const dialogRef = this.dialog.open(ConfirmDialog, {
    data: {
      title: 'Eliminar vehículo',
      message: '¿Seguro que deseas eliminar este vehículo?'
    }
  });

  dialogRef.afterClosed().subscribe(confirmado => {

    if (!confirmado) {
      return;
    }

    this.vehiculosService
      .deleteVehiculo(id)
      .subscribe({

        next: () => {

          this.notification.success(
            'Vehículo eliminado correctamente'
          );

          this.cargarVehiculos();

        },

        error: err => {

          this.notification.showHttpError(err);

        }

      });

  });

}

limpiarBusqueda(): void {

  this.busqueda = '';

  this.page = 1;

  this.cargarVehiculos();

}

}
/** Listado paginado de vehículos y búsqueda por matrícula, cliente o marca. */
