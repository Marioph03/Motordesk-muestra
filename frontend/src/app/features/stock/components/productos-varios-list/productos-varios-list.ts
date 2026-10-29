import { ChangeDetectorRef, Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { finalize, timeout } from 'rxjs';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatTableModule } from '@angular/material/table';
import { ArticuloStock } from '../../models/articulo-stock';
import { StockService } from '../../services/stock.service';
import { NotificationService } from '../../../../shared/services/notification';

@Component({ selector: 'app-productos-varios-list', standalone: true, imports: [CommonModule, RouterLink, MatButtonModule, MatCardModule, MatIconModule, MatTableModule], templateUrl: './productos-varios-list.html', styleUrl: './productos-varios-list.scss' })
export class ProductosVariosList implements OnInit {
  private readonly stock = inject(StockService);
  private readonly notification = inject(NotificationService);
  private readonly cdr = inject(ChangeDetectorRef);
  productos: ArticuloStock[] = [];
  cargando = true;
  readonly columnas = ['referencia', 'nombre', 'categoria', 'precio', 'acciones'];
  ngOnInit(): void {
    this.stock.getArticulos(false).pipe(timeout(12_000), finalize(() => { this.cargando = false; this.cdr.detectChanges(); })).subscribe({ next: productos => { this.productos = productos; this.cdr.markForCheck(); }, error: error => this.notification.showHttpError(error) });
  }
}
