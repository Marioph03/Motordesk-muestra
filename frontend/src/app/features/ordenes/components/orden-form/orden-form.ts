import { ArchivoOrden } from './../../models/archivo-orden';
import { OrdenCreate } from './../../models/orden-create';
import { OrdenUpdate } from './../../models/orden-update';

import {
  Component,
  OnInit,
  ViewChild,
  inject,
  OnDestroy
} from '@angular/core';

import { CommonModule } from '@angular/common';

import {
  FormBuilder,
  ReactiveFormsModule,
  Validators
} from '@angular/forms';

import {
  ActivatedRoute,
  Router,
  RouterLink
} from '@angular/router';

import {
  catchError,
  concatMap,
  finalize,
  from,
  of
} from 'rxjs';

import { MatDialog } from '@angular/material/dialog';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatDividerModule } from '@angular/material/divider';
import { MatTabsModule } from '@angular/material/tabs';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatChipsModule } from '@angular/material/chips';

import { Orden } from '../../models/orden';

import { EstadoVehiculo } from '../estado-vehiculo/estado-vehiculo';

import {
  ConfirmDeleteFileDialogComponent
} from '../confirm-delete-file-dialog/confirm-delete-file-dialog';

import { Vehiculos } from '../../../vehiculos/services/vehiculos';

import {
  VehiculoSelect
} from '../../../vehiculos/models/vehiculo-select';

import {
  OrdenesService
} from '../../services/ordenes.service';

import {
  NotificationService
} from '../../../../shared/services/notification';

import {
  ManoObraList
} from '../mano-obra/mano-obra-list/mano-obra-list';

import {
  PiezaList
} from '../piezas/pieza-list/pieza-list';
import { Factura } from '../../../facturas/models/factura';
import { FacturasService } from '../../../facturas/services/facturas.service';
import { ConfirmDialog } from '../../../../shared/components/confirm-dialog/confirm-dialog';
import { ResolverGarantiaDialog } from '../resolver-garantia-dialog/resolver-garantia-dialog';
import { AutocompleteSelect } from '../../../../shared/components/autocomplete-select/autocomplete-select';
import { PersonalService } from '../../../personal/services/personal.service';
import { DisponibilidadUsuario } from '../../../personal/services/personal.service';


interface EstadoSubidaArchivo {

  archivo: File;

  estado:
    | 'pendiente'
    | 'subiendo'
    | 'completado'
    | 'error';

  error?: string;

}


@Component({
  selector: 'app-orden-form',

  standalone: true,

  imports: [
    CommonModule,
    ReactiveFormsModule,

    MatCardModule,
    MatFormFieldModule,
    MatInputModule,
    MatSelectModule,
    MatButtonModule,
    MatDividerModule,
    MatTabsModule,
    MatIconModule,
    MatProgressBarModule,
    MatChipsModule,
    AutocompleteSelect,
    RouterLink,

    ManoObraList,
    PiezaList,
    EstadoVehiculo
  ],

  templateUrl: './orden-form.html',

  styleUrl: './orden-form.scss'
})
export class OrdenForm implements OnInit, OnDestroy {


  // =====================================================
  // SERVICIOS
  // =====================================================

  private fb = inject(FormBuilder);

  private vehiculosService =
    inject(Vehiculos);

  private ordenesService =
    inject(OrdenesService);

  private notification =
    inject(NotificationService);

  private router =
    inject(Router);

  private route =
    inject(ActivatedRoute);

  private dialog =
    inject(MatDialog);

  private facturasService =
    inject(FacturasService);

  private personalService =
    inject(PersonalService);


  // =====================================================
  // ESTADO DEL VEHÍCULO
  // =====================================================

  @ViewChild(EstadoVehiculo)
  estadoVehiculo?: EstadoVehiculo;


  // =====================================================
  // ORDEN
  // =====================================================

  selectedTabIndex = 0;

  vehiculos: VehiculoSelect[] = [];

  usuarios: DisponibilidadUsuario[] = [];

  etiquetaVehiculo = (vehiculo: VehiculoSelect): string =>
    vehiculo.descripcion;

  isEditMode = false;

  ordenId?: number;

  orden?: Orden;

  facturaAsociada?: Factura;

  ordenGenerada?: Orden;
  anulando = false;

  readonly esNuevoPresupuesto = this.route.snapshot.queryParamMap.get('tipo') === 'PR';

  get esPresupuesto(): boolean {
    return this.esNuevoPresupuesto || this.orden?.tipo === 'PR';
  }

  get esGarantia(): boolean {
    return this.orden?.tipo === 'GA';
  }

