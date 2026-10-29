export interface PiezaCreate {

  descripcion: string | null;

  cantidad: number | null;

  precio_unitario: number | null;

  proveedor_id?: number | null;

  articulo_stock_id?: number | null;

  referencia?: string | null;
  cubierto_garantia?: boolean | null;

}
/** Datos para añadir una pieza a la orden y registrar el consumo previsto. */
