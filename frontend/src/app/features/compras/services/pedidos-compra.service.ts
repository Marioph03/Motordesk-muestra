/** Cliente del ciclo de compra: borrador, envío y recepciones parciales. */
import { inject, Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';

import { Observable } from 'rxjs';

import {
  LineaPedidoCompra,
  PedidoCompra
} from '../models/pedido-compra';

import {
  PedidoCompraCreate
} from '../models/pedido-compra-create';

import {
  PedidoCompraUpdate
} from '../models/pedido-compra-update';

import {
  LineaPedidoCompraCreate
} from '../models/linea-pedido-compra-create';

import {
  LineaPedidoCompraUpdate
} from '../models/linea-pedido-compra-update';

import {
  RecepcionPedido
} from '../models/recepcion-pedido';
import { API_URL } from '../../../core/tokens/api.token';


@Injectable({
  providedIn: 'root'
})
export class PedidosCompraService {

  private http = inject(HttpClient);

  private apiUrl =
    `${inject(API_URL)}/pedidos-compra`;


  getPedidos(): Observable<PedidoCompra[]> {

    return this.http.get<PedidoCompra[]>(
      this.apiUrl
    );

  }


  getPedido(
    pedidoId: number
  ): Observable<PedidoCompra> {

    return this.http.get<PedidoCompra>(
      `${this.apiUrl}/${pedidoId}`
    );

  }


  crearPedido(
    datos: PedidoCompraCreate
  ): Observable<PedidoCompra> {

    return this.http.post<PedidoCompra>(
      this.apiUrl,
      datos
    );

  }


  actualizarPedido(
    pedidoId: number,
    datos: PedidoCompraUpdate
  ): Observable<PedidoCompra> {

    return this.http.patch<PedidoCompra>(
      `${this.apiUrl}/${pedidoId}`,
      datos
    );

  }


  añadirLinea(
    pedidoId: number,
    datos: LineaPedidoCompraCreate
  ): Observable<LineaPedidoCompra> {

    return this.http.post<LineaPedidoCompra>(
      `${this.apiUrl}/${pedidoId}/lineas`,
      datos
    );

  }


  actualizarLinea(
    lineaId: number,
    datos: LineaPedidoCompraUpdate
  ): Observable<LineaPedidoCompra> {

    return this.http.patch<LineaPedidoCompra>(
      `${this.apiUrl}/lineas/${lineaId}`,
      datos
    );

  }


  eliminarLinea(
    lineaId: number
  ): Observable<void> {

    return this.http.delete<void>(
      `${this.apiUrl}/lineas/${lineaId}`
    );

  }


  enviarPedido(
    pedidoId: number
  ): Observable<PedidoCompra> {

    return this.http.post<PedidoCompra>(
      `${this.apiUrl}/${pedidoId}/enviar`,
      {}
    );

  }


  cancelarPedido(
    pedidoId: number
  ): Observable<PedidoCompra> {

    return this.http.post<PedidoCompra>(
      `${this.apiUrl}/${pedidoId}/cancelar`,
      {}
    );

  }


  recibirPedido(
    pedidoId: number,
    datos: RecepcionPedido
  ): Observable<PedidoCompra> {

    return this.http.post<PedidoCompra>(
      `${this.apiUrl}/${pedidoId}/recibir`,
      datos
    );

  }


  getPdf(
    pedidoId: number
  ): Observable<Blob> {

    return this.http.get(
      `${this.apiUrl}/${pedidoId}/pdf`,
      {
        responseType: 'blob'
      }
    );

  }

  generarDesdeReposicion() {

  return this.http.post<
    PedidoCompra[]
  >(
    `${this.apiUrl}/generar-desde-reposicion`,
    {}
  );
  }

  
}