  get garantiaTieneConceptosFacturables(): boolean {
    return Number(this.orden?.total_cliente_garantia ?? 0) > 0;
  }

  get nombreDocumento(): string {
    if (this.esGarantia) return 'Garantía';
    return this.esPresupuesto ? 'Presupuesto' : 'Orden';
  }

  get nombreArchivoDocumento(): string {
    if (this.esGarantia) return 'garantia';
    return this.esPresupuesto ? 'presupuesto' : 'orden';
  }

  get esPresupuestoBloqueado(): boolean {
    return this.esPresupuesto
      && !!this.orden
      && this.orden.estado !== 'Borrador';
  }

  get puedeEditarPresupuesto(): boolean {
  if (!this.esPresupuesto) {
    return true;
  }

  // Mientras todavía lo estamos creando,
  // debe poder editarse.
  if (!this.isEditMode) {
    return true;
  }

  return this.orden?.estado === 'Borrador';
  }


get documentoEditable(): boolean {
  return !this.esPresupuesto ||
    this.puedeEditarPresupuesto;
}

  get tituloDocumento(): string {
    if (!this.isEditMode) {
      return this.esNuevoPresupuesto ? 'Nuevo presupuesto' : 'Nueva orden de reparación';
    }
    return this.esPresupuesto ? 'Editar presupuesto' : 'Editar orden';
  }

  get estadosDisponibles(): string[] {
    if (this.esPresupuesto) {
      return ['Borrador', 'Enviado', 'Aceptado', 'Rechazado'];
    }
    return this.orden?.estado === 'Anulada'
      ? ['Anulada']
      : ['Abierta', 'En proceso', 'Cerrada', 'Facturada'];
  }


  // =====================================================
  // ARCHIVOS GUARDADOS
  // =====================================================

  archivos: ArchivoOrden[] = [];


  // =====================================================
  // ARCHIVOS SELECCIONADOS
  // =====================================================

  archivosSeleccionados: File[] = [];

  arrastrandoArchivos = false;

  subiendoArchivo = false;


  // =====================================================
  // CATEGORÍAS
  // =====================================================

  categoriaArchivo = 'Otro';

  categoriasArchivo: string[] = [
    'Foto del vehículo',
    'Documento del cliente',
    'Informe',
    'Presupuesto',
    'Peritaje',
    'Factura externa',
    'Otro'
  ];


  // =====================================================
  // PREVISUALIZACIONES
  // =====================================================

  imagenesPreview: Record<number, string> = {};

  imagenVisor: string | null = null;

  nombreImagenVisor = '';


  // =====================================================
  // ESTADO DE SUBIDAS
  // =====================================================

  estadoSubidas: EstadoSubidaArchivo[] = [];

  archivosSubidos = 0;

  archivosFallidos = 0;


  // =====================================================
  // FORMULARIO
  // =====================================================

  form = this.fb.group({

    tipo: [
      'OR',
      Validators.required
    ],

    vehiculo_id: [
      null as number | null,
      Validators.required
    ],

    kilometros_entrada: [
      null as number | null,
      [Validators.min(0)]
    ],

    descripcion_averia: [
      '',
      [
        Validators.required,
        Validators.maxLength(1000)
      ]
    ],

    estado: [
      'Abierta',
      Validators.required
    ],

    diagnostico: [''],

    observaciones: [''],

    observaciones_internas: [''],

    usuarios_ids: [
      [] as number[]
    ]

  });


  // =====================================================
  // INIT
  // =====================================================

  ngOnInit(): void {

    if (this.esNuevoPresupuesto) {
      this.form.patchValue({ tipo: 'PR', estado: 'Borrador' });
    }

    this.cargarVehiculos();
    this.cargarUsuarios();

    const id =
      this.route.snapshot.paramMap.get('id');

    if (id) {

      this.isEditMode = true;

      this.ordenId = Number(id);

      this.cargarOrden();

    }

  }


  // =====================================================
  // DESTROY
  // =====================================================

  ngOnDestroy(): void {

    Object.values(
      this.imagenesPreview
    ).forEach(url => {

      URL.revokeObjectURL(url);

    });

  }


  // =====================================================
  // CAMBIO DE PESTAÑA
  // =====================================================

  onTabChange(index: number): void {

    // 0 = Orden
    // 1 = Mano de obra
    // 2 = Piezas
    // 3 = Estado del vehículo
    // 4 = Archivos

    if (
      index === 4 &&
      this.isEditMode &&
      this.ordenId
    ) {

      this.cargarArchivos();

    }

  }


