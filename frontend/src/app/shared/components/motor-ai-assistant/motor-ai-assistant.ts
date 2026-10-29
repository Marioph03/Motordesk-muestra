import {
  AfterViewChecked,
  ChangeDetectorRef,
  Component,
  ElementRef,
  ViewChild,
  inject
} from '@angular/core';

import {
  CommonModule
} from '@angular/common';

import {
  FormsModule
} from '@angular/forms';

import {
  MatButtonModule
} from '@angular/material/button';

import {
  MatIconModule
} from '@angular/material/icon';

import {
  MatProgressSpinnerModule
} from '@angular/material/progress-spinner';

import {
  MotorAIService
} from '../../../core/services/motor-ai.service';

import {
  MotorAIMessage
} from '../../../core/models/motor-ai';


@Component({
  selector: 'app-motor-ai-assistant',

  standalone: true,

  imports: [
    CommonModule,
    FormsModule,

    MatButtonModule,
    MatIconModule,
    MatProgressSpinnerModule
  ],

  templateUrl:
    './motor-ai-assistant.html',

  styleUrl:
    './motor-ai-assistant.scss'
})
export class MotorAIAssistant
implements AfterViewChecked {

  private readonly motorAIService =
    inject(MotorAIService);

  private readonly changeDetector =
    inject(ChangeDetectorRef);


  @ViewChild(
    'messagesContainer'
  )
  messagesContainer?:
    ElementRef<HTMLDivElement>;


  abierto = false;

  enviando = false;

  mensaje = '';

  private contadorMensajes = 0;

  private debeHacerScroll = false;


  mensajes: MotorAIMessage[] = [

    {
      id: ++this.contadorMensajes,

      rol: 'asistente',

      contenido:
        'Hola, soy MotorDesk AI. '
        +
        '¿En qué puedo ayudarte?',

      fecha: new Date()
    }

  ];


  sugerencias = [

    '¿Cuántas órdenes tenemos abiertas?',

    '¿Cuánto hemos facturado este mes?',

    'Busca un cliente',

    'Busca un vehículo'

  ];


  ngAfterViewChecked(): void {

    if (
      this.debeHacerScroll
    ) {

      this.scrollAbajo();

      this.debeHacerScroll =
        false;

    }

  }


  toggle(): void {

    this.abierto =
      !this.abierto;


    if (
      this.abierto
    ) {

      this.debeHacerScroll =
        true;

    }

  }


  cerrar(): void {

    this.abierto =
      false;

  }


  usarSugerencia(
    texto: string
  ): void {

    if (
      this.enviando
    ) {
      return;
    }


    this.mensaje =
      texto;

    this.enviar();

  }


  enviar(): void {

    const texto =
      this.mensaje
        .trim();


    if (
      !texto
      ||
      this.enviando
    ) {

      return;

    }


    this.mensajes.push({

      id:
        ++this.contadorMensajes,

      rol:
        'usuario',

      contenido:
        texto,

      fecha:
        new Date()

    });


    this.mensaje =
      '';


    this.enviando =
      true;


    this.debeHacerScroll =
      true;


    this.motorAIService
      .chat(texto)
      .subscribe({

        next: respuesta => {

          this.mensajes.push({

            id:
              ++this.contadorMensajes,

            rol:
              'asistente',

            contenido:
              respuesta.respuesta,

            fecha:
              new Date(),

            accion:
              respuesta.accion_pendiente
              ?? null,

            workflow:
              respuesta.workflow_pendiente
              ?? null

          });


          this.enviando =
            false;

          this.debeHacerScroll =
            true;

          // En el modo zoneless de Angular una respuesta HTTP no siempre
          // provoca un refresco automático de esta vista.
          this.changeDetector.markForCheck();

        },


        error: err => {

          console.error(
            'Error MotorDesk AI:',
            err
          );


          let mensajeError =
            (
              'MotorDesk AI no está '
              +
              'disponible en este momento.'
            );


          if (
            err?.status === 503
          ) {

            mensajeError =
              (
                'MotorDesk AI está '
                +
                'temporalmente ocupado. '
                +
                'Inténtalo de nuevo '
                +
                'en unos segundos.'
              );

          }


          if (
            err?.status === 401
            ||
            err?.status === 403
          ) {

            mensajeError =
              (
                'Tu sesión no permite '
                +
                'utilizar MotorDesk AI.'
              );

          }


          if (
            err?.error?.detail
          ) {

            mensajeError =
              err.error.detail;

          }


          this.mensajes.push({

            id:
              ++this.contadorMensajes,

            rol:
              'asistente',

            contenido:
              mensajeError,

            fecha:
              new Date(),

            error:
              true

          });


          this.enviando =
            false;

          this.debeHacerScroll =
            true;

          this.changeDetector.markForCheck();

        }

      });

  }


  confirmarAccion(
    mensaje: MotorAIMessage
  ): void {

    const accion = mensaje.accion;

    if (!accion || this.enviando) {
      return;
    }

    this.enviando = true;

    this.motorAIService
      .confirmarAccion(accion.id)
      .subscribe({
        next: resultado => {
          mensaje.accion = null;
          this.añadirRespuestaAccion(resultado.mensaje, !resultado.ok);
          this.enviando = false;
          this.debeHacerScroll = true;
          this.changeDetector.markForCheck();
        },
        error: err => {
          this.enviando = false;
          this.añadirRespuestaAccion(
            err?.error?.detail
            ?? 'No se ha podido confirmar la acción.',
            true
          );
          this.debeHacerScroll = true;
          this.changeDetector.markForCheck();
        }
      });

  }


  cancelarAccion(
    mensaje: MotorAIMessage
  ): void {

    const accion = mensaje.accion;

    if (!accion || this.enviando) {
      return;
    }

    this.enviando = true;

    this.motorAIService
      .cancelarAccion(accion.id)
      .subscribe({
        next: resultado => {
          mensaje.accion = null;
          this.añadirRespuestaAccion(resultado.mensaje, !resultado.ok);
          this.enviando = false;
          this.debeHacerScroll = true;
          this.changeDetector.markForCheck();
        },
        error: err => {
          this.enviando = false;
          this.añadirRespuestaAccion(
            err?.error?.detail
            ?? 'No se ha podido cancelar la acción.',
            true
          );
          this.debeHacerScroll = true;
          this.changeDetector.markForCheck();
        }
      });

  }


  confirmarWorkflow(
    mensaje: MotorAIMessage
  ): void {

    const workflow = mensaje.workflow;

    if (!workflow || this.enviando) {
      return;
    }

    this.enviando = true;

    this.motorAIService
      .confirmarWorkflow(workflow.id)
      .subscribe({
        next: resultado => {
          mensaje.workflow = null;
          this.agregarRespuestaAccion(resultado.mensaje, !resultado.ok);
          this.enviando = false;
          this.debeHacerScroll = true;
          this.changeDetector.markForCheck();
        },
        error: err => {
          this.enviando = false;
          this.agregarRespuestaAccion(
            err?.error?.detail
            ?? 'No se ha podido confirmar el workflow.',
            true
          );
          this.debeHacerScroll = true;
          this.changeDetector.markForCheck();
        }
      });

  }


  cancelarWorkflow(
    mensaje: MotorAIMessage
  ): void {

    const workflow = mensaje.workflow;

    if (!workflow || this.enviando) {
      return;
    }

    this.enviando = true;

    this.motorAIService
      .cancelarWorkflow(workflow.id)
      .subscribe({
        next: resultado => {
          mensaje.workflow = null;
          this.agregarRespuestaAccion(resultado.mensaje, !resultado.ok);
          this.enviando = false;
          this.debeHacerScroll = true;
          this.changeDetector.markForCheck();
        },
        error: err => {
          this.enviando = false;
          this.agregarRespuestaAccion(
            err?.error?.detail
            ?? 'No se ha podido cancelar el workflow.',
            true
          );
          this.debeHacerScroll = true;
          this.changeDetector.markForCheck();
        }
      });

  }


  getTituloAccion(
    tipo: string
  ): string {

    if (tipo === 'CREAR_CITA') {
      return 'Crear cita';
    }

    if (tipo === 'CREAR_ORDEN') {
      return 'Crear orden de reparación';
    }

    if (tipo === 'CREAR_CLIENTE') {
      return 'Crear cliente';
    }

    if (tipo === 'CREAR_VEHICULO') {
      return 'Crear vehículo';
    }

    return 'Acción pendiente';

  }


  getIconoAccion(
    tipo: string
  ): string {

    if (tipo === 'CREAR_CITA') {
      return 'event';
    }

    if (tipo === 'CREAR_ORDEN') {
      return 'build';
    }

    if (tipo === 'CREAR_CLIENTE') {
      return 'person_add';
    }

    if (tipo === 'CREAR_VEHICULO') {
      return 'directions_car';
    }

    return 'smart_toy';

  }


  onKeydown(
    event: KeyboardEvent
  ): void {

    if (
      event.key !== 'Enter'
    ) {
      return;
    }


    if (
      event.shiftKey
    ) {
      return;
    }


    event.preventDefault();

    this.enviar();

  }


  limpiarConversacion(): void {

    if (this.enviando) {
      return;
    }

    this.enviando = true;

    this.motorAIService
      .limpiarConversacion()
      .subscribe({
        next: () => {
          this.mensajes = [{
            id: ++this.contadorMensajes,
            rol: 'asistente',
            contenido: 'Conversación reiniciada. ¿Qué quieres consultar?',
            fecha: new Date()
          }];
          this.enviando = false;
          this.debeHacerScroll = true;
          this.changeDetector.markForCheck();
        },
        error: err => {
          this.enviando = false;
          this.agregarRespuestaAccion(
            err?.error?.detail
            ?? 'No se ha podido reiniciar la conversación.',
            true
          );
          this.debeHacerScroll = true;
          this.changeDetector.markForCheck();
        }
      });

    return;

    this.mensajes = [

      {
        id:
          ++this.contadorMensajes,

        rol:
          'asistente',

        contenido:
          (
            'Conversación reiniciada. '
            +
            '¿Qué quieres consultar?'
          ),

        fecha:
          new Date()
      }

    ];


    this.debeHacerScroll =
      true;

  }


  private añadirRespuestaAccion(
    contenido: string,
    error = false
  ): void {

    this.mensajes.push({
      id: ++this.contadorMensajes,
      rol: 'asistente',
      contenido,
      fecha: new Date(),
      error
    });

  }


  private agregarRespuestaAccion(
    contenido: string,
    error = false
  ): void {

    this.mensajes.push({
      id: ++this.contadorMensajes,
      rol: 'asistente',
      contenido,
      fecha: new Date(),
      error
    });

  }


  private scrollAbajo(): void {

    const elemento =
      this.messagesContainer
        ?.nativeElement;


    if (!elemento) {
      return;
    }


    elemento.scrollTop =
      elemento.scrollHeight;

  }

}
/**
 * Asistente global de MotorDesk AI. Las respuestas pueden incluir propuestas
 * que el usuario confirma mediante endpoints explícitos, nunca texto libre.
 */
