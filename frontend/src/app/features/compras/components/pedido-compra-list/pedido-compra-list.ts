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
import { MatChipsModule } from '@angular/material/chips';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatTableModule } from '@angular/material/table';

import {
  PedidoCompra
} from '../../models/pedido-compra';

import {
  PedidosCompraService
} from '../../services/pedidos-compra.service';

import {
  NotificationService
} from '../../../../shared/services/notification';


@Component({
  selector: 'app-pedido-compra-list',

  standalone: true,

  imports: [
    CommonModule,
    RouterLink,
    ReactiveFormsModule,

    MatButtonModule,
    MatCardModule,
    MatChipsModule,
    MatFormFieldModule,
    MatIconModule,
    MatInputModule,
    MatSelectModule,
    MatTableModule
  ],

  templateUrl: './pedido-compra-list.html',
  styleUrl: './pedido-compra-list.scss'
})
export class PedidoCompraList implements OnInit {

  private pedidosService =
    inject(PedidosCompraService);

  private notification =
    inject(NotificationService);

  private readonly changeDetector =
    inject(ChangeDetectorRef);


  pedidos: PedidoCompra[] = [];

  loading = false;

  filtroTexto = new FormControl(
    '',
    { nonNullable: true }
  );

  filtroEstado = 'TODOS';

  estados = [
    'TODOS',
    'BORRADOR',
    'ENVIADO',
    'RECIBIDO_PARCIAL',
    'RECIBIDO',
    'CANCELADO'
  ];


  displayedColumns = [
    'numero',
    'fecha',
    'proveedor',
    'estado',
    'recepcion',
    'total',
    'acciones'
  ];


  ngOnInit(): void {
    this.cargarPedidos();
  }


  cargarPedidos(): void {

    this.loading = true;

    this.pedidosService
      .getPedidos()
      .subscribe({

        next: pedidos => {

          this.pedidos = pedidos;

          this.loading = false;
          this.actualizarVista();

        },

        error: err => {

          this.loading = false;
          this.actualizarVista();

          this.notification.showHttpError(
            err
          );

        }

      });

  }

  private actualizarVista(): void {
    this.changeDetector.markForCheck();
    this.changeDetector.detectChanges();
  }


  get pedidosFiltrados(): PedidoCompra[] {

    const texto =
      this.filtroTexto.value
        .trim()
        .toLowerCase();

    return this.pedidos.filter(
      pedido => {

        const coincideTexto =
          !texto
          ||
          pedido.numero
            .toLowerCase()
            .includes(texto)
          ||
          pedido.proveedor.nombre
            .toLowerCase()
            .includes(texto)
          ||
          pedido.proveedor.cif
            .toLowerCase()
            .includes(texto);

        const coincideEstado =
          this.filtroEstado === 'TODOS'
          ||
          pedido.estado === this.filtroEstado;

        return (
          coincideTexto
          &&
          coincideEstado
        );

      }
    );

  }


  get totalBorradores(): number {

    return this.pedidos.filter(
      pedido =>
        pedido.estado === 'BORRADOR'
    ).length;

  }


  get totalPendientesRecepcion(): number {

    return this.pedidos.filter(
      pedido =>
        pedido.estado === 'ENVIADO'
        ||
        pedido.estado === 'RECIBIDO_PARCIAL'
    ).length;

  }


  get totalRecibidos(): number {

    return this.pedidos.filter(
      pedido =>
        pedido.estado === 'RECIBIDO'
    ).length;

  }


  porcentajeRecibido(
    pedido: PedidoCompra
  ): number {

    const pedida = pedido.lineas.reduce(
      (total, linea) =>
        total +
        Number(linea.cantidad_pedida),
      0
    );

    if (pedida <= 0) {
      return 0;
    }

    const recibida = pedido.lineas.reduce(
      (total, linea) =>
        total +
        Number(linea.cantidad_recibida),
      0
    );

    return Math.min(
      100,
      Math.round(
        (recibida / pedida) * 100
      )
    );

  }


  getEstadoTexto(
    estado: string
  ): string {

    switch (estado) {

      case 'BORRADOR':
        return 'Borrador';

      case 'ENVIADO':
        return 'Enviado';

      case 'RECIBIDO_PARCIAL':
        return 'Recibido parcial';

      case 'RECIBIDO':
        return 'Recibido';

      case 'CANCELADO':
        return 'Cancelado';

      default:
        return estado;

    }

  }

}
/** Listado de pedidos de compra y acceso a sus transiciones operativas. */
