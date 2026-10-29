import {
  Component,
  ChangeDetectorRef,
  OnInit,
  inject
} from '@angular/core';

import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';

import {
  FormControl,
  ReactiveFormsModule
} from '@angular/forms';

import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatTableModule } from '@angular/material/table';
import { MatChipsModule } from '@angular/material/chips';
import { MatSelectModule } from '@angular/material/select';

import {
  debounceTime,
  distinctUntilChanged
} from 'rxjs';

import { ArticuloStock } from '../../models/articulo-stock';
import { ArticuloMasConsumido } from '../../models/articulo-mas-consumido';
import { MovimientoStock } from '../../models/movimiento-stock';
import { ResumenStock } from '../../models/resumen-stock';
import { StockService } from '../../services/stock.service';

import {
  NotificationService
} from '../../../../shared/services/notification';


@Component({
  selector: 'app-articulo-stock-list',

  standalone: true,

  imports: [
    CommonModule,
    RouterLink,
    ReactiveFormsModule,

    MatButtonModule,
    MatCardModule,
    MatIconModule,
    MatInputModule,
    MatFormFieldModule,
    MatTableModule,
    MatChipsModule,
    MatSelectModule
  ],

  templateUrl: './articulo-stock-list.html',

  styleUrl: './articulo-stock-list.scss'
})
export class ArticuloStockList implements OnInit {

  private stockService =
    inject(StockService);

  private notification =
    inject(NotificationService);

  private cdr = inject(ChangeDetectorRef);


  articulos: ArticuloStock[] = [];

  resumen?: ResumenStock;

  masConsumidos: ArticuloMasConsumido[] = [];

  movimientosRecientes: MovimientoStock[] = [];

  filtro = new FormControl(
    '',
    { nonNullable: true }
  );

  loading = false;

  filtroEstado: 'TODOS' | 'ACTIVOS' | 'INACTIVOS' =
    'ACTIVOS';

  filtroStock:
    'TODOS'
    | 'DISPONIBLE'
    | 'BAJO'
    | 'SIN_STOCK'
    = 'TODOS';

  filtroCategoria = '';

  filtroMarca = '';


  displayedColumns = [
    'referencia',
    'nombre',
    'marca',
    'categoria',
    'stock',
    'stock_minimo',
    'precio',
    'estado',
    'acciones'
  ];


  ngOnInit(): void {

    this.cargarArticulos();
    this.cargarActividadStock();

    this.filtro.valueChanges
      .pipe(
        debounceTime(250),
        distinctUntilChanged()
      )
      .subscribe(() => {
        // El filtrado se hace mediante getter.
      });

  }


  cargarArticulos(): void {

    this.loading = true;

    this.stockService
      .getArticulos(true)
      .subscribe({

        next: articulos => {

          this.articulos = articulos;

          this.loading = false;

          this.actualizarVista();

        },

        error: err => {

          this.loading = false;

          this.notification.showHttpError(
            err
          );

        }

      });

  }


  cargarActividadStock(): void {

    this.stockService.getResumen().subscribe({
      next: resumen => {
        this.resumen = resumen;
        this.actualizarVista();
      },
      error: err => this.notification.showHttpError(err)
    });

    this.stockService.getMasConsumidos().subscribe({
      next: articulos => {
        this.masConsumidos = articulos;
        this.actualizarVista();
      },
      error: err => this.notification.showHttpError(err)
    });

    this.stockService.getTodosMovimientos().subscribe({
      next: movimientos => {
        this.movimientosRecientes = movimientos.slice(0, 5);
        this.actualizarVista();
      },
      error: err => this.notification.showHttpError(err)
    });

  }


  private actualizarVista(): void {
    queueMicrotask(() => this.cdr.detectChanges());
  }


