import { VehiculoSimple } from './../../vehiculos/models/vehiculo-simple';
import { VehicleDamage } from './vehicle-damage';

export interface Orden {

  id: number;

  numero: string;

  vehiculo_id: number;

  vehiculo: VehiculoSimple;

  usuarios_asignados: UsuarioOrden[];

  fecha_entrada: string;

  fecha_salida?: string;

  kilometros_entrada?: number | null;

  estado: string;

  fecha_envio_presupuesto?: string | null;

  canal_envio_presupuesto?: 'EMAIL' | 'WHATSAPP' | null;

  fecha_respuesta_presupuesto?: string | null;

  resolucion_garantia?: string | null;

  descripcion_averia: string;

  diagnostico?: string;

  observaciones?: string;

  observaciones_internas?: string;

  total_mano_obra: number;

  total_piezas: number;

  subtotal: number;

  descuento_porcentaje: number;

  base_imponible: number;

  iva: number;

  importe_total: number;

  coste_asumido_taller?: number;
  trabajos_no_cubiertos?: number;
  iva_cliente_garantia?: number;
  total_cliente_garantia?: number;

  tipo: string;

  presupuesto_origen_id?: number | null;

  orden_origen_garantia_id?: number | null;

  factura_origen_garantia_id?: number | null;

  garantia: boolean;

  garantia_meses?: number;

  vehicle_damage?: VehicleDamage;

}

export interface UsuarioOrden {
  id: number;
  nombre: string;
  apellidos: string;
  rol: string;
}
/** Orden de reparación completa, con relaciones y estado operativo actual. */
