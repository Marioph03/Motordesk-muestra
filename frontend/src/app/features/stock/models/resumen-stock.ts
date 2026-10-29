export interface ResumenStock {
  total_articulos: number;
  articulos_activos: number;
  stock_bajo: number;
  sin_stock: number;

  valor_inventario_coste: number;
  valor_inventario_venta: number;
}
/** Indicadores agregados de valor y salud operativa del almacén. */
