export interface LineaDevolucionProveedor {
  id: number;
  linea_albaran_id: number;
  articulo_stock_id: number;
  cantidad: number;
}

export interface DevolucionProveedor {
  id: number;
  numero: string;
  proveedor_id: number;
  albaran_origen_id: number;
  estado: 'BORRADOR' | 'CONFIRMADA' | 'ANULADA';
  resolucion: 'PENDIENTE' | 'ABONO' | 'SUSTITUCION' | 'RECHAZADA';
  motivo: string;
  observaciones?: string | null;
  fecha: string;
  lineas: LineaDevolucionProveedor[];
}

export interface CrearDevolucionProveedor {
  proveedor_id: number;
  albaran_origen_id: number;
  motivo: string;
  observaciones?: string | null;
  lineas: Array<{
    linea_albaran_id: number;
    articulo_stock_id: number;
    cantidad: number;
  }>;
}
/** Documento de devolución de mercancía y sus cantidades por línea. */
