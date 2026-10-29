import { DatePipe, DecimalPipe } from '@angular/common';
import { ChangeDetectorRef, Component, OnInit, inject } from '@angular/core';
import { MatDialog } from '@angular/material/dialog';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatChipsModule } from '@angular/material/chips';
import { MatDividerModule } from '@angular/material/divider';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatTableModule } from '@angular/material/table';
import { MatSelectModule } from '@angular/material/select';
import { NotificationService } from '../../../../shared/services/notification';
import { Factura } from '../../models/factura';
import { FacturaLinea } from '../../models/factura-linea';
import { FacturaLineaCreate } from '../../models/factura-linea-create';
import { FacturaLineaUpdate } from '../../models/factura-linea-update';
import { FacturaLineasService } from '../../services/factura-lineas.service';
import { FacturasService } from '../../services/facturas.service';
import { PagoFactura } from '../../models/pago-factura';
import { PagoFacturaResumen } from '../../models/pago-factura-resumen';
import { PagoFacturaService } from '../../services/pago-factura.service';
import { ConfirmDialog } from '../../../../shared/components/confirm-dialog/confirm-dialog';
import { RegistroVerifactu } from '../../models/registro-verifactu';
import { OrdenesService } from '../../../ordenes/services/ordenes.service';
import { AuthService } from '../../../../core/auth/auth.service';
import { ClientesService } from '../../../clientes/services/clientes.service';
import { Cliente } from '../../../clientes/models/cliente';
import { ConfiguracionDocumentosService } from '../../../configuracion/services/configuracion-documentos.service';
import { FacturaeDestinoUpdate } from '../../models/facturae-destino';
import { FacturaeOrganismo } from '../../models/facturae-organismo';
import { AutocompleteSelect } from '../../../../shared/components/autocomplete-select/autocomplete-select';

@Component({
  selector: 'app-factura-form',
  standalone: true,
  imports: [
    DecimalPipe,
    DatePipe,
    FormsModule,
    MatButtonModule,
    MatCardModule,
    MatChipsModule,
    MatDividerModule,
    MatFormFieldModule,
    MatIconModule,
    MatInputModule,
    MatProgressSpinnerModule,
    MatTableModule,
    MatSelectModule,
    AutocompleteSelect,
    RouterLink
  ],
  templateUrl: './factura-form.html',
  styleUrl: './factura-form.scss'
})
export class FacturaForm implements OnInit {
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly facturasService = inject(FacturasService);
  private readonly facturaLineasService = inject(FacturaLineasService);
  private readonly notification = inject(NotificationService);
  private readonly cdr = inject(ChangeDetectorRef);
  private pagoFacturaService = inject(PagoFacturaService);
  private readonly dialog = inject(MatDialog);
  private readonly ordenesService = inject(OrdenesService);
  private readonly clientesService = inject(ClientesService);
  private readonly documentosConfigService = inject(ConfiguracionDocumentosService);
  readonly authService = inject(AuthService);

  nuevoPago = {
  importe: 0,
  metodo_pago: 'EFECTIVO',
  referencia: '',
  observaciones: ''
  };

  mostrarFormularioPago = false;
  ibanCobros: string | null = null;
  pagos: PagoFactura[] = [];
  resumenPago?: PagoFacturaResumen;
  registrosVerifactu: RegistroVerifactu[] = [];
  cargandoVerifactu = false;
  generandoVerifactu = false;
  guardandoFacturae = false;
  guardandoOrganismoFacturae = false;
  facturaeDestino: FacturaeDestinoUpdate = this.crearDestinoFacturaeVacio();
  organismosFacturae: FacturaeOrganismo[] = [];
  organismoFacturaeId: number | null = null;
  tieneDestinoFacturae = false;
  factura?: Factura;
  lineas: FacturaLinea[] = [];
  lineaEditando: number | null = null;
  lineaTemporal: FacturaLineaUpdate = {};
  registroVerifactuId: number | null = null;
  estadoVerifactu: string | null = null;
  loading = false;
  observaciones = '';
  modoCreacion = false;
  clientes: Cliente[] = [];
  etiquetaCliente = (cliente: Cliente): string => [
    cliente.apellidos,
    cliente.nombre,
    cliente.dni,
    cliente.telefono,
    cliente.email,
  ].filter(valor => Boolean(valor?.trim())).join(' · ');
  nuevaFactura = {
    cliente_id: null as number | null,
    tipo_factura: 'REPARACION',
    observaciones: ''
  };

