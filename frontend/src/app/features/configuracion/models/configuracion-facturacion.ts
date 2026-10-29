export type ModoFacturacion = 'PRUEBAS' | 'VERIFACTU';

export interface ConfiguracionFacturacion {
  id: number;
  modo_facturacion: ModoFacturacion;
  serie_pruebas: string;
  serie_facturas: string;
  permitir_envio_aeat: boolean;
}

export type ConfiguracionFacturacionUpdate = Omit<ConfiguracionFacturacion, 'id'>;
/** Configuración fiscal del frontend para pruebas, series y VERI*FACTU. */