  // =====================================================
  // VEHÍCULOS
  // =====================================================

  cargarVehiculos(): void {

    this.vehiculosService
      .getVehiculosSelect()
      .subscribe({

        next: data => {

          this.vehiculos = data;

        },

        error: err => {

          this.notification.showHttpError(
            err
          );

        }

      });

  }

  cargarUsuarios(): void {

    const inicio = new Date();
    const fin = new Date(inicio.getTime() + 60_000);

    this.personalService
      .getDisponibilidad(
        this.formatearFechaHoraLocal(inicio),
        this.formatearFechaHoraLocal(fin),
        undefined,
        this.ordenId
      )
      .subscribe({
        next: usuarios => this.usuarios = usuarios,
        error: err => this.notification.showHttpError(err)
      });

  }

  private formatearFechaHoraLocal(fecha: Date): string {
    const rellenar = (valor: number) => String(valor).padStart(2, '0');

    return `${fecha.getFullYear()}-${rellenar(fecha.getMonth() + 1)}-${rellenar(fecha.getDate())}`
      + `T${rellenar(fecha.getHours())}:${rellenar(fecha.getMinutes())}:${rellenar(fecha.getSeconds())}`;
  }


  // =====================================================
  // GUARDAR ORDEN
  // =====================================================

  anularOrden(): void {
    if (!this.ordenId || this.anulando) return;
    if (!confirm('Se anulará la orden y se devolverán al stock las piezas asociadas. ¿Continuar?')) return;
    this.anulando = true;
    this.ordenesService.anularOrden(this.ordenId).pipe(finalize(() => this.anulando = false)).subscribe({
      next: orden => { this.orden = orden; this.form.patchValue({ estado: orden.estado }); this.notification.success('Orden anulada y stock devuelto.'); },
      error: error => this.notification.showHttpError(error),
    });
  }

  guardar(): void {

    if (this.form.invalid) {

      this.form.markAllAsTouched();

      // El selector de vehiculo es un componente personalizado; sin este
      // aviso una pulsacion sobre Guardar podia parecer que no hacia nada
      // cuando aun faltaba seleccionar una opcion valida de la lista.
      this.notification.warning(
        'Selecciona un vehículo y completa la descripción de la avería.'
      );

      return;

    }


    const orden: OrdenCreate = {

      tipo:
        this.form.value.tipo!,

      vehiculo_id:
        this.form.value.vehiculo_id!,

      kilometros_entrada:
        this.form.value.kilometros_entrada,

      descripcion_averia:
        this.form.value.descripcion_averia!,

      estado:
        this.form.value.estado!,

      diagnostico:
        this.form.value.diagnostico ?? '',

      observaciones:
        this.form.value.observaciones ?? '',

      observaciones_internas:
        this.form.value.observaciones_internas ?? '',

      usuarios_ids:
        this.form.value.usuarios_ids ?? [],

      // Las altas normales no son garantias, pero enviar los valores de
      // forma explicita evita depender de defaults internos del backend.
      garantia: false,

      garantia_meses: null

    };


    // ===================================================
    // ACTUALIZAR
    // ===================================================

    if (this.isEditMode) {

      const ordenUpdate: OrdenUpdate = {

        tipo:
          orden.tipo,

        vehiculo_id:
          orden.vehiculo_id,

        kilometros_entrada:
          orden.kilometros_entrada,

        descripcion_averia:
          orden.descripcion_averia,

        estado:
          orden.estado,

        diagnostico:
          orden.diagnostico,

        observaciones:
          orden.observaciones,

        observaciones_internas:
          orden.observaciones_internas,

        usuarios_ids:
          orden.usuarios_ids,

        vehicle_damage:
          this.estadoVehiculo
            ?.getDamageState()
          // Si no se abre la pestana de estado durante una edicion, Angular
          // no crea el componente. En ese caso conservamos el croquis ya
          // guardado y evitamos borrar danos accidentalmente.
          ?? this.orden?.vehicle_damage
          ?? {}

      };


      this.ordenesService
        .updateOrden(
          this.ordenId!,
          ordenUpdate
        )
        .subscribe({

          next: () => {

            this.notification.success(
              this.esPresupuesto ? 'Presupuesto actualizado correctamente' : 'Orden actualizada correctamente'
            );

            this.cargarOrden();

          },

          error: err => {

            this.notification.showHttpError(
              err
            );

          }

        });


      return;

    }


    // ===================================================
    // CREAR
    // ===================================================

    this.ordenesService
      .createOrden(orden)
      .subscribe({

        next: (
          nuevaOrden: Orden
        ) => {

            this.notification.success(
              this.esPresupuesto ? 'Presupuesto creado correctamente' : 'Orden creada correctamente'
            );

          this.router.navigate([
            '/ordenes',
            nuevaOrden.id
          ]);

        },

        error: err => {

          this.notification.showHttpError(
            err
          );

        }

      });

  }


