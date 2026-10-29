import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatTableModule } from '@angular/material/table';
import { finalize } from 'rxjs';

import { Cliente } from '../../../clientes/models/cliente';
import { ClientesService } from '../../../clientes/services/clientes.service';
import { ArticuloStock } from '../../models/articulo-stock';
import { AlbaranVentaCreate } from '../../models/albaran-venta';
import { StockService } from '../../services/stock.service';
import { AlbaranVentaService } from '../../services/albaran-venta.service';
import { NotificationService } from '../../../../shared/services/notification';
import { AutocompleteSelect } from '../../../../shared/components/autocomplete-select/autocomplete-select';

interface LineaFormulario {
  articulo_stock_id: number;
  referencia: string;
  descripcion: string;
  cantidad: number;
  precio_unitario: number;
  descuento_porcentaje: number;
}

@Component({
  selector: 'app-albaran-venta-form',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink, MatButtonModule, MatCardModule, MatFormFieldModule, MatIconModule, MatInputModule, MatSelectModule, MatTableModule, AutocompleteSelect],
  templateUrl: './albaran-venta-form.html',
  styleUrl: './albaran-venta-form.scss',
})
export class AlbaranVentaForm implements OnInit {
  private readonly clientesService = inject(ClientesService);
  private readonly stockService = inject(StockService);
  private readonly albaranesService = inject(AlbaranVentaService);
  private readonly notification = inject(NotificationService);
  private readonly router = inject(Router);

  clientes: Cliente[] = [];
  articulos: ArticuloStock[] = [];
  lineas: LineaFormulario[] = [];
  cargando = false;
  guardando = false;

  clienteId: number | null = null;
  etiquetaCliente = (cliente: Cliente): string => [
    cliente.apellidos,
    cliente.nombre,
    cliente.dni,
    cliente.telefono,
    cliente.email,
  ].filter(valor => Boolean(valor?.trim())).join(' · ');
  fecha = new Date().toISOString().slice(0, 10);
  observaciones = '';
  articuloId: number | null = null;
  cantidad = 1;
  precioUnitario: number | null = null;
  descuento = 0;

  ngOnInit(): void {
    this.clientesService.getClientesSelect().subscribe({
      // El endpoint /select ya devuelve exclusivamente clientes activos.
      // ClienteSelect no incluye el campo "activo", por lo que filtrarlo
      // en el navegador dejaba el selector vacío.
      next: clientes => this.clientes = clientes,
      error: error => this.notification.showHttpError(error),
    });
    this.stockService.getArticulos().subscribe({
      next: articulos => this.articulos = articulos.filter(articulo => articulo.activo),
      error: error => this.notification.showHttpError(error),
    });
  }

  seleccionarArticulo(): void {
    const articulo = this.articulos.find(item => item.id === this.articuloId);
    this.precioUnitario = articulo ? articulo.precio_venta : null;
  }

  agregarLinea(): void {
    const articulo = this.articulos.find(item => item.id === this.articuloId);
    if (!articulo || !this.cantidad || this.cantidad <= 0 || this.precioUnitario === null || this.precioUnitario < 0) {
      this.notification.error('Selecciona un art\u00edculo e indica una cantidad y precio v\u00e1lidos.');
      return;
    }
    if (this.lineas.some(linea => linea.articulo_stock_id === articulo.id)) {
      this.notification.error('Ese art\u00edculo ya est\u00e1 incluido en el albar\u00e1n.');
      return;
    }
    this.lineas = [...this.lineas, {
      articulo_stock_id: articulo.id,
      referencia: articulo.referencia,
      descripcion: articulo.nombre,
      cantidad: this.cantidad,
      precio_unitario: this.precioUnitario,
      descuento_porcentaje: this.descuento || 0,
    }];
    this.articuloId = null;
    this.cantidad = 1;
    this.precioUnitario = null;
    this.descuento = 0;
  }

  eliminarLinea(indice: number): void { this.lineas = this.lineas.filter((_, current) => current !== indice); }

  totalLinea(linea: LineaFormulario): number {
    return linea.cantidad * linea.precio_unitario * (1 - linea.descuento_porcentaje / 100);
  }

  get total(): number { return this.lineas.reduce((acumulado, linea) => acumulado + this.totalLinea(linea), 0); }

  guardar(): void {
    if (!this.clienteId || !this.fecha || this.lineas.length === 0) {
      this.notification.error('Indica cliente, fecha y al menos una l\u00ednea.');
      return;
    }
    this.guardando = true;
    const datos: AlbaranVentaCreate = {
      cliente_id: this.clienteId,
      fecha: this.fecha,
      observaciones: this.observaciones.trim() || null,
      lineas: this.lineas.map(linea => ({
        articulo_stock_id: linea.articulo_stock_id,
        cantidad: linea.cantidad,
        precio_unitario: linea.precio_unitario,
        descuento_porcentaje: linea.descuento_porcentaje,
      })),
    };
    this.albaranesService.crear(datos).pipe(finalize(() => this.guardando = false)).subscribe({
      next: () => { this.notification.success('Albar\u00e1n de venta creado en borrador.'); this.router.navigate(['/stock/albaranes-venta']); },
      error: error => { this.notification.showHttpError(error); },
    });
  }
}
