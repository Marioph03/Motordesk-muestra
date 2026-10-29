export interface LineaAlbaranProveedor {
  id: number;
  articulo_stock_id: number;
  cantidad_recibida: number;
  coste_unitario?: number | null;
}

export interface LineaAlbaranDevolvible {
  linea_albaran_id: number;
  articulo_stock_id: number;
  cantidad_recibida: number;
  cantidad_devuelta: number;
  cantidad_disponible: number;
  coste_unitario?: number | null;
  articulo: {
    id: number;
    referencia?: string | null;
    nombre?: string | null;
    descripcion?: string | null;
  };
}

export interface AlbaranProveedor {
  id: number;
  numero_interno: string;
  numero_proveedor?: string | null;
  proveedor_id: number;
  pedido_compra_id?: number | null;
  fecha: string;
  estado: 'BORRADOR' | 'CONFIRMADO' | 'ANULADO';
  observaciones?: string | null;
  lineas: LineaAlbaranProveedor[];
}

export interface CrearLineaAlbaranProveedor {
  articulo_stock_id: number;
  cantidad_recibida: number;
  coste_unitario?: number | null;
}

export interface CrearAlbaranProveedor {
  numero_proveedor?: string | null;
  proveedor_id: number;
  pedido_compra_id?: number | null;
  fecha: string;
  observaciones?: string | null;
  lineas: CrearLineaAlbaranProveedor[];
}
/** Albarán recibido de proveedor, sus líneas y estado de confirmación. */
