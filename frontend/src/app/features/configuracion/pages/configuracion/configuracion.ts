import {
  ChangeDetectorRef,
  Component,
  inject,
  OnDestroy,
  OnInit,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatDividerModule } from '@angular/material/divider';
import { MatIconModule } from '@angular/material/icon';
import { MatIcon } from '@angular/material/icon';

import {
  WhatsAppPlantilla,
  WhatsAppService,
} from '../../../ordenes/services/whatsapp.service';


/** Portada de configuración e inicio seguro de WhatsApp Embedded Signup. */
@Component({
  selector: 'app-configuracion',
  standalone: true,
  imports: [
    CommonModule,
    MatButtonModule,
    MatCardModule,
    MatDividerModule,
    MatIconModule,
    RouterLink,
    MatIcon
  ],
  templateUrl: './configuracion.html',
  styleUrl: './configuracion.scss',
})
export class Configuracion implements OnInit, OnDestroy {

  whatsappConectado = false;
  whatsappEmbeddedSignupDisponible = false;
  conectandoWhatsApp = false;
  desconectandoWhatsApp = false;
  errorWhatsApp = '';
  configuracionMetaPendiente: string[] = [];

  // La gestión se abre bajo demanda:
  // consultar Configuración no llama a Meta.
  mostrarGestionWhatsApp = false;

  plantillasWhatsApp: WhatsAppPlantilla[] = [];
  cargandoPlantillasWhatsApp = false;
  sincronizandoPlantillasWhatsApp = false;
  creandoPlantillaWhatsApp: string | null = null;

  errorPlantillasWhatsApp: string | null = null;

  // Valores temporales que entrega Meta.
  // Nunca se persisten en el navegador.
  private whatsappOAuthCode: string | null = null;
  private whatsappWabaId: string | null = null;
  private whatsappPhoneNumberId: string | null = null;
  private whatsappConexionEnCurso = false;

  // Se entrega desde el backend solo cuando esa instalación tiene lista la
  // configuración privada de Meta. Nunca se codifica una cuenta de otro
  // taller en el frontend distribuido.
  private metaConfigId: string | null = null;
  private metaAppId: string | null = null;
  private metaSignupBridgeUrl: string | null = null;
  private whatsappRedirectUri: string | null = null;
  private whatsappBridgeNonce: string | null = null;

  private readonly origenPuenteWhatsApp = 'https://marioph03.github.io';

  private readonly whatsappService = inject(WhatsAppService);
  private readonly cdr = inject(ChangeDetectorRef);


  /**
   * Captura el evento FINISH de Meta sin aceptar
   * mensajes procedentes de otros orígenes.
   */
  private readonly listenerWhatsApp = (
    event: MessageEvent
  ): void => {

    if (event.origin === this.origenPuenteWhatsApp) {
      this.recibirResultadoPuenteWhatsApp(event.data);
      return;
    }

    if (
      event.origin !== 'https://www.facebook.com'
      && event.origin !== 'https://web.facebook.com'
      && event.origin !== 'https://business.facebook.com'
    ) {
      return;
    }

    let data = event.data;

    try {
      if (typeof data === 'string') {
        data = JSON.parse(data);
      }
    } catch {
      return;
    }

    if (data?.type !== 'WA_EMBEDDED_SIGNUP') {
      return;
    }

    if (data?.event === 'FINISH') {
      this.whatsappWabaId =
        data?.data?.waba_id ?? null;

      this.whatsappPhoneNumberId =
        data?.data?.phone_number_id ?? null;

      this.intentarCompletarConexionWhatsApp();
      return;
    }

    if (data?.event === 'ERROR' || data?.event === 'CANCEL') {
      this.whatsappConexionEnCurso = false;
      this.conectandoWhatsApp = false;
      this.errorWhatsApp = data?.data?.error_message
        ?? data?.data?.error
        ?? (data.event === 'CANCEL'
          ? 'La conexión con WhatsApp fue cancelada.'
          : 'Meta no ha podido completar la conexión con WhatsApp.');
      this.cdr.detectChanges();
    }
  };


  ngOnInit(): void {
    this.configurarListenerWhatsApp();
    this.cargarEstadoWhatsApp();
  }