  get displayedColumns(): string[] {
    const columnas = [
      'descripcion', 'origen', 'cantidad', 'precio', 'descuento', 'iva', 'total', 'acciones'
    ];
    return this.factura?.tipo_factura === 'VENTAS_COMISIONES'
      ? ['categoria_fiscal', ...columnas]
      : columnas;
  }

  ngOnInit(): void {
    const parametroId = this.route.snapshot.paramMap.get('id');

    if (
      this.route.snapshot.data['modoCreacion']
      || parametroId === 'nuevo'
      || parametroId === 'nueva'
    ) {
      this.modoCreacion = true;
      const tipo = this.route.snapshot.queryParamMap.get('tipo');
      if (tipo === 'RECAMBIO') {
        this.nuevaFactura.tipo_factura = 'RECAMBIO';
      }
      this.cargarClientesParaNuevaFactura();
      return;
    }

    const id = Number(parametroId);

    if (!Number.isInteger(id) || id <= 0) {
      this.notification.error('La factura indicada no es válida.');
      void this.router.navigate(['/facturas']);
      return;
    }

    this.cargarFactura(id);
  }

  cargarClientesParaNuevaFactura(): void {
    this.loading = true;
    this.clientesService.getClientesSelect().subscribe({
      next: clientes => {
        this.clientes = clientes;
        this.loading = false;
        this.cdr.markForCheck();
      },
      error: err => {
        this.loading = false;
        this.notification.showHttpError(err);
        this.cdr.markForCheck();
      }
    });
  }

  crearFacturaManual(): void {
    if (!this.nuevaFactura.cliente_id) {
      this.notification.error('Selecciona un cliente para crear la factura.');
      return;
    }

    this.loading = true;
    this.facturasService.createFactura({
      tipo_documento: 'FACTURA',
      tipo_factura: this.nuevaFactura.tipo_factura,
      cliente_id: this.nuevaFactura.cliente_id,
      orden_id: undefined,
      descuento_porcentaje: 0,
      iva: 21,
      observaciones: this.nuevaFactura.observaciones || undefined
    }).subscribe({
      next: factura => {
        this.notification.success('Factura en borrador creada correctamente.');
        void this.router.navigate(['/facturas', factura.id]);
      },
      error: err => {
        this.loading = false;
        this.notification.showHttpError(err);
        this.cdr.markForCheck();
      }
    });
  }

  cargarFactura(id: number): void {
    this.loading = true;
    this.facturasService.getFactura(id).subscribe({
      next: factura => {
        this.factura = factura;
        // La respuesta de detalle ya incluye las líneas asociadas. Usarla
        // evita que una segunda petición vacía o desactualizada oculte los
        // conceptos que se han usado para calcular los totales.
        this.cargarPagos();
        this.cargarResumenPago();
        this.cargarRegistrosVerifactu();
        this.cargarDestinoFacturae();
        this.lineas = factura.lineas ?? [];
        this.observaciones = factura.observaciones ?? '';
        this.loading = false;
        this.cdr.markForCheck();
      },
      error: err => {
        this.loading = false;
        this.notification.showHttpError(err);
        this.cdr.markForCheck();
      }
    });
  }

