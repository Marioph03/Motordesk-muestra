import {
  Component,
  ChangeDetectorRef,
  OnInit,
  inject
} from '@angular/core';

import { CommonModule } from '@angular/common';
import {
  Router,
  RouterLink
} from '@angular/router';

import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatChipsModule } from '@angular/material/chips';
import { MatIconModule } from '@angular/material/icon';
import { MatTableModule } from '@angular/material/table';
import { finalize } from 'rxjs';

import { ArticuloStock } from '../../models/articulo-stock';
import { StockService } from '../../services/stock.service';
import { NotificationService } from '../../../../shared/services/notification';
import {
  PedidosCompraService
} from '../../../compras/services/pedidos-compra.service';


@Component({
  selector: 'app-reposicion-stock',
  standalone: true,
  imports: [
    CommonModule,
    RouterLink,
    MatButtonModule,
    MatCardModule,
    MatChipsModule,
    MatIconModule,
    MatTableModule
  ],
  templateUrl: './reposicion-stock.html',
  styleUrl: './reposicion-stock.scss'
})
export class ReposicionStock implements OnInit {

  private stockService = inject(StockService);
  private notification = inject(NotificationService);
  private pedidosCompraService = inject(PedidosCompraService);
  private router = inject(Router);
  private readonly changeDetector = inject(ChangeDetectorRef);

  articulos: ArticuloStock[] = [];
  loading = false;
  generando = false;

  readonly displayedColumns = [
    'referencia',
    'articulo',
    'stock',
    'minimo',
    'faltan',
    'estado',
    'acciones'
  ];

  ngOnInit(): void {
    this.cargarNecesidades();
  }

  cargarNecesidades(): void {
    this.loading = true;

    this.stockService.getNecesidadesReposicion().subscribe({
      next: articulos => {
        this.articulos = articulos;
        this.loading = false;
        this.actualizarVista();
      },
      error: err => {
        this.loading = false;
        this.actualizarVista();
        this.notification.showHttpError(err);
      }
    });
  }

  private actualizarVista(): void {
    this.changeDetector.markForCheck();
    this.changeDetector.detectChanges();
  }

  getCantidadReposicion(articulo: ArticuloStock): number {
    return Math.max(
      0,
      articulo.stock_minimo - articulo.stock_actual
    );
  }

  estaSinStock(articulo: ArticuloStock): boolean {
    return articulo.stock_actual <= 0;
  }

  prepararReposicion(articulo: ArticuloStock): void {
    void this.router.navigate(['/stock', articulo.id]);
  }

  get sinProveedorHabitual(): number {
    return this.articulos.filter(articulo => !articulo.proveedor_habitual_id).length;
  }

  generarPedidosReposicion(): void {
    if (this.generando) return;
    this.generando = true;
    this.pedidosCompraService
      .generarDesdeReposicion()
      .pipe(finalize(() => this.generando = false))
      .subscribe({
        next: pedidos => {
          this.notification.success(
            `${pedidos.length} pedido(s) generado(s) correctamente.`
          );

          if (this.sinProveedorHabitual) {
            this.notification.info(`${this.sinProveedorHabitual} artículo(s) no se incluyeron porque no tienen proveedor habitual.`);
          }

          void this.router.navigate([
            '/compras/pedidos'
          ]);
        },
        error: err => {
          this.notification.showHttpError(err);
        }
      });
  }
}
/** Vista de reposición que permite generar borradores de compra por proveedor. */