  ngOnDestroy(): void {
    window.removeEventListener(
      'message',
      this.listenerWhatsApp
    );
  }


  /** Registra una sola escucha durante la vida de la pantalla. */
  private configurarListenerWhatsApp(): void {
    window.addEventListener(
      'message',
      this.listenerWhatsApp
    );
  }


  private cargarEstadoWhatsApp(): void {

    this.whatsappService.obtenerEstado().subscribe({

      next: (response) => {

        this.whatsappConectado = response.conectado;
        this.whatsappEmbeddedSignupDisponible =
          response.embedded_signup_disponible;
        this.metaConfigId = response.meta_config_id ?? null;
        this.metaAppId = response.meta_app_id ?? null;
        this.metaSignupBridgeUrl = response.meta_signup_bridge_url ?? null;
        this.configuracionMetaPendiente =
          response.configuracion_meta_pendiente ?? [];
        this.conectandoWhatsApp = false;
        this.errorWhatsApp = '';

        this.cdr.detectChanges();
      },

      error: (errorResponse) => {

        this.whatsappConectado = false;
        this.conectandoWhatsApp = false;
        this.configuracionMetaPendiente = [];

        this.errorWhatsApp =
          errorResponse?.error?.detail
          ?? 'No se pudo consultar el estado de WhatsApp.';

        this.cdr.detectChanges();
      },

    });
  }


  administrarWhatsApp(): void {

    this.mostrarGestionWhatsApp =
      !this.mostrarGestionWhatsApp;

    if (
      this.mostrarGestionWhatsApp
      && this.plantillasWhatsApp.length === 0
    ) {
      this.cargarPlantillasWhatsApp();
    }
  }

  desconectarWhatsApp(): void {
    if (
      this.desconectandoWhatsApp
      || !window.confirm(
        'Se borrará solo la conexión local de MotorDesk. La cuenta y el número seguirán en Meta. ¿Continuar?'
      )
    ) {
      return;
    }

    this.desconectandoWhatsApp = true;
    this.errorWhatsApp = '';
    this.whatsappService.desconectar().subscribe({
      next: () => {
        this.desconectandoWhatsApp = false;
        this.mostrarGestionWhatsApp = false;
        this.plantillasWhatsApp = [];
        this.cargarEstadoWhatsApp();
      },
      error: (errorResponse) => {
        this.desconectandoWhatsApp = false;
        this.errorWhatsApp = errorResponse?.error?.detail
          ?? 'No se pudo desconectar WhatsApp.';
        this.cdr.detectChanges();
      },
    });
  }


  private cargarPlantillasWhatsApp(): void {

    this.cargandoPlantillasWhatsApp = true;
    this.errorPlantillasWhatsApp = null;

    this.whatsappService.obtenerPlantillas().subscribe({

      next: (response) => {

        this.plantillasWhatsApp =
          response.plantillas ?? [];

        this.cargandoPlantillasWhatsApp = false;

        this.cdr.detectChanges();
      },

      error: (error) => {

        this.cargandoPlantillasWhatsApp = false;

        this.errorPlantillasWhatsApp =
          error?.error?.detail
          ?? 'No se han podido cargar las plantillas de WhatsApp.';

        this.cdr.detectChanges();
      },

    });
  }


  sincronizarPlantillasWhatsApp(): void {

    if (this.sincronizandoPlantillasWhatsApp) {
      return;
    }

    this.sincronizandoPlantillasWhatsApp = true;
    this.errorPlantillasWhatsApp = null;

    this.whatsappService
      .sincronizarPlantillas()
      .subscribe({

        next: (response) => {

          this.plantillasWhatsApp =
            response.plantillas ?? [];

          this.sincronizandoPlantillasWhatsApp = false;

          this.cdr.detectChanges();
        },

        error: (error) => {

          this.sincronizandoPlantillasWhatsApp = false;

          this.errorPlantillasWhatsApp =
            error?.error?.detail
            ?? 'No se han podido sincronizar las plantillas con Meta.';

          this.cdr.detectChanges();
        },

      });
  }