  cargarDestinoFacturae(): void {
    if (!this.factura) return;
    this.cargarOrganismosFacturae();
    this.facturasService.getFacturaeDestino(this.factura.id).subscribe({
      next: destino => {
        const { id, factura_id, created_at, updated_at, ...datos } = destino;
        this.facturaeDestino = datos;
        this.tieneDestinoFacturae = true;
        this.cdr.markForCheck();
      },
      error: () => {
        this.facturaeDestino = this.crearDestinoFacturaeVacio();
        this.tieneDestinoFacturae = false;
        this.cdr.markForCheck();
      }
    });
  }

  guardarDestinoFacturae(): void {
    if (!this.factura || this.factura.estado !== 'BORRADOR' || this.guardandoFacturae) return;
    const destino = this.facturaeDestino;
    if (!destino.nombre.trim() || !destino.nif.trim() || !destino.oficina_contable.trim()
      || !destino.organo_gestor.trim() || !destino.unidad_tramitadora.trim()) {
      this.notification.error('Completa el organismo, NIF y los tres códigos DIR3.');
      return;
    }
    this.guardandoFacturae = true;
    this.facturasService.guardarFacturaeDestino(this.factura.id, destino).subscribe({
      next: () => {
        this.guardandoFacturae = false;
        this.tieneDestinoFacturae = true;
        this.notification.success('Datos de Facturae guardados.');
        this.cdr.markForCheck();
      },
      error: err => {
        this.guardandoFacturae = false;
        this.notification.showHttpError(err);
        this.cdr.markForCheck();
      }
    });
  }

  private crearDestinoFacturaeVacio(): FacturaeDestinoUpdate {
    return {
      nombre: '', nif: '', direccion: '', codigo_postal: '', ciudad: '', provincia: '',
      oficina_contable: '', organo_gestor: '', unidad_tramitadora: '', expediente: '',
      referencia_contrato: '', referencia_receptor: '', observaciones: ''
    };
  }

  getEstadoColor(estado: string): string {
    return ({ BORRADOR: '#ff9800', EMITIDA: '#4caf50', ANULADA: '#f44336' } as Record<string, string>)[estado] ?? '#607d8b';
  }

  getOrigenLabel(origen: string): string {
    return ({ MANO_OBRA: 'Mano de obra', PIEZA: 'Pieza', MANUAL: 'Manual' } as Record<string, string>)[origen] ?? origen;
  }

  getTipoFacturaLabel(tipo: string): string {
    return ({
      REPARACION: 'Reparaci\u00f3n',
      PRESUPUESTO: 'Presupuesto',
      GARANTIA: 'Garant\u00eda',
      RECAMBIO: 'Recambio',
      VENTAS_COMISIONES: 'Ventas y comisiones'
    } as Record<string, string>)[tipo] ?? tipo;
  }

  esFacturaVentasComisiones(): boolean {
    return this.factura?.tipo_factura === 'VENTAS_COMISIONES';
  }

  getCategoriaFiscalLabel(categoria?: string): string {
    return ({
      VENTA_SERVICIO: 'Venta o servicio',
      COMISION_SUJETA: 'Comisi\u00f3n sujeta',
      COMISION_EXENTA: 'Comisi\u00f3n exenta'
    } as Record<string, string>)[categoria ?? 'VENTA_SERVICIO'] ?? categoria ?? '';
  }

  actualizarCategoriaFiscal(): void {
    if (this.lineaTemporal.categoria_fiscal === 'COMISION_EXENTA') {
      this.lineaTemporal.iva = 0;
      return;
    }

    this.lineaTemporal.motivo_exencion = null;
  }