  get articulosFiltrados(): ArticuloStock[] {

    const texto =
      this.filtro.value
        .trim()
        .toLowerCase();

    return this.articulos.filter(
      articulo => {

        const coincideTexto = (
          !texto
          ||
          articulo.referencia
            .toLowerCase()
            .includes(texto)
          ||
          articulo.nombre
            .toLowerCase()
            .includes(texto)
          ||
          (
            articulo.marca ?? ''
          )
            .toLowerCase()
            .includes(texto)
        );

        const coincideEstado =
          this.filtroEstado === 'TODOS'
          || (this.filtroEstado === 'ACTIVOS' && articulo.activo)
          || (this.filtroEstado === 'INACTIVOS' && !articulo.activo);

        const coincideStock =
          this.filtroStock === 'TODOS'
          || (
            this.filtroStock === 'SIN_STOCK'
            && articulo.stock_actual <= 0
          )
          || (
            this.filtroStock === 'BAJO'
            && articulo.stock_actual > 0
            && articulo.stock_actual <= articulo.stock_minimo
          )
          || (
            this.filtroStock === 'DISPONIBLE'
            && articulo.stock_actual > articulo.stock_minimo
          );

        const coincideCategoria =
          !this.filtroCategoria
          || articulo.categoria === this.filtroCategoria;

        const coincideMarca =
          !this.filtroMarca
          || articulo.marca === this.filtroMarca;

        return (
          coincideTexto
          && coincideEstado
          && coincideStock
          && coincideCategoria
          && coincideMarca
        );

      }
    );

  }


  get categoriasDisponibles(): string[] {
    return [
      ...new Set(
        this.articulos
          .map(articulo => articulo.categoria)
          .filter((categoria): categoria is string => !!categoria)
      )
    ].sort();
  }


  get marcasDisponibles(): string[] {
    return [
      ...new Set(
        this.articulos
          .map(articulo => articulo.marca)
          .filter((marca): marca is string => !!marca)
      )
    ].sort();
  }


  cambiarEstadoArticulo(articulo: ArticuloStock): void {
    const activo = !articulo.activo;
    const accion = activo ? 'reactivar' : 'desactivar';

    if (!confirm(`¿Deseas ${accion} el artículo "${articulo.nombre}"?`)) {
      return;
    }

    this.stockService.cambiarEstadoArticulo(articulo.id, activo).subscribe({
      next: actualizado => {
        this.articulos = this.articulos.map(item =>
          item.id === actualizado.id ? actualizado : item
        );
        this.cargarActividadStock();
        this.notification.success(
          `Artículo ${activo ? 'reactivado' : 'desactivado'} correctamente.`
        );
      },
      error: err => this.notification.showHttpError(err)
    });
  }


  get totalArticulos(): number {
    return this.articulos.length;
  }


  get totalStockBajo(): number {

    return this.articulos.filter(
      articulo =>
        articulo.activo
        &&
        articulo.stock_actual
        <=
        articulo.stock_minimo
    ).length;

  }


  get totalSinStock(): number {

    return this.articulos.filter(
      articulo =>
        articulo.activo
        &&
        articulo.stock_actual <= 0
    ).length;

  }


  esStockBajo(
    articulo: ArticuloStock
  ): boolean {

    return (
      articulo.activo
      &&
      articulo.stock_actual
      <=
      articulo.stock_minimo
    );

  }


  estaSinStock(
    articulo: ArticuloStock
  ): boolean {

    return articulo.activo && articulo.stock_actual <= 0;

  }


  getArticuloMovimiento(
    movimiento: MovimientoStock
  ): ArticuloStock | undefined {
    return this.articulos.find(
      articulo => articulo.id === movimiento.articulo_id
    );
  }


  esMovimientoSalida(
    movimiento: MovimientoStock
  ): boolean {
    return [
      'SALIDA',
      'AJUSTE_NEGATIVO',
      'CONSUMO_ORDEN'
    ].includes(movimiento.tipo);
  }

}
/** Catálogo de almacén con resumen, consumo y navegación al detalle de artículo. */