  /**
   * Inicia Meta Embedded Signup.
   * No usa redirecciones OAuth antiguas.
   */
  conectarWhatsApp(): void {

    const configId = this.metaConfigId;
    const appId = this.metaAppId;

    if (
      !this.whatsappEmbeddedSignupDisponible
      || !configId
      || !appId
    ) {
      this.errorWhatsApp =
        'WhatsApp Business todavía no está habilitado para esta instalación.';
      this.cdr.detectChanges();
      return;
    }

    if (!window.isSecureContext || window.location.protocol !== 'https:') {
      this.errorWhatsApp =
        'WhatsApp Business debe conectarse desde la dirección segura del '
        + 'servidor: https://localhost:8443.';
      this.cdr.detectChanges();
      return;
    }

    // Meta exige que Embedded Signup se ejecute desde un dominio público.
    // El puente es una página estática sin secretos que devuelve el resultado
    // mediante postMessage al MotorDesk local. Si aún no se ha publicado,
    // conservamos el flujo local anterior para no alterar instalaciones ya
    // configuradas.
    if (this.metaSignupBridgeUrl) {
      this.abrirPuenteWhatsApp(appId, configId);
      return;
    }

    const FB = (window as any).FB;

    if (!FB) {

      this.errorWhatsApp =
        'El SDK de Meta no está disponible.';

      this.cdr.detectChanges();

      return;
    }

    try {
      // Meta exige que el SDK se inicialice con un App ID y una versión de
      // Graph API antes de invocar FB.login.
      FB.init({
        appId,
        cookie: true,
        xfbml: false,
        version: 'v23.0',
      });
    } catch {
      this.errorWhatsApp =
        'No se ha podido inicializar el SDK de Meta. Recarga la página e inténtalo de nuevo.';
      this.cdr.detectChanges();
      return;
    }

    // Un nuevo intento no puede reutilizar
    // los resultados del intento anterior.
    this.whatsappOAuthCode = null;
    this.whatsappWabaId = null;
    this.whatsappPhoneNumberId = null;

    this.whatsappConexionEnCurso = false;

    this.errorWhatsApp = '';
    this.conectandoWhatsApp = true;

    this.cdr.detectChanges();

    FB.login(
      (response: any) => {

        const code =
          response?.authResponse?.code;

        if (!code) {

          this.conectandoWhatsApp = false;

          this.errorWhatsApp =
            'La conexión con WhatsApp fue cancelada '
            + 'o no se completó.';

          this.cdr.detectChanges();

          return;
        }

        this.whatsappOAuthCode = code;

        // FINISH puede haber llegado antes
        // o llegar después de este callback.
        this.intentarCompletarConexionWhatsApp();
      },
      {
        config_id: configId,
        auth_type: 'rerequest',
        response_type: 'code',
        override_default_response_type: true,
        extras: {
          setup: {},
          sessionInfoVersion: '3',
        },
      },
    );
  }


  /**
   * Envía al backend solo cuando Meta ha completado
   * las tres piezas necesarias.
   */
  private intentarCompletarConexionWhatsApp(): void {

    if (
      !this.whatsappOAuthCode
      || !this.whatsappWabaId
      || !this.whatsappPhoneNumberId
      || this.whatsappConexionEnCurso
    ) {
      return;
    }

    this.whatsappConexionEnCurso = true;

    this.whatsappService.conectar(
      this.whatsappOAuthCode,
      this.whatsappWabaId,
      this.whatsappPhoneNumberId,
      this.whatsappRedirectUri,
    ).subscribe({

      next: () => {

        this.whatsappConexionEnCurso = false;
        this.conectandoWhatsApp = false;

        this.whatsappOAuthCode = null;
        this.whatsappWabaId = null;
        this.whatsappPhoneNumberId = null;
        this.whatsappRedirectUri = null;
        this.whatsappBridgeNonce = null;

        this.cargarEstadoWhatsApp();
      },

      error: (errorResponse) => {

        this.whatsappConexionEnCurso = false;
        this.conectandoWhatsApp = false;

        this.errorWhatsApp =
          errorResponse?.error?.detail
          ?? 'No se pudo conectar WhatsApp Business.';

        this.cdr.detectChanges();
      },

    });
  }


