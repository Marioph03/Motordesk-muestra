export interface TrabajoFrecuenteInforme {
  descripcion: string;
  total: number;
}

export interface ResumenOrdenesInforme {
  total: number;
  cerradas: number;
  facturadas: number;
  garantias: number;
  presupuestos: number;
  en_curso: number;
  trabajos_frecuentes: TrabajoFrecuenteInforme[];
}

export interface FacturacionDiaInforme {
  fecha: string;
  total: number;
}

export interface ResumenFacturacionInforme {
  facturas_emitidas: number;
  facturas_anuladas: number;
  total_facturado: number;
  ticket_medio: number;
  evolucion_diaria: FacturacionDiaInforme[];
}

export interface ArticuloConsumidoInforme {
  articulo_id: number;
  referencia: string;
  nombre: string;
  cantidad_consumida: number;
}

export interface ResumenStockInforme {
  movimientos: number;
  unidades_consumidas: number;
  entradas_compra: number;
  ajustes_positivos: number;
  ajustes_negativos: number;
  articulos_mas_consumidos: ArticuloConsumidoInforme[];
}

export interface ProveedorCompraInforme {
  proveedor_id: number;
  nombre: string;
  pedidos: number;
  total_compras: number;
}

export interface ResumenComprasInforme {
  pedidos: number;
  recibidos: number;
  recibidos_parciales: number;
  cancelados: number;
  total_compras: number;
  ticket_medio: number;
  proveedores_top: ProveedorCompraInforme[];
}

export interface ResumenIvaInforme {
  iva_repercutido: number;
  iva_soportado: number;
  diferencia: number;
}

export interface ResumenGarantiasInforme {
  total: number;
  abiertas: number;
  en_revision: number;
  aprobadas: number;
  rechazadas: number;
  en_reparacion: number;
  resueltas: number;
  tiempo_medio_resolucion_horas: number;
  tiempo_medio_resolucion_dias: number;
}

export interface PersonalUsuarioInforme {
  usuario_id: number;
  nombre: string;
  rol: string;
  ordenes_asignadas: number;
  citas_asignadas: number;
  ausencias: number;
  dias_ausencia: number;
  actividad_total: number;
}

export interface ResumenPersonalInforme {
  usuarios_activos: number;
  detalle: PersonalUsuarioInforme[];
}

export interface InformeGeneral {
  fecha_inicio: string;
  fecha_fin: string;
  ordenes: ResumenOrdenesInforme;
  facturacion: ResumenFacturacionInforme;
  stock: ResumenStockInforme;
  compras: ResumenComprasInforme;
  iva: ResumenIvaInforme;
  garantias: ResumenGarantiasInforme;
  personal: ResumenPersonalInforme;
}
/** Estructura completa del informe agregado devuelto por el backend. */