  // =====================================================
  // CARGAR ORDEN
  // =====================================================

  cargarOrden(): void {

    if (this.ordenId === undefined) {
      return;
    }


    this.ordenesService
      .getOrden(
        this.ordenId
      )
      .subscribe({

        next: orden => {

          this.orden = orden;

          this.form.enable({ emitEvent: false });

          if (orden.tipo !== 'PR') {
            this.cargarFacturaAsociada(orden.id);
          } else if (orden.estado === 'Aceptado') {
            this.cargarOrdenGenerada(orden.id);
          } else {
            this.ordenGenerada = undefined;
          }


          this.form.patchValue({

            tipo:
              orden.tipo,

            vehiculo_id:
              orden.vehiculo_id,

            kilometros_entrada:
              orden.kilometros_entrada,

            descripcion_averia:
              orden.descripcion_averia,

            estado:
              orden.estado,

            diagnostico:
              orden.diagnostico ?? '',

            observaciones:
              orden.observaciones ?? '',

            observaciones_internas:
              orden.observaciones_internas ?? '',

            usuarios_ids:
              orden.usuarios_asignados?.map(
                usuario => usuario.id
              ) ?? []

          });

          if (orden.tipo === 'PR' && orden.estado !== 'Borrador') {
            this.form.disable({ emitEvent: false });
          }


          this.cargarArchivos();

        },

        error: err => {

          this.notification.showHttpError(
            err
          );

          this.router.navigate([
            '/ordenes'
          ]);

        }

      });

  }

  private cargarFacturaAsociada(ordenId: number): void {

    this.facturasService
      .getFacturaPorOrden(ordenId)
      .subscribe({
        next: factura => this.facturaAsociada = factura,
        error: () => this.facturaAsociada = undefined
      });

  }

  private cargarOrdenGenerada(presupuestoId: number): void {
    this.ordenesService
      .getOrdenGeneradaDesdePresupuesto(presupuestoId)
      .subscribe({
        next: orden => this.ordenGenerada = orden,
        error: () => this.ordenGenerada = undefined
      });
  }

  enviarPresupuesto(): void {
    if (!this.ordenId) return;
    this.ordenesService.enviarPresupuesto(this.ordenId).subscribe({
      next: () => {
        this.notification.success('Presupuesto marcado como enviado.');
        this.cargarOrden();
      },
      error: err => this.notification.showHttpError(err)
    });
  }

  aceptarPresupuesto(): void {
    if (!this.ordenId) return;
    this.ordenesService.aceptarPresupuesto(this.ordenId).subscribe({
      next: () => {
        this.notification.success('Presupuesto aceptado.');
        this.cargarOrden();
      },
      error: err => this.notification.showHttpError(err)
    });
  }

  rechazarPresupuesto(): void {
    if (!this.ordenId) return;
    this.dialog.open(ConfirmDialog, {
      data: {
        title: 'Rechazar presupuesto',
        message: '¿Confirmas que el presupuesto ha sido rechazado?'
      }
    }).afterClosed().subscribe(confirmado => {
      if (!confirmado || !this.ordenId) return;
      this.ordenesService.rechazarPresupuesto(this.ordenId).subscribe({
        next: () => {
          this.notification.success('Presupuesto rechazado.');
          this.cargarOrden();
        },
        error: err => this.notification.showHttpError(err)
      });
    });
  }

  convertirEnOrden(): void {
    if (!this.ordenId) return;
    this.ordenesService.convertirPresupuestoEnOrden(this.ordenId).subscribe({
      next: orden => {
        this.notification.success(`Presupuesto convertido en ${orden.numero}.`);
        void this.router.navigate(['/ordenes', orden.id]);
      },
      error: err => this.notification.showHttpError(err)
    });
  }

  iniciarRevisionGarantia(): void { this.ejecutarAccionGarantia('iniciarRevisionGarantia', 'Garantía puesta en revisión.'); }
  aprobarGarantia(): void { this.ejecutarAccionGarantia('aprobarGarantia', 'Garantía aprobada.'); }
  iniciarReparacionGarantia(): void { this.ejecutarAccionGarantia('iniciarReparacionGarantia', 'Reparación de garantía iniciada.'); }

