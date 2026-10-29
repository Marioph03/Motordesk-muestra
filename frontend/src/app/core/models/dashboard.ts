export interface DashboardResponse {

  clientes: number;

  vehiculos: number;

  ordenes_abiertas: number;

  ordenes_cerradas: number;

  facturacion_mes: number;

  facturacion_anual: number;

  facturacion_ultimos_meses: DashboardFacturacionMes[];

  presupuestos: number;
  stock_actual: number;
  stock_bajo: number;
  citas_hoy: number;
  cobros_pendientes: number;
  facturas: number;
  alertas: DashboardAlerta[];

  ultimas_facturas: DashboardFactura[];
  ultimas_ordenes: DashboardOrden[];

}

export interface DashboardAlerta {
  tipo: string;
  titulo: string;
  mensaje: string;
  cantidad: number;
  ruta: string;
}

export interface DashboardFacturacionMes {
  periodo: string;
  etiqueta: string;
  total: number;
}

export interface DashboardFactura {
  id: number;
  numero: string;
  estado: string;
  total: number;
  fecha_emision: string;
  cliente?: { nombre: string; apellidos?: string | null };
}

export interface DashboardOrden {
  id: number;
  numero: string;
  estado: string;
  fecha_entrada: string;
  descripcion_averia: string;
  importe_total: number;
  vehiculo?: { marca: string; modelo: string; matricula: string };
}
/** Contrato de indicadores y alertas devuelto para el Dashboard operativo. */
