import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';

import { Observable } from 'rxjs';

import { ArticuloStock } from '../models/articulo-stock';
import { ArticuloStockCreate } from '../models/articulo-stock-create';
import { ArticuloStockUpdate } from './../models/articulo-stock-update';

import { MovimientoStock } from '../models/movimiento-stock';
import { ResumenStock } from '../models/resumen-stock';
import { ArticuloMasConsumido } from '../models/articulo-mas-consumido';
import { API_URL } from '../../../core/tokens/api.token';


@Injectable({
  providedIn: 'root'
})
export class StockService {

  private http = inject(HttpClient);

  private apiUrl =
    `${inject(API_URL)}/stock`;


  getArticulos(controlaStock?: boolean): Observable<ArticuloStock[]> {

    let params = new HttpParams();
    if (controlaStock !== undefined) params = params.set('controla_stock', controlaStock);

    return this.http.get<ArticuloStock[]>(
      `${this.apiUrl}/articulos`, { params }
    );

  }


  getArticulo(
    articuloId: number
  ): Observable<ArticuloStock> {

    return this.http.get<ArticuloStock>(
      `${this.apiUrl}/articulos/${articuloId}`
    );

  }


  getStockBajo(): Observable<ArticuloStock[]> {

    return this.http.get<ArticuloStock[]>(
      `${this.apiUrl}/articulos/stock-bajo`
    );

  }


  crearArticulo(
    datos: ArticuloStockCreate
  ): Observable<ArticuloStock> {

    return this.http.post<ArticuloStock>(
      `${this.apiUrl}/articulos`,
      datos
    );

  }


  actualizarArticulo(
    articuloId: number,
    datos: ArticuloStockUpdate
  ): Observable<ArticuloStock> {

    return this.http.patch<ArticuloStock>(
      `${this.apiUrl}/articulos/${articuloId}`,
      datos
    );

  }


  getNecesidadesReposicion(): Observable<ArticuloStock[]> {

    return this.http.get<ArticuloStock[]>(
      `${this.apiUrl}/reposicion`
    );

  }


  getResumen(): Observable<ResumenStock> {

    return this.http.get<ResumenStock>(
      `${this.apiUrl}/resumen`
    );

  }


  getMasConsumidos(
    limite = 10
  ): Observable<ArticuloMasConsumido[]> {

    return this.http.get<ArticuloMasConsumido[]>(
      `${this.apiUrl}/mas-consumidos`,
      {
        params: { limite }
      }
    );

  }


  getTodosMovimientos(): Observable<MovimientoStock[]> {

    return this.http.get<MovimientoStock[]>(
      `${this.apiUrl}/movimientos`
    );

  }


  cambiarEstadoArticulo(
    articuloId: number,
    activo: boolean
  ): Observable<ArticuloStock> {

    return this.http.patch<ArticuloStock>(
      `${this.apiUrl}/articulos/${articuloId}/estado`,
      {},
      {
        params: { activo }
      }
    );

  }


  entrada(
    articuloId: number,
    cantidad: number,
    motivo?: string
  ): Observable<MovimientoStock> {

    return this.http.post<MovimientoStock>(
      `${this.apiUrl}/articulos/${articuloId}/entrada`,
      {
        cantidad,
        motivo
      }
    );

  }


  salida(
    articuloId: number,
    cantidad: number,
    motivo?: string
  ): Observable<MovimientoStock> {

    return this.http.post<MovimientoStock>(
      `${this.apiUrl}/articulos/${articuloId}/salida`,
      {
        cantidad,
        motivo
      }
    );

  }


  ajustePositivo(
    articuloId: number,
    cantidad: number,
    motivo: string
  ): Observable<MovimientoStock> {

    return this.http.post<MovimientoStock>(
      `${this.apiUrl}/articulos/${articuloId}/ajuste-positivo`,
      {
        cantidad,
        motivo
      }
    );

  }


  ajusteNegativo(
    articuloId: number,
    cantidad: number,
    motivo: string
  ): Observable<MovimientoStock> {

    return this.http.post<MovimientoStock>(
      `${this.apiUrl}/articulos/${articuloId}/ajuste-negativo`,
      {
        cantidad,
        motivo
      }
    );

  }


  getMovimientos(
    articuloId: number
  ): Observable<MovimientoStock[]> {

    return this.http.get<MovimientoStock[]>(
      `${this.apiUrl}/articulos/${articuloId}/movimientos`
    );

  }

}
/** Cliente HTTP de artículos, movimientos, resumen y reposición de almacén. */