  rechazarGarantia(): void {
    this.dialog.open(ConfirmDialog, { data: { title: 'Rechazar garantía', message: '¿Confirmas el rechazo de la garantía?' } })
      .afterClosed().subscribe(confirmado => {
        if (confirmado) this.ejecutarAccionGarantia('rechazarGarantia', 'Garantía rechazada.');
      });
  }

  resolverGarantia(): void {
    if (!this.ordenId) return;
    this.dialog.open(ResolverGarantiaDialog, { data: { numero: this.orden?.numero ?? '' } })
      .afterClosed().subscribe(resolucion => {
        if (!resolucion) return;
        this.ordenesService.resolverGarantia(this.ordenId!, resolucion).subscribe({
          next: () => { this.notification.success('Garantía resuelta.'); this.cargarOrden(); },
          error: err => this.notification.showHttpError(err)
        });
      });
  }

  generarFacturaGarantia(): void {
    if (!this.ordenId) return;

    this.facturasService.crearDesdeGarantia(this.ordenId).subscribe({
      next: factura => {
        this.notification.success(
          `Factura ${factura.numero} creada con los conceptos no cubiertos.`
        );
        void this.router.navigate(['/facturas', factura.id]);
      },
      error: err => this.notification.showHttpError(err)
    });
  }

  crearGarantia(): void {
    if (!this.ordenId) return;
    this.ordenesService.crearGarantiaDesdeOrden(this.ordenId).subscribe({
      next: garantia => {
        this.notification.success(`Garantía ${garantia.numero} creada.`);
        void this.router.navigate(['/ordenes', garantia.id]);
      },
      error: err => this.notification.showHttpError(err)
    });
  }

  private ejecutarAccionGarantia(
    accion: 'iniciarRevisionGarantia' | 'aprobarGarantia' | 'rechazarGarantia' | 'iniciarReparacionGarantia',
    mensaje: string
  ): void {
    if (!this.ordenId) return;
    this.ordenesService[accion](this.ordenId).subscribe({
      next: () => { this.notification.success(mensaje); this.cargarOrden(); },
      error: err => this.notification.showHttpError(err)
    });
  }


  // =====================================================
  // PDF
  // =====================================================

  generarPdf(): void {

    if (!this.ordenId) {
      return;
    }


    this.ordenesService
      .getOrdenPdf(
        this.ordenId
      )
      .subscribe({

        next: (
          pdf: Blob
        ) => {

          const url =
            URL.createObjectURL(pdf);


          const enlace =
            document.createElement('a');


          enlace.href = url;

          enlace.download =
            `${this.nombreArchivoDocumento}_${
              this.orden?.numero ??
              this.ordenId
            }.pdf`;


          document.body.appendChild(
            enlace
          );

          enlace.click();

          document.body.removeChild(
            enlace
          );

          URL.revokeObjectURL(
            url
          );


          this.notification.success(
            `PDF de ${this.nombreDocumento.toLowerCase()} descargado correctamente`
          );

        },

        error: err => {

          this.notification.showHttpError(
            err
          );

        }

      });

  }


  // =====================================================
  // EMAIL
  // =====================================================

  enviarEmail(): void {

    if (!this.ordenId) {
      return;
    }


    this.ordenesService
      .enviarOrdenEmail(
        this.ordenId
      )
      .subscribe({

        next: response => {

          this.notification.success(
            `Envío de ${this.nombreDocumento.toLowerCase()} correcto a ${response.email}`
          );

          if (this.esPresupuesto) {
            this.cargarOrden();
          }

        },

        error: err => {

          this.notification.showHttpError(
            err
          );

        }

      });

  }


  // =====================================================
  // WHATSAPP
  // =====================================================

  enviarWhatsApp(): void {

    if (!this.ordenId) {
      return;
    }


    this.ordenesService
      .enviarOrdenWhatsApp(
        this.ordenId
      )
      .subscribe({

        next: response => {

          this.notification.success(
            `WhatsApp enviado correctamente a ${response.telefono}`
          );

          if (this.esPresupuesto) {
            this.cargarOrden();
          }

        },

        error: err => {

          this.notification.showHttpError(
            err
          );

        }

      });

  }


  // =====================================================
  // CANCELAR
  // =====================================================

  cancelar(): void {

    this.router.navigate([
      '/ordenes'
    ]);

  }


  // =====================================================
  // CARGAR ARCHIVOS
  // =====================================================

