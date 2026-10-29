export interface ArticuloStockCreate {
  referencia: string;
  nombre: string;

  descripcion?: string | null;
  marca?: string | null;
  categoria?: string | null;
  ubicacion?: string | null;

  coste: number;
  precio_venta: number;
  iva: number;

  stock_inicial: number;
  stock_minimo: number;

  activo: boolean;
  controla_stock: boolean;

  proveedor_habitual_id?: number | null;
}
/** Datos iniciales de un artículo, incluido stock de apertura trazable. */
