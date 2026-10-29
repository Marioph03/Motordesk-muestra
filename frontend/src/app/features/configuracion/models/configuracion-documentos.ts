export interface ConfiguracionDocumentos {
  id: number;

  mostrar_telefono: boolean;
  mostrar_email: boolean;
  mostrar_direccion: boolean;
  mostrar_nif_cif: boolean;
  mostrar_web: boolean;
  iban_cobros?: string | null;

  validez_presupuesto_dias: number;

  pie_documentos?: string | null;
  observaciones_presupuesto?: string | null;
  observaciones_orden?: string | null;
  observaciones_pedido_compra?: string | null;
}
/** Preferencias visibles y textos por defecto aplicables a documentos del taller. */