  getDesgloseIva(): Array<{ etiqueta: string; base: number; cuota: number }> {
    const grupos = new Map<string, { etiqueta: string; base: number; cuota: number }>();

    for (const linea of this.lineas) {
      const categoria = linea.categoria_fiscal ?? 'VENTA_SERVICIO';
      const exenta = categoria === 'COMISION_EXENTA';
      const etiqueta = exenta
        ? 'Comisi\u00f3n exenta'
        : categoria === 'COMISION_SUJETA'
          ? `Comisi\u00f3n - IVA ${linea.iva} %`
          : `Venta o servicio - IVA ${linea.iva} %`;
      const clave = `${categoria}:${linea.iva}`;
      const grupo = grupos.get(clave) ?? { etiqueta, base: 0, cuota: 0 };
      const base = Number(linea.subtotal);

      grupo.base += base;
      grupo.cuota += base * Number(linea.iva) / 100;
      grupos.set(clave, grupo);
    }

    return [...grupos.values()];
  }

  getMetodoPagoLabel(metodo: string): string {
    return ({
      EFECTIVO: 'Efectivo', TARJETA: 'Tarjeta', TRANSFERENCIA: 'Transferencia',
      BIZUM: 'Bizum', OTRO: 'Otro'
    } as Record<string, string>)[metodo] ?? metodo;
  }

  getEstadoCobro(): string {
    if (!this.resumenPago) return 'PENDIENTE';
    if (this.resumenPago.importe_pagado <= 0) return 'PENDIENTE';
    return this.resumenPago.importe_pendiente > 0 ? 'PARCIAL' : 'PAGADA';
  }

  getEstadoCobroColor(): string {
    return ({ PENDIENTE: '#ff9800', PARCIAL: '#2196f3', PAGADA: '#4caf50' } as Record<string, string>)[this.getEstadoCobro()];
  }

  get registroVerifactuAlta(): RegistroVerifactu | undefined {
    return this.registrosVerifactu.find(registro => registro.tipo_registro === 'ALTA');
  }

  get registroVerifactuAnulacion(): RegistroVerifactu | undefined {
    return this.registrosVerifactu.find(registro => registro.tipo_registro === 'ANULACION');
  }

  get altaVerifactuAceptada(): boolean {
    return ['ACEPTADO', 'ACEPTADO_CON_ERRORES'].includes(
      this.registroVerifactuAlta?.estado ?? ''
    );
  }

  getHashCorto(hash: string): string {
    return `${hash.slice(0, 12)}…${hash.slice(-8)}`;
  }

  cargarRegistrosVerifactu(): void {
    if (!this.factura) return;

    this.cargandoVerifactu = true;
    this.facturasService.getRegistrosVerifactu(this.factura.id).subscribe({
      next: registros => {
        this.registrosVerifactu = registros;
        const registroAlta = registros.find(registro => registro.tipo_registro === 'ALTA');
        this.registroVerifactuId = registroAlta?.id ?? null;
        this.estadoVerifactu = registroAlta?.estado ?? null;
        this.cargandoVerifactu = false;
        this.cdr.markForCheck();
      },
      error: err => {
        this.registrosVerifactu = [];
        this.registroVerifactuId = null;
        this.estadoVerifactu = null;
        this.cargandoVerifactu = false;
        this.notification.showHttpError(err);
        this.cdr.markForCheck();
      }
    });
  }

  generarRegistroVerifactuPrueba(): void {
    if (!this.factura || this.factura.estado !== 'EMITIDA' || this.generandoVerifactu) {
      return;
    }

    this.generandoVerifactu = true;
    this.facturasService.generarRegistroVerifactuPrueba(this.factura.id).subscribe({
      next: registro => {
        this.registrosVerifactu = [...this.registrosVerifactu, registro];
        this.generandoVerifactu = false;
        this.notification.success('Registro VERI*FACTU generado y validado correctamente.');
        this.cdr.markForCheck();
      },
      error: err => {
        this.generandoVerifactu = false;
        this.notification.showHttpError(err);
        this.cdr.markForCheck();
      }
    });
  }

  puedeModificarLinea(linea: FacturaLinea): boolean {
    return this.factura?.estado === 'BORRADOR' && linea.origen === 'MANUAL';
  }

