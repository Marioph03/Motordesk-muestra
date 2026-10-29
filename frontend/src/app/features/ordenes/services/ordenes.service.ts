import { HttpClient, HttpParams } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { Observable } from 'rxjs';

import { API_URL } from '../../../core/tokens/api.token';

import { Orden } from '../models/orden';
import { OrdenCreate } from '../models/orden-create';
import { OrdenPage } from '../models/orden-page';
import { OrdenUpdate } from '../models/orden-update';
import { ArchivoOrden } from '../models/archivo-orden';

@Injectable({
  providedIn: 'root'
})
export class OrdenesService {

  private http = inject(HttpClient);

  private apiUrl = inject(API_URL);

  getOrdenes(
    page: number = 1,
    size: number = 10,
    q: string = '',
    tipo?: 'OR' | 'PR',
    estado?: string
  ): Observable<OrdenPage> {

    let params = new HttpParams()
      .set('page', Math.max(1, page))
      .set('size', size);

    if (q.trim()) {
      params = params.set('q', q.trim());
    }

    if (tipo) {
      params = params.set('tipo', tipo);
    }

    if (estado) {
      params = params.set('estado', estado);
    }

    return this.http.get<OrdenPage>(
      `${this.apiUrl}/ordenes-reparacion/`,
      { params }
    );

  }

  getOrden(id: number): Observable<Orden> {

    return this.http.get<Orden>(
      `${this.apiUrl}/ordenes-reparacion/${id}`
    );

  }

  createOrden(
    orden: OrdenCreate
  ): Observable<Orden> {

    return this.http.post<Orden>(
      `${this.apiUrl}/ordenes-reparacion/`,
      orden
    );

  }

  updateOrden(
    id: number,
    orden: OrdenUpdate
  ): Observable<Orden> {

    return this.http.patch<Orden>(
      `${this.apiUrl}/ordenes-reparacion/${id}`,
      orden
    );

  }

  deleteOrden(
    id: number
  ): Observable<void> {

    return this.http.delete<void>(
      `${this.apiUrl}/ordenes-reparacion/${id}`
    );

  }

  getOrdenPdf(
    id: number
  ): Observable<Blob> {

    return this.http.get(
      `${this.apiUrl}/ordenes-reparacion/${id}/pdf`,
      {
        responseType: 'blob'
      }
    );

  }


  enviarOrdenEmail(
  id: number
  ): Observable<{ message: string; email: string }> {

  return this.http.post<{
    message: string;
    email: string;
  }>(
    `${this.apiUrl}/ordenes-reparacion/${id}/enviar-email`,
    {}
  );

  }

  enviarOrdenWhatsApp(
  id: number
  ): Observable<{
  message: string;
  telefono: string;
  }> {

  return this.http.post<{
    message: string;
    telefono: string;
  }>(
    `${this.apiUrl}/ordenes-reparacion/${id}/enviar-whatsapp`,
    {}
  );

  }

  getArchivos(
  ordenId: number
  ): Observable<ArchivoOrden[]> {

  return this.http.get<ArchivoOrden[]>(
    `${this.apiUrl}/ordenes-reparacion/${ordenId}/archivos/`
  );

  }


  subirArchivo(
  ordenId: number,
  archivo: File,
  categoria: string
  ): Observable<ArchivoOrden> {

  const formData = new FormData();

  formData.append(
    'archivo',
    archivo
  );

  formData.append(
    'categoria',
    categoria
  );

  return this.http.post<ArchivoOrden>(
    `${this.apiUrl}/ordenes-reparacion/${ordenId}/archivos/`,
    formData
  );

  }


  descargarArchivo(
  ordenId: number,
  archivoId: number
  ): Observable<Blob> {

  return this.http.get(
    `${this.apiUrl}/ordenes-reparacion/${ordenId}/archivos/${archivoId}/descargar`,
    {
      responseType: 'blob'
    }
  );

  }


  eliminarArchivo(
  ordenId: number,
  archivoId: number
  ): Observable<void> {

  return this.http.delete<void>(
    `${this.apiUrl}/ordenes-reparacion/${ordenId}/archivos/${archivoId}`
  );

  }

  convertirPresupuestoEnOrden(
  presupuestoId: number
  ): Observable<Orden> {
  return this.http.post<Orden>(
    `${this.apiUrl}/ordenes-reparacion/${presupuestoId}/convertir-en-orden`,
    {}
  );
  }

  anularOrden(id: number): Observable<Orden> {
    return this.http.post<Orden>(`${this.apiUrl}/ordenes-reparacion/${id}/anular`, {});
  }

  getOrdenGeneradaDesdePresupuesto(
    presupuestoId: number
  ): Observable<Orden> {
    return this.http.get<Orden>(
      `${this.apiUrl}/ordenes-reparacion/${presupuestoId}/orden-generada`
    );
  }

  enviarPresupuesto(id: number): Observable<Orden> {
    return this.http.post<Orden>(
      `${this.apiUrl}/ordenes-reparacion/${id}/enviar`, {}
    );
  }

  aceptarPresupuesto(id: number): Observable<Orden> {
    return this.http.post<Orden>(
      `${this.apiUrl}/ordenes-reparacion/${id}/aceptar`, {}
    );
  }

  rechazarPresupuesto(id: number): Observable<Orden> {
    return this.http.post<Orden>(
      `${this.apiUrl}/ordenes-reparacion/${id}/rechazar`, {}
    );
  }

  iniciarRevisionGarantia(id: number): Observable<Orden> {
    return this.http.post<Orden>(`${this.apiUrl}/ordenes-reparacion/${id}/garantia/iniciar-revision`, {});
  }

  crearGarantiaDesdeOrden(id: number): Observable<Orden> {
    return this.http.post<Orden>(`${this.apiUrl}/ordenes-reparacion/${id}/crear-garantia`, {});
  }

  crearGarantiaDesdeFactura(id: number): Observable<Orden> {
    return this.http.post<Orden>(`${this.apiUrl}/ordenes-reparacion/garantias/desde-factura/${id}`, {});
  }

  aprobarGarantia(id: number): Observable<Orden> {
    return this.http.post<Orden>(`${this.apiUrl}/ordenes-reparacion/${id}/garantia/aprobar`, {});
  }

  rechazarGarantia(id: number): Observable<Orden> {
    return this.http.post<Orden>(`${this.apiUrl}/ordenes-reparacion/${id}/garantia/rechazar`, {});
  }

  iniciarReparacionGarantia(id: number): Observable<Orden> {
    return this.http.post<Orden>(`${this.apiUrl}/ordenes-reparacion/${id}/garantia/iniciar-reparacion`, {});
  }

  resolverGarantia(id: number, resolucion: string): Observable<Orden> {
    return this.http.post<Orden>(
      `${this.apiUrl}/ordenes-reparacion/${id}/garantia/resolver`,
      { resolucion }
    );
  }

}
/** Cliente HTTP del ciclo de vida de órdenes, presupuestos y garantías. */
