import { Proveedor } from "../../proveedores/models/proveedor";

export interface Pieza {

  id: number;

  orden_id: number;

  descripcion: string;

  cantidad: number;

  precio_unitario: number;

  descuento_porcentaje?: number;

  total: number;

  proveedor_id: number | null;

  referencia: string | null;
  cubierto_garantia: boolean;
  articulo_stock_id?: number | null;
  articulo_stock?: {
    id: number;
    referencia: string;
    nombre: string;
  } | null;

}
/** Pieza de almacén reservada o consumida por una orden de reparación. */