  verFactura(): void {
    if (!this.factura) return;

    this.facturasService.descargarPdf(this.factura.id).subscribe({
      next: blob => {
        const url = URL.createObjectURL(blob);
        window.open(url, '_blank', 'noopener');
        setTimeout(() => URL.revokeObjectURL(url), 60_000);
      },
      error: err => this.notification.showHttpError(err)
    });
  }

  enviarEmail(): void {
    if (!this.factura) return;

    this.facturasService.enviarFacturaEmail(this.factura.id).subscribe({
      next: response => this.notification.success(
        `Factura enviada correctamente a ${response.email}`
      ),
      error: err => this.notification.showHttpError(err)
    });
  }

  emitirFactura(): void {
    this.cambiarEstado('emitirFactura', 'Factura emitida correctamente.');
  }

  anularFactura(): void {
    if (this.altaVerifactuAceptada) {
      this.prepararAnulacionVerifactu();
      return;
    }
    if (this.registroVerifactuAlta) {
      this.notification.error(
        'Primero debe resolverse el envío del registro VERI*FACTU de alta.'
      );
      return;
    }
    this.cambiarEstado('anularFactura', 'Factura anulada correctamente.');
  }

  prepararAnulacionVerifactu(): void {
    if (!this.factura) return;

    if (this.registroVerifactuAnulacion) {
      this.notification.error(
        'Ya existe un registro VERI*FACTU de anulación para esta factura.'
      );
      return;
    }

    this.dialog.open(ConfirmDialog, {
      data: {
        title: 'Anular factura en VERI*FACTU',
        message: 'Se generará un registro de anulación encadenado. La factura solo quedará anulada cuando AEAT lo acepte.'
      }
    }).afterClosed().subscribe((confirmado: boolean) => {
      if (!confirmado || !this.factura) return;

      this.facturasService.generarAnulacionVerifactu(this.factura.id).subscribe({
        next: () => {
          this.notification.success(
            'Registro de anulación generado. Envíalo a AEAT TEST para completar la anulación.'
          );
          this.cargarRegistrosVerifactu();
        },
        error: err => this.notification.showHttpError(err)
      });
    });
  }

  enviarWhatsapp(): void {
    if (!this.factura) return;

    this.facturasService.enviarFacturaWhatsApp(this.factura.id).subscribe({
      next: response => this.notification.success(
        `Factura enviada correctamente por WhatsApp a ${response.telefono}`
      ),
      error: err => this.notification.showHttpError(err)
    });
    return;

    this.notification.success('Próximamente disponible.');
  }

  guardarObservaciones(): void {
    if (!this.factura) return;

    this.facturasService.updateFactura(this.factura.id, { observaciones: this.observaciones }).subscribe({
      next: factura => {
        this.factura = factura;
        this.lineas = factura.lineas ?? [];
        this.observaciones = factura.observaciones ?? '';
        this.notification.success('Observaciones actualizadas.');
      },
      error: err => this.notification.showHttpError(err)
    });
  }

  nuevaLinea(): void {
    if (!this.factura) return;

    const linea: FacturaLineaCreate = {
      origen: 'MANUAL', descripcion: 'Nueva línea', cantidad: 1,
      precio_unitario: 0, descuento_porcentaje: 0, iva: 21,
      categoria_fiscal: 'VENTA_SERVICIO', motivo_exencion: null
    };
    this.facturaLineasService.createLinea(this.factura.id, linea).subscribe({
      next: () => {
        this.notification.success('Línea creada correctamente.');
        this.refrescarFactura();
      },
      error: err => this.notification.showHttpError(err)
    });
  }

  eliminarLinea(lineaId: number): void {
    const linea = this.lineas.find(item => item.id === lineaId);
    if (!linea || !this.puedeModificarLinea(linea)) return;

    this.facturaLineasService.deleteLinea(lineaId).subscribe({
      next: () => {
        this.notification.success('Línea eliminada correctamente.');
        this.refrescarFactura();
      },
      error: err => this.notification.showHttpError(err)
    });
  }

