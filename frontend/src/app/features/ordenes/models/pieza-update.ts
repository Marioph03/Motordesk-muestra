export interface PiezaUpdate {

  descripcion?: string | null;

  cantidad?: number | null;

  precio_unitario?: number | null;

  proveedor_id?: number | null;

  articulo_stock_id?: number | null;

  referencia?: string | null;

}
/** Cambios permitidos sobre una pieza antes de cerrar o facturar la orden. */
