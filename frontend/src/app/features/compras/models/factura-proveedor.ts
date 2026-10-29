export interface AlbaranFacturaProveedor {
  id: number;
  numero_interno: string;
  numero_proveedor?: string | null;
  fecha: string;
}

export interface FacturaProveedor {
  id: number;
  proveedor_id: number;
  numero_factura: string;
  tipo_gasto: 'COMPRA' | 'SUMINISTRO' | 'REPARACION' | 'OTRO';
  fecha_factura: string;
  fecha_vencimiento?: string | null;
  base_imponible: number;
  porcentaje_iva: number;
  iva: number;
  porcentaje_retencion: number;
  retencion_irpf: number;
  total: number;
  estado_pago: 'PENDIENTE' | 'PAGADA';
  fecha_pago?: string | null;
  archivo_pdf?: string | null;
  observaciones?: string | null;
  created_at: string;
  albaranes: AlbaranFacturaProveedor[];
}

export interface CrearFacturaProveedor {
  proveedor_id: number;
  numero_factura: string;
  tipo_gasto: 'COMPRA' | 'SUMINISTRO' | 'REPARACION' | 'OTRO';
  fecha_factura: string;
  fecha_vencimiento?: string | null;
  base_imponible: number;
  porcentaje_iva: number;
  porcentaje_retencion: number;
  observaciones?: string | null;
  albaranes_ids: number[];
}
/** Factura recibida del proveedor, albaranes asociados y estado de pago. */
