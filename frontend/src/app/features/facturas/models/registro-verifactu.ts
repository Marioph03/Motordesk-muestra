export interface RegistroVerifactu {
  id: number;
  factura_id: number;
  tipo_registro: 'ALTA' | 'ANULACION';
  estado: string;
  hash_registro: string;
  hash_anterior?: string | null;
  factura_anterior_numero?: string | null;
  factura_anterior_fecha?: string | null;
  codigo_respuesta?: string | null;
  mensaje_error?: string | null;
  intentos_envio: number;
  fecha_generacion: string;
  fecha_ultimo_intento?: string | null;
  fecha_aceptacion?: string | null;
  created_at: string;
}
/** Estado y evidencia de un registro fiscal relacionado con una factura. */
