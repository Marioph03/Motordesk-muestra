import { Orden } from './../../ordenes/models/orden';
import { Cliente } from '../../clientes/models/cliente';
import { Vehiculo } from '../../vehiculos/models/vehiculo';

import { FacturaLinea } from './factura-linea';


export interface Factura {

  id: number;

  numero: string;

  tipo_documento: string;

  tipo_factura: string;

  estado: string;

  estado_cobro?: string;

  cliente_id: number;

  vehiculo_id?: number;

  orden_id?: number;

  subtotal: number;

  descuento_porcentaje: number;

  base_imponible: number;

  iva: number;

  cuota_iva: number;

  total: number;

  observaciones?: string;

  fecha_emision: string;

  created_at: string;

  updated_at?: string;

  // Control fiscal: las facturas de prueba pueden eliminarse aunque se hayan
  // emitido, ya que no pertenecen a VERI*FACTU.
  es_prueba?: boolean;
  modo_facturacion?: 'PRUEBAS' | 'VERIFACTU' | string | null;

  // Relaciones

  cliente: Cliente;

  vehiculo?: Vehiculo;

  orden?: Orden;

  lineas: FacturaLinea[];

}
/** Factura comercial con estado, importes, cobros y trazabilidad fiscal asociada. */
