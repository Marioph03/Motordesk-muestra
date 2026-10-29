import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { API_URL } from '../../../core/tokens/api.token';
import { OrdenInterna, LineaOrdenInterna } from '../models/orden-interna';
@Injectable({ providedIn: 'root' })
export class OrdenesInternasService {
  private readonly http = inject(HttpClient); private readonly url = `${inject(API_URL)}/ordenes-internas`;
  listar() { return this.http.get<OrdenInterna[]>(this.url); }
  obtener(id: number) { return this.http.get<OrdenInterna>(`${this.url}/${id}`); }
  crear(datos: { titulo: string; categoria: string; vehiculo_id?: number | null; referencia_activo?: string | null; descripcion: string; responsable_id?: number | null }) { return this.http.post<OrdenInterna>(this.url, datos); }
  anadirLinea(id: number, datos: { tipo: string; articulo_stock_id?: number | null; descripcion: string; cantidad: number; coste_unitario: number }) { return this.http.post<LineaOrdenInterna>(`${this.url}/${id}/lineas`, datos); }
  borrarLinea(id: number, lineaId: number) { return this.http.delete(`${this.url}/${id}/lineas/${lineaId}`); }
  cerrar(id: number) { return this.http.post<OrdenInterna>(`${this.url}/${id}/cerrar`, {}); }
  pdf(id: number) { return this.http.get(`${this.url}/${id}/pdf`, { responseType: 'blob' }); }
}
