export interface ArticuloStockUpdate {
  referencia?: string;
  nombre?: string;

  descripcion?: string | null;
  marca?: string | null;
  categoria?: string | null;
  ubicacion?: string | null;

  coste?: number;
  precio_venta?: number;
  iva?: number;

  stock_minimo?: number;

  activo?: boolean;
  controla_stock?: boolean;

  proveedor_habitual_id?: number | null;
}
/** Campos de catálogo editables sin modificar stock directamente. */
