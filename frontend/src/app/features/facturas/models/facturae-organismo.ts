import { FacturaeDestinoUpdate } from './facturae-destino';

export interface FacturaeOrganismo extends FacturaeDestinoUpdate {
  id: number;
  created_at: string;
  updated_at: string;
}