  cargarArchivos(): void {

    if (!this.ordenId) {
      return;
    }


    this.ordenesService
      .getArchivos(
        this.ordenId
      )
      .subscribe({

        next: archivos => {


          // Liberamos las URLs antiguas

          Object.values(
            this.imagenesPreview
          ).forEach(url => {

            URL.revokeObjectURL(
              url
            );

          });


          this.imagenesPreview = {};


          // Guardamos los archivos

          this.archivos = archivos;


          // Cargamos las miniaturas

          archivos
            .filter(
              archivo =>
                archivo.tipo_mime
                  .startsWith('image/')
            )
            .forEach(
              archivo =>
                this.cargarPreviewImagen(
                  archivo
                )
            );

        },

        error: err => {

          console.error(
            'Error cargando archivos',
            err
          );

          this.notification.showHttpError(
            err
          );

        }

      });

  }


  // =====================================================
  // SELECCIONAR ARCHIVOS
  // =====================================================

  seleccionarArchivos(
    event: Event
  ): void {

    const input =
      event.target as HTMLInputElement;


    if (!input.files) {
      return;
    }


    this.agregarArchivos(
      Array.from(
        input.files
      )
    );


    // Permite volver a seleccionar el mismo fichero

    input.value = '';

  }


  // =====================================================
  // AGREGAR ARCHIVOS
  // =====================================================

  private agregarArchivos(
    archivos: File[]
  ): void {

    const permitidos = [
      'application/pdf',
      'image/jpeg',
      'image/png',
      'image/webp'
    ];


    const maxSize =
      10 * 1024 * 1024;


    for (const archivo of archivos) {


      // ===============================================
      // TIPO
      // ===============================================

      if (
        !permitidos.includes(
          archivo.type
        )
      ) {

        console.error(
          `Tipo no permitido: ${archivo.name}`
        );

        continue;

      }


      // ===============================================
      // TAMAÑO
      // ===============================================

      if (
        archivo.size > maxSize
      ) {

        console.error(
          `Archivo demasiado grande: ${archivo.name}`
        );

        continue;

      }


      // ===============================================
      // DUPLICADOS
      // ===============================================

      const existe =
        this.archivosSeleccionados
          .some(
            seleccionado =>
              seleccionado.name ===
                archivo.name &&

              seleccionado.size ===
                archivo.size &&

              seleccionado.lastModified ===
                archivo.lastModified
          );


      if (!existe) {

        this.archivosSeleccionados.push(
          archivo
        );

      }

    }


    // Creamos nueva referencia para Angular

    this.archivosSeleccionados = [
      ...this.archivosSeleccionados
    ];

  }


  // =====================================================
  // DRAG OVER
  // =====================================================

  onDragOver(
    event: DragEvent
  ): void {

    event.preventDefault();

    event.stopPropagation();

    this.arrastrandoArchivos = true;

  }


  // =====================================================
  // DRAG LEAVE
  // =====================================================

  onDragLeave(
    event: DragEvent
  ): void {

    event.preventDefault();

    event.stopPropagation();

    this.arrastrandoArchivos = false;

  }


  // =====================================================
  // DROP
  // =====================================================

  onDrop(
    event: DragEvent
  ): void {

    event.preventDefault();

    event.stopPropagation();

    this.arrastrandoArchivos = false;


    if (
      !event.dataTransfer?.files
    ) {
      return;
    }


    this.agregarArchivos(
      Array.from(
        event.dataTransfer.files
      )
    );

  }


  // =====================================================
  // QUITAR ARCHIVO PENDIENTE
  // =====================================================

  quitarArchivoSeleccionado(
    index: number
  ): void {

    if (this.subiendoArchivo) {
      return;
    }


    this.archivosSeleccionados =
      this.archivosSeleccionados
        .filter(
          (_, i) =>
            i !== index
        );

  }


  // =====================================================
  // SUBIR ARCHIVOS
  // =====================================================

