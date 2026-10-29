export interface FacturaeDestino {
  id: number;
  factura_id: number;
  nombre: string;
  nif: string;
  direccion?: string | null;
  codigo_postal?: string | null;
  ciudad?: string | null;
  provincia?: string | null;
  oficina_contable: string;
  organo_gestor: string;
  unidad_tramitadora: string;
  expediente?: string | null;
  referencia_contrato?: string | null;
  referencia_receptor?: string | null;
  observaciones?: string | null;
  created_at: string;
  updated_at: string;
}

export type FacturaeDestinoUpdate = Omit<FacturaeDestino, 'id' | 'factura_id' | 'created_at' | 'updated_at'>;