  editarLinea(linea: FacturaLinea): void {
    if (!this.puedeModificarLinea(linea)) return;

    this.lineaEditando = linea.id;
    this.lineaTemporal = {
      descripcion: linea.descripcion,
      cantidad: linea.cantidad,
      precio_unitario: linea.precio_unitario,
      descuento_porcentaje: linea.descuento_porcentaje,
      iva: linea.iva,
      categoria_fiscal: linea.categoria_fiscal,
      motivo_exencion: linea.motivo_exencion ?? null
    };
  }

  cancelarEdicion(): void {
    this.lineaEditando = null;
    this.lineaTemporal = {};
  }

  guardarLinea(linea: FacturaLinea): void {
    if (!this.puedeModificarLinea(linea)) return;

    const datos = this.lineaTemporal;
    if (!this.esLineaValida(datos)) {
      this.notification.error('Revisa la cantidad, el precio y el IVA de la línea.');
      return;
    }

    this.facturaLineasService.updateLinea(linea.id, datos).subscribe({
      next: () => {
        this.notification.success('Línea actualizada.');
        this.cancelarEdicion();
        this.refrescarFactura();
      },
      error: err => this.notification.showHttpError(err)
    });
  }

  actualizarDesdeOrden(): void {
    if (!this.factura) return;

    this.facturasService.actualizarDesdeOrden(this.factura.id).subscribe({
      next: factura => {
        this.factura = factura;
        this.lineas = factura.lineas ?? [];
        this.observaciones = factura.observaciones ?? '';
        this.notification.success('Factura actualizada desde la orden.');
      },
      error: err => this.notification.showHttpError(err)
    });
  }

  private refrescarFactura(): void {
    if (this.factura) this.cargarFactura(this.factura.id);
  }

  private cambiarEstado(accion: 'emitirFactura' | 'anularFactura', mensaje: string): void {
    if (!this.factura) return;

    const esEmision = accion === 'emitirFactura';
    this.dialog.open(ConfirmDialog, {
      data: {
        title: esEmision ? 'Emitir factura' : 'Anular factura',
        message: esEmision
          ? 'La factura quedará emitida y no podrá modificarse. ¿Deseas continuar?'
          : 'La factura quedará anulada. ¿Deseas continuar?',
        confirmText: esEmision ? 'Emitir factura' : 'Anular factura',
        confirmColor: esEmision ? 'primary' : 'warn',
      },
      disableClose: true,
      autoFocus: false,
    }).afterClosed().subscribe(confirmado => {
      if (!confirmado || !this.factura) return;

      this.facturasService[accion](this.factura.id).subscribe({
        next: factura => {
          this.factura = factura;
          this.notification.success(mensaje);
        },
        error: err => this.notification.showHttpError(err)
      });
    });
  }

  cargarOrganismosFacturae(): void {
    this.facturasService.getOrganismosFacturae().subscribe({
      next: organismos => {
        this.organismosFacturae = organismos;
        this.cdr.markForCheck();
      },
      error: () => {
        this.organismosFacturae = [];
        this.cdr.markForCheck();
      },
    });
  }

  etiquetaOrganismoFacturae = (organismo: FacturaeOrganismo): string =>
    `${organismo.nombre} · ${organismo.nif}`;

  seleccionarOrganismoFacturae(id: number | null): void {
    this.organismoFacturaeId = id;
    const organismo = this.organismosFacturae.find(item => item.id === id);
    if (!organismo) return;
    const { id: _id, created_at: _createdAt, updated_at: _updatedAt, ...datos } = organismo;
    this.facturaeDestino = { ...datos };
    this.cdr.markForCheck();
  }