  subirArchivos(): void {

    if (
      !this.ordenId ||
      this.archivosSeleccionados.length === 0 ||
      this.subiendoArchivo
    ) {
      return;
    }


    // ===================================================
    // PREPARAR ESTADO
    // ===================================================

    this.subiendoArchivo = true;

    this.archivosSubidos = 0;

    this.archivosFallidos = 0;


    this.estadoSubidas =
      this.archivosSeleccionados.map(
        archivo => ({

          archivo,

          estado:
            'pendiente' as const

        })
      );


    const subidas = [
      ...this.estadoSubidas
    ];


    // ===================================================
    // SUBIR SECUENCIALMENTE
    // ===================================================

    from(subidas)
      .pipe(

        concatMap(item => {


          // =============================================
          // MARCAR COMO SUBIENDO
          // =============================================

          item.estado =
            'subiendo';


          // =============================================
          // PETICIÓN
          // =============================================

          return this.ordenesService
            .subirArchivo(
              this.ordenId!,
              item.archivo,
              this.categoriaArchivo
            )
            .pipe(

              catchError(error => {


                // =======================================
                // ERROR DE ESTE ARCHIVO
                // =======================================

                item.estado =
                  'error';


                item.error =
                  error?.error?.detail ??
                  'No se pudo subir el archivo';


                this.archivosFallidos++;


                // No propagamos el error.
                // Así concatMap continúa con
                // el siguiente archivo.

                return of(null);

              })

            );

        }),


        // =================================================
        // FINALIZACIÓN GLOBAL
        // =================================================

        finalize(() => {

          this.subiendoArchivo = false;


          // Dejamos seleccionados únicamente
          // los archivos que hayan fallado.

          this.archivosSeleccionados =
            this.estadoSubidas

              .filter(
                item =>
                  item.estado ===
                  'error'
              )

              .map(
                item =>
                  item.archivo
              );


          // Actualizamos galería/documentos

          this.cargarArchivos();


          // ===============================================
          // NOTIFICACIÓN FINAL
          // ===============================================

          if (
            this.archivosFallidos === 0
          ) {

            this.notification.success(
              this.archivosSubidos === 1
                ? 'Archivo subido correctamente'
                : `${this.archivosSubidos} archivos subidos correctamente`
            );

          }

        })

      )
      .subscribe({

        next: resultado => {


          // Si resultado es null,
          // ese archivo ya se marcó como error.

          if (
            resultado === null
          ) {
            return;
          }


          // Como la subida es secuencial,
          // solo puede existir un elemento
          // en estado "subiendo".

          const actual =
            this.estadoSubidas.find(
              item =>
                item.estado ===
                'subiendo'
            );


          if (!actual) {
            return;
          }


          actual.estado =
            'completado';


          this.archivosSubidos++;

        }

      });

  }


  // =====================================================
  // TOTAL ARCHIVOS DE LA SUBIDA
  // =====================================================

  get totalArchivosSubida(): number {

    return this.estadoSubidas.length;

  }


  // =====================================================
  // PROGRESO
  // =====================================================

  get progresoSubida(): number {

    if (
      this.totalArchivosSubida === 0
    ) {

      return 0;

    }


    const procesados =
      this.archivosSubidos +
      this.archivosFallidos;


    return Math.round(
      (
        procesados /
        this.totalArchivosSubida
      ) * 100
    );

  }


  // =====================================================
  // DESCARGAR ARCHIVO
  // =====================================================

  descargarArchivo(
    archivo: ArchivoOrden
  ): void {

    if (!this.ordenId) {
      return;
    }


    this.ordenesService
      .descargarArchivo(
        this.ordenId,
        archivo.id
      )
      .subscribe({

        next: blob => {

          const url =
            URL.createObjectURL(
              blob
            );


          const enlace =
            document.createElement(
              'a'
            );


          enlace.href = url;

          enlace.download =
            archivo.nombre_original;


          document.body.appendChild(
            enlace
          );


          enlace.click();


          document.body.removeChild(
            enlace
          );


          URL.revokeObjectURL(
            url
          );

        },

        error: err => {

          console.error(
            'Error descargando archivo',
            err
          );

          this.notification.showHttpError(
            err
          );

        }

      });

  }


  // =====================================================
  // ELIMINAR ARCHIVO
  // =====================================================

  eliminarArchivo(
    archivo: ArchivoOrden
  ): void {

    if (!this.ordenId) {
      return;
    }


    const dialogRef =
      this.dialog.open(
        ConfirmDeleteFileDialogComponent,
        {

          width: '430px',

          data: {
            nombre:
              archivo.nombre_original
          }

        }
      );


    dialogRef
      .afterClosed()
      .subscribe(
        confirmado => {

          if (!confirmado) {
            return;
          }


          this.confirmarEliminarArchivo(
            archivo
          );

        }
      );

  }


  // =====================================================
  // CONFIRMAR ELIMINACIÓN
  // =====================================================

  private confirmarEliminarArchivo(
    archivo: ArchivoOrden
  ): void {

    if (!this.ordenId) {
      return;
    }


    this.ordenesService
      .eliminarArchivo(
        this.ordenId,
        archivo.id
      )
      .subscribe({

        next: () => {


          // =============================================
          // LIBERAR MINIATURA
          // =============================================

          const preview =
            this.imagenesPreview[
              archivo.id
            ];


          if (preview) {

            URL.revokeObjectURL(
              preview
            );


            delete this.imagenesPreview[
              archivo.id
            ];

          }


          // =============================================
          // ACTUALIZAR LISTADO
          // =============================================

          this.cargarArchivos();


          this.notification.success(
            'Archivo eliminado correctamente'
          );

        },

        error: err => {

          console.error(
            'Error eliminando archivo',
            err
          );

          this.notification.showHttpError(
            err
          );

        }

      });

  }


