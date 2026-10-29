import {
  AfterViewInit,
  ChangeDetectorRef,
  Component,
  DestroyRef,
  inject,
  OnInit
} from '@angular/core';

import { ClientesService } from '../../services/clientes.service';
import { ClientePage } from '../../models/cliente-page';

import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

import { MatTableModule } from '@angular/material/table';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatPaginatorModule } from '@angular/material/paginator';
import { MatTooltipModule } from '@angular/material/tooltip';

import { PageEvent } from '@angular/material/paginator';
import { RouterLink } from '@angular/router';
import { Router } from '@angular/router';
import { MatTableDataSource } from '@angular/material/table';
import { MatDialog } from '@angular/material/dialog';
import { ConfirmDialog } from '../../../../shared/components/confirm-dialog/confirm-dialog';
import { NotificationService } from '../../../../shared/services/notification';
import { MatSortModule } from '@angular/material/sort';
import { ViewChild } from '@angular/core';
import { MatSort } from '@angular/material/sort';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { timeout } from 'rxjs/operators';

@Component({
  selector: 'app-clientes-list',
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
            MatSortModule,
            RouterLink,
            MatProgressSpinnerModule,
            MatTooltipModule
            ],
  templateUrl: './clientes-list.html',
  styleUrl: './clientes-list.scss',
})
export class ClientesList implements OnInit, AfterViewInit {

  private clientesService = inject(ClientesService);

  clientes?: ClientePage;

  dataSource = new MatTableDataSource();

  private router = inject(Router);

  private dialog = inject(MatDialog);

  private notification = inject(NotificationService);

  private readonly changeDetector = inject(ChangeDetectorRef);

  private readonly destroyRef = inject(DestroyRef);

  @ViewChild(MatSort)
  sort!: MatSort;

  loading = false;

  deleting = false;

  displayedColumns = [
  'codigo',
  'nombre',
  'dni',
  'telefono',
  'email',
  'estado',
  'acciones'
  ];

  busqueda = '';

  private busquedaTimer?: ReturnType<typeof setTimeout>;

  page = 1;

  size = 10;

  ngOnInit(): void {
    this.cargarClientes();
  }

  ngAfterViewInit(): void {
    this.dataSource.sort = this.sort;
  }

  cargarClientes(): void {

  this.loading = true;
  this.actualizarVista();

  this.clientesService
    .getClientes(
      this.page,
      this.size,
      this.busqueda
    )
    .pipe(
      // Evita que una petición bloqueada deje la pantalla cargando para siempre.
      timeout(30000),
      takeUntilDestroyed(this.destroyRef)
    )
    .subscribe({

      next: data => {

        this.clientes = data;

        this.dataSource.data = data.items;

        if (this.sort) {
          this.dataSource.sort = this.sort;
        }

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
    // El proyecto usa carga zoneless en algunas rutas. Forzamos el refresco
    // tras las respuestas HTTP para no depender de una interacción del usuario.
    this.changeDetector.markForCheck();
    this.changeDetector.detectChanges();
  }

  buscar(): void {

    this.page = 1;

    this.cargarClientes();

  }

  alCambiarBusqueda(): void {
    if (this.busquedaTimer) {
      clearTimeout(this.busquedaTimer);
    }

    this.busquedaTimer = setTimeout(() => this.buscar(), 250);
  }

  cambiarPagina(event: PageEvent): void {

    this.page = event.pageIndex + 1;

    this.size = event.pageSize;

    this.cargarClientes();

  }

  editar(id: number): void {

    this.router.navigate(['/clientes', id]);

  }

  eliminar(id: number): void {

    this.deleting = true;

    this.dialog.open(ConfirmDialog, {

      data: {

        title: 'Eliminar cliente',

        message: '¿Seguro que deseas eliminar este cliente?'

      }

    }).afterClosed().subscribe(result => {

        if (!result) {
          return;
        }

        this.clientesService
            .deleteCliente(id)
            .subscribe({

              next: () => {

                this.deleting = false;

                this.notification.success(
                'Cliente eliminado correctamente'
                );

                this.cargarClientes();

              },

              error: err => {
                this.deleting = false;

                this.notification.showHttpError(err);

                console.error(err);

              }

            });

    });

  }

  limpiarBusqueda(): void {

    this.busqueda = '';

    this.page = 1;

    this.cargarClientes();

  }

}
/** Listado paginado de clientes con búsqueda y navegación a su ficha. */
