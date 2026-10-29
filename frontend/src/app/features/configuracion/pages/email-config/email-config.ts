import { ChangeDetectorRef, Component, inject, OnDestroy, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { finalize } from 'rxjs';
import { ConfiguracionEmailGuardar, ConfiguracionEmailService } from '../../services/configuracion-email.service';
import { NotificationService } from '../../../../shared/services/notification';

@Component({
  selector: 'app-email-config', standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  templateUrl: './email-config.html', styleUrl: './email-config.scss',
})
export class EmailConfig implements OnInit, OnDestroy {
  private readonly service = inject(ConfiguracionEmailService);
  private readonly notification = inject(NotificationService);
  private readonly cdr = inject(ChangeDetectorRef);
  cargando = true; guardando = false; probando = false; configurado = false;
  pruebaDestinatario = '';
  conectandoGoogle = false; conectandoMicrosoft = false;
  metodoAutenticacion: 'password' | 'google_oauth' | 'microsoft_oauth' = 'password';
  private esperaGoogle?: number; private limiteGoogle?: number;
  private esperaMicrosoft?: number; private limiteMicrosoft?: number;
  datos: ConfiguracionEmailGuardar = { proveedor: 'gmail', host: 'smtp.gmail.com', puerto: 587, seguridad: 'starttls', usuario: '', remitente: '', password: '', activo: true };

  ngOnInit(): void { this.cargar(); }
  ngOnDestroy(): void { this.finalizarGoogle(); this.finalizarMicrosoft(); }
  get googleConectado(): boolean { return this.configurado && this.metodoAutenticacion === 'google_oauth'; }
  get microsoftConectado(): boolean { return this.configurado && this.metodoAutenticacion === 'microsoft_oauth'; }

  private cargar(): void {
    this.service.obtener().pipe(finalize(() => { this.cargando = false; this.cdr.detectChanges(); })).subscribe({
      next: c => {
        this.configurado = c.configurado;
        this.metodoAutenticacion = c.metodo_autenticacion;
        if (c.configurado) this.datos = { ...this.datos, ...c, usuario: c.usuario || '', remitente: c.remitente || '', password: '' };
      },
      error: () => this.notification.error('No se pudo cargar la configuración de correo.'),
    });
  }

  cambiarProveedor(): void {
    if (this.datos.proveedor === 'gmail') Object.assign(this.datos, { host: 'smtp.gmail.com', puerto: 587, seguridad: 'starttls' });
    if (this.datos.proveedor === 'outlook') Object.assign(this.datos, { host: 'smtp.office365.com', puerto: 587, seguridad: 'starttls' });
  }
  guardar(): void {
    if (!this.datos.usuario || (!this.configurado && !this.datos.password)) { this.notification.error('Indica el correo y su contraseña de aplicación.'); return; }
    this.guardando = true;
    this.service.guardar(this.datos).pipe(finalize(() => this.guardando = false)).subscribe({
      next: () => { this.configurado = true; this.metodoAutenticacion = 'password'; this.datos.password = ''; this.notification.success('Configuración de correo guardada.'); },
      error: e => this.notification.error(e.error?.detail || 'No se pudo guardar la configuración.'),
    });
  }
  probar(): void {
    if (!this.pruebaDestinatario) { this.notification.error('Indica una dirección para la prueba.'); return; }
    this.probando = true;
    this.service.probar(this.pruebaDestinatario).pipe(finalize(() => this.probando = false)).subscribe({
      next: () => this.notification.success('Correo de prueba enviado.'),
      error: e => this.notification.error(e.error?.detail || 'No se pudo enviar la prueba.'),
    });
  }

  private finalizarGoogle(mensaje?: string): void {
    if (this.esperaGoogle) window.clearInterval(this.esperaGoogle);
    if (this.limiteGoogle) window.clearTimeout(this.limiteGoogle);
    this.esperaGoogle = undefined; this.limiteGoogle = undefined; this.conectandoGoogle = false;
    if (mensaje) this.notification.error(mensaje);
  }
  private finalizarMicrosoft(mensaje?: string): void {
    if (this.esperaMicrosoft) window.clearInterval(this.esperaMicrosoft);
    if (this.limiteMicrosoft) window.clearTimeout(this.limiteMicrosoft);
    this.esperaMicrosoft = undefined; this.limiteMicrosoft = undefined; this.conectandoMicrosoft = false;
    if (mensaje) this.notification.error(mensaje);
  }

  conectarGoogle(): void {
    if (this.conectandoGoogle) return;
    this.finalizarGoogle(); this.conectandoGoogle = true;
    this.service.iniciarGoogle().subscribe({ next: ({ url, estado }) => {
      if (!window.open(url, 'motordesk-google-oauth', 'width=520,height=700')) { this.finalizarGoogle('El navegador bloqueó la ventana de Google. Permítela e inténtalo de nuevo.'); return; }
      this.esperaGoogle = window.setInterval(() => this.service.estadoGoogle(estado).subscribe({
        next: r => {
          if (r.estado === 'COMPLETADO') { this.finalizarGoogle(); this.configurado = true; this.metodoAutenticacion = 'google_oauth'; this.datos.proveedor = 'gmail'; this.notification.success('Cuenta de Google conectada correctamente.'); }
          else if (r.estado === 'ERROR') this.finalizarGoogle(r.detalle || 'Google rechazó la autorización.');
          else if (r.estado === 'NO_ENCONTRADO') this.finalizarGoogle('La conexión con Google no se pudo completar. Vuelve a intentarlo.');
        }, error: () => this.finalizarGoogle('No se pudo comprobar la conexión con Google.'),
      }), 1500);
      this.limiteGoogle = window.setTimeout(() => this.finalizarGoogle('La conexión con Google ha caducado. Vuelve a intentarlo.'), 10 * 60_000);
    }, error: e => this.finalizarGoogle(e.error?.detail || 'No se pudo iniciar Google.') });
  }

  conectarMicrosoft(): void {
    if (this.conectandoMicrosoft) return;
    this.finalizarMicrosoft(); this.conectandoMicrosoft = true;
    this.service.iniciarMicrosoft().subscribe({ next: ({ url, estado }) => {
      if (!window.open(url, 'motordesk-microsoft-oauth', 'width=520,height=700')) { this.finalizarMicrosoft('El navegador bloqueó la ventana de Microsoft. Permítela e inténtalo de nuevo.'); return; }
      this.esperaMicrosoft = window.setInterval(() => this.service.estadoMicrosoft(estado).subscribe({
        next: r => {
          if (r.estado === 'COMPLETADO') { this.finalizarMicrosoft(); this.configurado = true; this.metodoAutenticacion = 'microsoft_oauth'; this.datos.proveedor = 'outlook'; this.notification.success('Cuenta de Microsoft conectada correctamente.'); }
          else if (r.estado === 'ERROR' || r.estado === 'NO_ENCONTRADO') this.finalizarMicrosoft('La conexión con Microsoft no se pudo completar. Vuelve a intentarlo.');
        }, error: () => this.finalizarMicrosoft('No se pudo comprobar la conexión con Microsoft.'),
      }), 1500);
      this.limiteMicrosoft = window.setTimeout(() => this.finalizarMicrosoft('La conexión con Microsoft ha caducado. Vuelve a intentarlo.'), 10 * 60_000);
    }, error: e => this.finalizarMicrosoft(e.error?.detail || 'No se pudo iniciar Microsoft.') });
  }
}
