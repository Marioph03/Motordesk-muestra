export interface LineaPedidoCompraCreate {
  articulo_stock_id?: number | null;
  referencia?: string | null;
  descripcion?: string | null;

  cantidad_pedida: number;

  coste_unitario?: number | null;
  iva?: number | null;
}
/** Datos necesarios para añadir una línea a un pedido de compra. */
