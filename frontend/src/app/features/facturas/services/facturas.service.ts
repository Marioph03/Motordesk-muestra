import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';

import { Observable } from 'rxjs';

import { API_URL } from '../../../core/tokens/api.token';

import { Factura } from '../models/factura';
import { FacturaCreate } from '../models/factura-create';
import { FacturaPage } from '../models/factura-page';
import { RegistroVerifactu } from '../models/registro-verifactu';
import { FacturaeDestino, FacturaeDestinoUpdate } from '../models/facturae-destino';
import { FacturaeOrganismo } from '../models/facturae-organismo';
import { FacturaFilter } from '../models/factura-filter';

@Injectable({
  providedIn: 'root'
})
export class FacturasService {

  private http = inject(HttpClient);

  private apiUrl = inject(API_URL);

  getFacturas(
    page: number = 1,
    size: number = 10,
    filtro: FacturaFilter = {}
  ): Observable<FacturaPage> {

    let params = new HttpParams()
      .set('page', Math.max(1, page))
      .set('size', size);

    Object.entries(filtro).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        params = params.set(key, value);
      }
    });

    return this.http.get<FacturaPage>(
      `${this.apiUrl}/facturas/`,
      {
        params
      }
    );

  }

  getFactura(
    id: number
  ) {

    return this.http.get<Factura>(
      `${this.apiUrl}/facturas/${id}`
    );

  }

  getFacturaPorOrden(
    ordenId: number
  ): Observable<Factura> {

    return this.http.get<Factura>(
      `${this.apiUrl}/facturas/orden/${ordenId}`
    );

  }

  createFactura(
    factura: FacturaCreate
  ) {

    return this.http.post<Factura>(
      `${this.apiUrl}/facturas/`,
      factura
    );

  }

  updateFactura(
    id: number,
    factura: Partial<FacturaCreate>
  ) {

    return this.http.patch<Factura>(
      `${this.apiUrl}/facturas/${id}`,
      factura
    );

  }

  deleteFactura(
    id: number
  ) {

    return this.http.delete(
      `${this.apiUrl}/facturas/${id}`
    );

  }

  emitirFactura(
    id: number
  ) {

    return this.http.post<Factura>(
      `${this.apiUrl}/facturas/${id}/emitir`,
      {}
    );

  }

  anularFactura(
    id: number
  ) {

    return this.http.post<Factura>(
      `${this.apiUrl}/facturas/${id}/anular`,
      {}
    );

  }

  enviarFacturaEmail(
    id: number
  ): Observable<{ message: string; email: string }> {

    return this.http.post<{ message: string; email: string }>(
      `${this.apiUrl}/facturas/${id}/enviar-email`,
      {}
    );

  }

  enviarFacturaWhatsApp(
    id: number
  ): Observable<{ message: string; telefono: string }> {

    return this.http.post<{ message: string; telefono: string }>(
      `${this.apiUrl}/facturas/${id}/enviar-whatsapp`,
      {}
    );

  }

  crearDesdeOrden(
  ordenId: number,
  tipoDocumento: string,
  clienteId: number
  ) {

  const params = new HttpParams()
    .set('tipo_documento', tipoDocumento)
    .set('cliente_id', clienteId);

  return this.http.post<Factura>(
    `${this.apiUrl}/facturas/desde-orden/${ordenId}`,
    {},
    {
      params
    }
  );

  }

  crearDesdeGarantia(garantiaId: number): Observable<Factura> {
    return this.http.post<Factura>(
      `${this.apiUrl}/facturas/desde-garantia/${garantiaId}`,
      {}
    );
  }

  crearDesdeAlbaranVenta(albaranVentaId: number): Observable<Factura> {
    return this.http.post<Factura>(
      `${this.apiUrl}/facturas/desde-albaran-venta/${albaranVentaId}`,
      {},
    );
  }

  crearDesdeAlbaranesVenta(albaranesVentaIds: number[]): Observable<Factura> {
    return this.http.post<Factura>(
      `${this.apiUrl}/facturas/desde-albaranes-venta`,
      { albaranes_venta_ids: albaranesVentaIds },
    );
  }

  descargarPdf(
    id: number
  ) {

    return this.http.get(
      `${this.apiUrl}/facturas/${id}/pdf`,
      {
        responseType: 'blob'
      }
    );

  }

  actualizarDesdeOrden(
  facturaId: number
  ) {

    return this.http.post<Factura>(
      `${this.apiUrl}/facturas/${facturaId}/actualizar-desde-orden`,
    {}
  );

  }

  getFacturaeDestino(id: number): Observable<FacturaeDestino> {
    return this.http.get<FacturaeDestino>(`${this.apiUrl}/facturas/${id}/facturae-destino`);
  }

  guardarFacturaeDestino(id: number, destino: FacturaeDestinoUpdate): Observable<FacturaeDestino> {
    return this.http.put<FacturaeDestino>(`${this.apiUrl}/facturas/${id}/facturae-destino`, destino);
  }

  crearDesdeOrdenes(ordenes_ids: number[], tipo_documento: string, cliente_id: number): Observable<Factura> {
    return this.http.post<Factura>(`${this.apiUrl}/facturas/desde-ordenes`, { ordenes_ids, tipo_documento, cliente_id });
  }

  getOrganismosFacturae(): Observable<FacturaeOrganismo[]> {
    return this.http.get<FacturaeOrganismo[]>(`${this.apiUrl}/facturas/facturae-organismos`);
  }

  guardarOrganismoFacturae(destino: FacturaeDestinoUpdate, id?: number): Observable<FacturaeOrganismo> {
    const url = id
      ? `${this.apiUrl}/facturas/facturae-organismos/${id}`
      : `${this.apiUrl}/facturas/facturae-organismos`;
    return id
      ? this.http.put<FacturaeOrganismo>(url, destino)
      : this.http.post<FacturaeOrganismo>(url, destino);
  }

  getRegistrosVerifactu(id: number): Observable<RegistroVerifactu[]> {
    return this.http.get<RegistroVerifactu[]>(
      `${this.apiUrl}/verifactu/facturas/${id}/registros`
    );
  }

  generarRegistroVerifactuPrueba(id: number): Observable<RegistroVerifactu> {
    return this.http.post<RegistroVerifactu>(
      `${this.apiUrl}/facturas/${id}/verifactu/generar-prueba`,
      {}
    );
  }

  generarVerifactu(
  facturaId: number
  ) {
  return this.http.post<any>(
    `${this.apiUrl.replace('/facturas', '')}/verifactu/facturas/${facturaId}/generar`,
    {}
  );
  }

  generarAnulacionVerifactu(facturaId: number) {
    return this.http.post<any>(
      `${this.apiUrl.replace('/facturas', '')}/verifactu/facturas/${facturaId}/generar-anulacion`,
      {}
    );
  }

  enviarVerifactuTest(
  registroId: number
  ) {
  return this.http.post<any>(
    `${this.apiUrl.replace('/facturas', '')}/verifactu/registros/${registroId}/enviar-test`,
    {}
  );
  }

}
/** Cliente HTTP de facturación, PDF y operaciones VERI*FACTU controladas. */
