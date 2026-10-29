export interface ArticuloStock {
  id: number;

  referencia: string;
  nombre: string;

  descripcion?: string | null;
  marca?: string | null;
  categoria?: string | null;
  ubicacion?: string | null;

  coste: number;
  precio_venta: number;
  iva: number;

  stock_actual: number;
  stock_minimo: number;

  activo: boolean;
  controla_stock: boolean;

  proveedor_habitual_id?: number | null;

  created_at: string;
  updated_at: string;
}
/** Artículo de almacén, sus precios, existencias y umbrales de reposición. */
