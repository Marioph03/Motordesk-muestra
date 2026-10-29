import { Cliente } from '../../clientes/models/cliente';

export interface LineaAlbaranVenta {
  id: number;
  articulo_stock_id: number;
  referencia: string;
  descripcion: string;
  cantidad: number;
  precio_unitario: number;
  descuento_porcentaje: number;
  total: number;
}

export interface AlbaranVenta {
  id: number;
  numero: string;
  cliente_id: number;
  cliente: Cliente;
  fecha: string;
  estado: 'BORRADOR' | 'CONFIRMADO' | 'ANULADO';
  factura_id: number | null;
  observaciones: string | null;
  total: number;
  lineas: LineaAlbaranVenta[];
}

export interface AlbaranVentaCreate {
  cliente_id: number;
  fecha: string;
  observaciones?: string | null;
  lineas: Array<{
    articulo_stock_id: number;
    cantidad: number;
    precio_unitario?: number | null;
    descuento_porcentaje: number;
  }>;
}
