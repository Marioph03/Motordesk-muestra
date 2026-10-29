export interface ProveedorPedido {
  id: number;
  nombre: string;
  cif: string;

  telefono?: string | null;
  email?: string | null;
}


export interface LineaPedidoCompra {
  id: number;

  pedido_id: number;
  articulo_stock_id?: number | null;

  referencia: string;
  descripcion: string;

  cantidad_pedida: number;
  cantidad_recibida: number;

  coste_unitario: number;
  iva: number;

  subtotal: number;
  iva_importe: number;
  total: number;
}


export interface PedidoCompra {
  id: number;

  numero: string;
  proveedor_id: number;

  estado: string;

  fecha: string;

  fecha_envio?: string | null;
  fecha_recepcion?: string | null;

  observaciones?: string | null;

  subtotal: number;
  iva_total: number;
  total: number;

  created_at: string;
  updated_at: string;

  proveedor: ProveedorPedido;

  lineas: LineaPedidoCompra[];
}
/** Pedido de proveedor con líneas, totales y avance de recepción. */