  guardarOrganismoFacturae(): void {
    if (this.guardandoOrganismoFacturae) return;
    const destino = this.facturaeDestino;
    if (!destino.nombre.trim() || !destino.nif.trim() || !destino.oficina_contable.trim()
      || !destino.organo_gestor.trim() || !destino.unidad_tramitadora.trim()) {
      this.notification.error('Completa el organismo, NIF y los tres códigos DIR3 antes de guardarlo.');
      return;
    }
    this.guardandoOrganismoFacturae = true;
    this.facturasService.guardarOrganismoFacturae(destino, this.organismoFacturaeId ?? undefined).subscribe({
      next: organismo => {
        this.guardandoOrganismoFacturae = false;
        this.organismoFacturaeId = organismo.id;
        const indice = this.organismosFacturae.findIndex(item => item.id === organismo.id);
        if (indice >= 0) this.organismosFacturae[indice] = organismo;
        else this.organismosFacturae = [...this.organismosFacturae, organismo].sort((a, b) => a.nombre.localeCompare(b.nombre));
        this.notification.success('Organismo Facturae guardado para próximas facturas.');
        this.cdr.markForCheck();
      },
      error: error => {
        this.guardandoOrganismoFacturae = false;
        this.notification.showHttpError(error);
        this.cdr.markForCheck();
      },
    });
  }

  private esLineaValida(linea: FacturaLineaUpdate): boolean {
    const categoria = linea.categoria_fiscal ?? 'VENTA_SERVICIO';
    const esComisionExenta = categoria === 'COMISION_EXENTA';

    return !!linea.descripcion?.trim()
      && (linea.cantidad ?? 0) > 0
      && (linea.precio_unitario ?? -1) >= 0
      && (linea.descuento_porcentaje ?? -1) >= 0
      && (linea.descuento_porcentaje ?? 101) <= 100
      && (linea.iva ?? -1) >= 0
      && (!esComisionExenta || linea.iva === 0)
      && (!esComisionExenta || !!linea.motivo_exencion?.trim());
  }

  cargarPagos(): void {

  if (!this.factura) {
    return;
  }

  this.pagoFacturaService
    .getPagos(this.factura.id)
    .subscribe({

      next: pagos => {
        this.pagos = pagos;
        this.cdr.markForCheck();
      },

      error: err => {
        this.notification.showHttpError(err);
        this.cdr.markForCheck();
      }

    });

  }

  cargarResumenPago(): void {

  if (!this.factura) {
    return;
  }

  this.pagoFacturaService
    .getResumen(this.factura.id)
    .subscribe({

      next: resumen => {
        this.resumenPago = resumen;
        this.cdr.markForCheck();
      },

      error: err => {
        this.notification.showHttpError(err);
        this.cdr.markForCheck();
      }

    });

  }

  abrirFormularioPago(): void {

  if (
    !this.factura
    || this.factura.estado !== 'EMITIDA'
    || !this.resumenPago
    || this.resumenPago.importe_pendiente <= 0
  ) {
    return;
  }

  this.nuevoPago = {
    importe: this.resumenPago.importe_pendiente,
    metodo_pago: 'EFECTIVO',
    referencia: '',
    observaciones: ''
  };

  this.mostrarFormularioPago = true;
  this.cdr.markForCheck();

  }

  /** Carga la cuenta del taller una vez y solo para informar transferencias. */
  private cargarCuentaCobros(): void {
    if (this.ibanCobros !== null) {
      return;
    }

    this.documentosConfigService.getConfiguracion().subscribe({
      next: configuracion => {
        this.ibanCobros = configuracion.iban_cobros?.trim() || '';
        this.cdr.markForCheck();
      },
      // La ausencia de una cuenta no debe impedir registrar un cobro.
      error: () => {
        this.ibanCobros = '';
        this.cdr.markForCheck();
      }
    });
  }

  esTransferencia(): boolean {
    return this.nuevoPago.metodo_pago === 'TRANSFERENCIA';
  }

  alCambiarMetodoPago(): void {
    if (this.esTransferencia()) {
      this.cargarCuentaCobros();
    }
  }