  // =====================================================
  // FORMATEAR TAMAÑO
  // =====================================================

  formatearTamano(
    bytes: number
  ): string {

    if (
      bytes < 1024
    ) {

      return `${bytes} B`;

    }


    if (
      bytes <
      1024 * 1024
    ) {

      return `${
        (
          bytes / 1024
        ).toFixed(1)
      } KB`;

    }


    return `${
      (
        bytes /
        (
          1024 *
          1024
        )
      ).toFixed(1)
    } MB`;

  }


  // =====================================================
  // PREVIEW DE IMAGEN
  // =====================================================

  cargarPreviewImagen(
    archivo: ArchivoOrden
  ): void {

    if (!this.ordenId) {
      return;
    }


    if (
      !archivo.tipo_mime
        .startsWith('image/')
    ) {
      return;
    }


    if (
      this.imagenesPreview[
        archivo.id
      ]
    ) {
      return;
    }


    this.ordenesService
      .descargarArchivo(
        this.ordenId,
        archivo.id
      )
      .subscribe({

        next: blob => {

          const url =
            URL.createObjectURL(
              blob
            );


          this.imagenesPreview[
            archivo.id
          ] = url;

        },

        error: err => {

          console.error(
            'Error cargando previsualización',
            err
          );

        }

      });

  }


  // =====================================================
  // FILTRAR IMÁGENES
  // =====================================================

  get imagenes(): ArchivoOrden[] {

    return this.archivos.filter(
      archivo =>
        archivo.tipo_mime
          .startsWith('image/')
    );

  }


  // =====================================================
  // FILTRAR DOCUMENTOS
  // =====================================================

  get documentos(): ArchivoOrden[] {

    return this.archivos.filter(
      archivo =>
        !archivo.tipo_mime
          .startsWith('image/')
    );

  }


  // =====================================================
  // VER ARCHIVO
  // =====================================================

  verArchivo(
    archivo: ArchivoOrden
  ): void {

    if (!this.ordenId) {
      return;
    }


    // ===================================================
    // IMAGEN
    // ===================================================

    if (
      archivo.tipo_mime
        .startsWith('image/')
    ) {

      const preview =
        this.imagenesPreview[
          archivo.id
        ];


      // Ya tenemos la imagen cargada

      if (preview) {

        this.imagenVisor =
          preview;

        this.nombreImagenVisor =
          archivo.nombre_original;

        return;

      }


      // No tenemos preview todavía

      this.ordenesService
        .descargarArchivo(
          this.ordenId,
          archivo.id
        )
        .subscribe({

          next: blob => {

            const url =
              URL.createObjectURL(
                blob
              );


            this.imagenesPreview[
              archivo.id
            ] = url;


            this.imagenVisor =
              url;

            this.nombreImagenVisor =
              archivo.nombre_original;

          },

          error: err => {

            console.error(
              'Error abriendo imagen',
              err
            );

            this.notification.showHttpError(
              err
            );

          }

        });


      return;

    }


    // ===================================================
    // PDF / DOCUMENTO
    // ===================================================

    this.ordenesService
      .descargarArchivo(
        this.ordenId,
        archivo.id
      )
      .subscribe({

        next: blob => {

          const url =
            URL.createObjectURL(
              blob
            );


          const ventana =
            window.open(
              url,
              '_blank'
            );


          // Si el navegador bloquea el popup,
          // liberamos inmediatamente.

          if (!ventana) {

            URL.revokeObjectURL(
              url
            );

            return;

          }


          // Damos tiempo a la nueva pestaña
          // para cargar el Blob.

          setTimeout(
            () => {

              URL.revokeObjectURL(
                url
              );

            },
            60_000
          );

        },

        error: err => {

          console.error(
            'Error abriendo documento',
            err
          );

          this.notification.showHttpError(
            err
          );

        }

      });

  }


  // =====================================================
  // CERRAR VISOR
  // =====================================================

  cerrarVisorImagen(): void {

    this.imagenVisor = null;

    this.nombreImagenVisor = '';

  }

}
/** Ficha de orden: coordina cliente, vehículo, personal, piezas y mano de obra. */