  /** Abre el origen público autorizado por Meta sin exponer secretos. */
  private abrirPuenteWhatsApp(appId: string, configId: string): void {
    const bridgeUrl = this.metaSignupBridgeUrl;
    if (!bridgeUrl) {
      return;
    }

    const nonce = this.generarNonceWhatsApp();
    const url = new URL(bridgeUrl);
    url.searchParams.set('app_id', appId);
    url.searchParams.set('config_id', configId);
    url.searchParams.set('parent_origin', window.location.origin);
    url.searchParams.set('state', nonce);

    this.whatsappOAuthCode = null;
    this.whatsappWabaId = null;
    this.whatsappPhoneNumberId = null;
    // El SDK de Meta gestiona internamente su callback al ejecutarse desde el
    // puente. Enviar una redirect_uri en el canje del código obliga a que sea
    // idéntica byte a byte a la URL interna del SDK y Meta lo rechaza (36008).
    // El endpoint OAuth acepta correctamente el código del SDK sin este
    // parámetro, igual que en el flujo Embedded Signup original.
    this.whatsappRedirectUri = null;
    this.whatsappBridgeNonce = nonce;
    this.whatsappConexionEnCurso = false;
    this.errorWhatsApp = '';
    this.conectandoWhatsApp = true;
    this.cdr.detectChanges();

    const popup = window.open(
      url.toString(),
      'motordesk_whatsapp_signup',
      'popup=yes,width=680,height=780',
    );

    if (!popup) {
      this.conectandoWhatsApp = false;
      this.whatsappBridgeNonce = null;
      this.errorWhatsApp =
        'El navegador ha bloqueado la ventana de conexión con WhatsApp. '
        + 'Permite las ventanas emergentes e inténtalo de nuevo.';
      this.cdr.detectChanges();
    }
  }


  /** Acepta solo el resultado asociado al intento que abrió esta pantalla. */
  private recibirResultadoPuenteWhatsApp(data: unknown): void {
    const resultado = data as {
      source?: string;
      state?: string;
      event?: string;
      code?: string;
      waba_id?: string;
      phone_number_id?: string;
      error?: string;
    };

    if (
      resultado?.source !== 'motordesk-whatsapp-bridge'
      || !this.whatsappBridgeNonce
      || resultado.state !== this.whatsappBridgeNonce
    ) {
      return;
    }

    if (resultado.event === 'FINISH') {
      this.whatsappOAuthCode = resultado.code ?? null;
      this.whatsappWabaId = resultado.waba_id ?? null;
      this.whatsappPhoneNumberId = resultado.phone_number_id ?? null;

      if (
        !this.whatsappOAuthCode
        || !this.whatsappWabaId
        || !this.whatsappPhoneNumberId
      ) {
        this.conectandoWhatsApp = false;
        this.errorWhatsApp =
          'Meta no devolvió todos los datos necesarios para conectar WhatsApp.';
        this.cdr.detectChanges();
        return;
      }

      this.intentarCompletarConexionWhatsApp();
      return;
    }

    this.whatsappConexionEnCurso = false;
    this.conectandoWhatsApp = false;
    this.errorWhatsApp = resultado.error
      ?? 'La conexión con WhatsApp fue cancelada o no se completó.';
    this.cdr.detectChanges();
  }


  private generarNonceWhatsApp(): string {
    const bytes = new Uint8Array(24);
    crypto.getRandomValues(bytes);
    return Array.from(bytes, (byte) => byte.toString(16).padStart(2, '0')).join('');
  }


  crearPlantilla(
    plantilla: WhatsAppPlantilla
  ): void {

    if (
      plantilla.estado !== 'NO_CREADA'
      || this.creandoPlantillaWhatsApp !== null
    ) {
      return;
    }

    this.creandoPlantillaWhatsApp =
      plantilla.tipo;

    this.errorPlantillasWhatsApp = null;

    this.whatsappService
      .crearPlantilla(plantilla.tipo)
      .subscribe({

        next: () => {

          this.creandoPlantillaWhatsApp = null;

          // Recarga el catálogo local.
          // La plantilla debería pasar normalmente a PENDING.
          this.cargarPlantillasWhatsApp();
        },

        error: (error) => {

          this.creandoPlantillaWhatsApp = null;

          this.errorPlantillasWhatsApp =
            error?.error?.detail
            ?? `No se ha podido crear la plantilla ${plantilla.tipo}.`;

          this.cdr.detectChanges();
        },

      });
  }
}