  cancelarPago(): void {

  this.mostrarFormularioPago = false;
  this.cdr.markForCheck();

  }

  registrarPago(): void {

  if (!this.factura || !this.resumenPago) {
    return;
  }

  if (
    !Number.isFinite(this.nuevoPago.importe)
    || this.nuevoPago.importe <= 0
    || this.nuevoPago.importe > this.resumenPago.importe_pendiente
  ) {
    this.notification.error('Indica un importe válido que no supere el pendiente.');
    return;
  }

  this.pagoFacturaService
    .crearPago(
      this.factura.id,
      this.nuevoPago
    )
    .subscribe({

      next: () => {

        this.notification.success(
          'Cobro registrado correctamente.'
        );

        this.mostrarFormularioPago = false;
        this.cdr.markForCheck();

        this.cargarPagos();
        this.cargarResumenPago();
        this.cargarFactura(this.factura!.id);

      },

      error: err => {

        this.notification.showHttpError(err);

      }

    });

  }

  eliminarPago(pago: PagoFactura): void {
    this.dialog.open(ConfirmDialog, {
      data: {
        title: 'Eliminar cobro',
        message: `¿Eliminar el cobro de ${pago.importe.toFixed(2)} €?`
      }
    }).afterClosed().subscribe((confirmado: boolean) => {
      if (!confirmado) return;

      this.pagoFacturaService.eliminarPago(pago.id).subscribe({
        next: () => {
          this.notification.success('Cobro eliminado correctamente.');
          this.cargarPagos();
          this.cargarResumenPago();
        },
        error: err => this.notification.showHttpError(err)
      });
    });
  }

  generarVerifactu(): void {

  if (!this.factura) {
    return;
  }

  this.facturasService
    .generarVerifactu(this.factura.id)
    .subscribe({

      next: respuesta => {

        this.registroVerifactuId =
          respuesta.id;

        this.estadoVerifactu =
          respuesta.estado;

        this.notification.success(
          'Registro VERI*FACTU generado correctamente.'
        );

      },

      error: err => {

        this.notification.showHttpError(err);

      }

    });

  }

  enviarVerifactuTest(): void {

  if (!this.registroVerifactuId) {
    return;
  }

  this.facturasService
    .enviarVerifactuTest(
      this.registroVerifactuId
    )
    .subscribe({

      next: respuesta => {

        this.estadoVerifactu =
          respuesta.estado;

        // La aceptación cambia el flujo de anulación y debe reflejarse en el
        // historial antes de que el usuario pueda pulsar otra acción.
        this.cargarRegistrosVerifactu();

        this.notification.success(
          'Respuesta recibida de AEAT.'
        );

        console.log(
          'VERI*FACTU AEAT:',
          respuesta
        );

      },

      error: err => {

        this.notification.showHttpError(err);

      }

    });

  }

  enviarAnulacionVerifactuTest(): void {
    const anulacion = this.registroVerifactuAnulacion;
    if (!anulacion) return;

    this.facturasService.enviarVerifactuTest(anulacion.id).subscribe({
      next: respuesta => {
        this.notification.success('Respuesta de anulación recibida de AEAT.');
        console.log('VERI*FACTU AEAT (anulación):', respuesta);
        this.cargarRegistrosVerifactu();
        if (['ACEPTADO', 'ACEPTADO_CON_ERRORES'].includes(respuesta.estado)) {
          this.refrescarFactura();
        }
      },
      error: err => this.notification.showHttpError(err)
    });
  }

  crearGarantia(): void {
    if (!this.factura) return;

    this.ordenesService.crearGarantiaDesdeFactura(this.factura.id).subscribe({
      next: garantia => {
        this.notification.success(`Garantía ${garantia.numero} creada.`);
        void this.router.navigate(['/ordenes', garantia.id]);
      },
      error: err => this.notification.showHttpError(err)
    });
  }

}
/** Formulario de factura en borrador; la emisión fiscal se realiza desde backend. */
