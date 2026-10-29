export interface MotorAIChatRequest {
  mensaje: string;
}

export interface MotorAIAction {
  id: string;
  tipo: string;
  resumen: string;
  datos: Record<string, unknown>;
}


export interface MotorAIActionResult {
  ok: boolean;
  mensaje: string;
  resultado?: Record<string, unknown> | null;
}

export interface MotorAIWorkflowStep {
  orden: number;
  tipo: string;
  resumen: string;
}

export interface MotorAIWorkflow {
  id: string;
  tipo: string;
  resumen: string;
  pasos: MotorAIWorkflowStep[];
}


export interface MotorAIChatResponse {
  respuesta: string;

  herramientas_usadas: string[];

  accion_pendiente?: MotorAIAction | null;

  workflow_pendiente?: MotorAIWorkflow | null;
}


export interface MotorAIMessage {
  id: number;

  rol:
    | 'usuario'
    | 'asistente';

  contenido: string;

  fecha: Date;

  error?: boolean;

  accion?: MotorAIAction | null;

  workflow?: MotorAIWorkflow | null;
}
/** Mensajes y propuestas confirmables intercambiados con MotorDesk AI. */
