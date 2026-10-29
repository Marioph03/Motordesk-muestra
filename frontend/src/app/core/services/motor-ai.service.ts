import {
  inject,
  Injectable
} from '@angular/core';

import {
  HttpClient
} from '@angular/common/http';

import {
  Observable
} from 'rxjs';

import {
  MotorAIChatRequest,
  MotorAIActionResult,
  MotorAIChatResponse
} from '../models/motor-ai';
import { API_URL } from '../tokens/api.token';


@Injectable({
  providedIn: 'root'
})
export class MotorAIService {

  private readonly http =
    inject(HttpClient);


  private readonly apiUrl =
    `${inject(API_URL)}/ai`;


  chat(
    mensaje: string
  ): Observable<MotorAIChatResponse> {

    // El backend asocia la consulta al usuario del JWT; el navegador no envía
    // permisos ni identificadores de usuario como fuente de verdad.

    const datos:
      MotorAIChatRequest = {

      mensaje

    };


    return this.http.post<
      MotorAIChatResponse
    >(
      `${this.apiUrl}/chat`,
      datos
    );

  }


  confirmarAccion(
    accionId: string
  ): Observable<MotorAIActionResult> {

    // Una action solo se ejecuta tras la confirmación explícita del usuario.

    return this.http.post<MotorAIActionResult>(
      `${this.apiUrl}/actions/${accionId}/confirmar`,
      {}
    );

  }


  cancelarAccion(
    accionId: string
  ): Observable<MotorAIActionResult> {

    // Cancelar elimina una propuesta temporal: todavía no hay cambios en BD.

    return this.http.post<MotorAIActionResult>(
      `${this.apiUrl}/actions/${accionId}/cancelar`,
      {}
    );

  }


  confirmarWorkflow(
    workflowId: string
  ): Observable<MotorAIActionResult> {

    // El backend ejecuta los pasos dependientes del workflow en una transacción.

    return this.http.post<MotorAIActionResult>(
      `${this.apiUrl}/workflows/${workflowId}/confirmar`,
      {}
    );

  }


  cancelarWorkflow(
    workflowId: string
  ): Observable<MotorAIActionResult> {

    return this.http.post<MotorAIActionResult>(
      `${this.apiUrl}/workflows/${workflowId}/cancelar`,
      {}
    );

  }


  limpiarConversacion(): Observable<{
    ok: boolean;
    mensaje: string;
  }> {

    // Limpia memoria temporal del asistente, no datos del negocio ni auditorías.

    return this.http.delete<{
      ok: boolean;
      mensaje: string;
    }>(
      `${this.apiUrl}/conversation`
    );

  }

}
/** Cliente HTTP del asistente IA y de sus confirmaciones explícitas. */
