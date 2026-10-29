export interface RecepcionLineaPedido {
  linea_id: number;
  cantidad: number;
}

export interface RecepcionPedido {
  lineas: RecepcionLineaPedido[];
  observaciones?: string | null;
}
/** Cantidades seleccionadas para registrar una recepción parcial o total. */
