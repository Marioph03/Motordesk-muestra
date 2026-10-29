export interface MovimientoStock {
  id: number;

  articulo_id: number;

  tipo: string;
  cantidad: number;

  stock_anterior: number;
  stock_resultante: number;

  motivo?: string | null;

  orden_id?: number | null;

  fecha: string;
}
/** Movimiento trazable que explica una variación en las existencias. */
