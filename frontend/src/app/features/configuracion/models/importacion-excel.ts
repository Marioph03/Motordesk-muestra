export interface HojaExcel { nombre: string; filas: number; columnas: number; }
export interface ColumnaExcel { indice: number; nombre: string; }
export interface AnalisisExcel {
  archivo: string;
  hojas: HojaExcel[];
  hoja_activa: string;
  columnas: ColumnaExcel[];
  total_filas: number;
  muestra: Record<string, unknown>[];
}

export interface CampoImportacion {
  campo: string;
  label: string;
  obligatorio: boolean;
}

export interface CamposImportacionResponse {
  tipo: string;
  campos: CampoImportacion[];
}

export interface MapeoCampo {
  campo_motordesk: string;
  columna_excel: string | null;
}

export interface FilaPreviewImportacion {
  numero_fila: number;
  datos: Record<string, unknown>;
  valida: boolean;
  duplicado: boolean;
  errores: string[];
  advertencias: string[];
}

export interface PreviewImportacion {
  total: number;
  validas: number;
  errores: number;
  advertencias: number;
  duplicados: number;
  filas: FilaPreviewImportacion[];
}

export interface ResultadoImportacion {
  total: number;
  importados: number;
  omitidos: number;
  errores: number;
  detalle_errores: string[];
}
/** Resultado de análisis y mapeo de columnas para migrar datos desde Excel. */
