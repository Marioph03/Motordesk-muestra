import {
  Component,
  OnInit,
  inject
} from '@angular/core';

import { CommonModule } from '@angular/common';

import {
  FormBuilder,
  ReactiveFormsModule,
  Validators
} from '@angular/forms';

import {
  ActivatedRoute,
  Router
} from '@angular/router';

import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatIconModule } from '@angular/material/icon';
import { MatDividerModule } from '@angular/material/divider';
import { MatTableModule } from '@angular/material/table';

import { StockService } from '../../services/stock.service';

import { ArticuloStock } from '../../models/articulo-stock';
import { ArticuloStockCreate } from '../../models/articulo-stock-create';
import { ArticuloStockUpdate } from '../../models/articulo-stock-update';
import { MovimientoStock } from '../../models/movimiento-stock';
import { MatDialog } from '@angular/material/dialog';

import { Proveedor } from '../../../proveedores/models/proveedor';
import { ProveedoresService } from '../../../proveedores/services/proveedores.service';

import {StockMovimientoDialog} from '../stock-movimiento-dialog/stock-movimiento-dialog';
import { AutocompleteSelect } from '../../../../shared/components/autocomplete-select/autocomplete-select';

import {
  NotificationService
} from '../../../../shared/services/notification';
import { AuthService } from '../../../../core/auth/auth.service';


@Component({
  selector: 'app-articulo-stock-form',

  standalone: true,

  imports: [
    CommonModule,
    ReactiveFormsModule,

    MatButtonModule,
    MatCardModule,
    MatFormFieldModule,
    MatInputModule,
    MatSelectModule,
    MatIconModule,
    MatDividerModule,
    MatTableModule
    ,AutocompleteSelect
  ],

  templateUrl: './articulo-stock-form.html',

  styleUrl: './articulo-stock-form.scss'
})
export class ArticuloStockForm implements OnInit {

  private fb = inject(FormBuilder);

  private stockService =
    inject(StockService);

  private proveedoresService =
    inject(ProveedoresService);

  private notification =
    inject(NotificationService);

  readonly authService = inject(AuthService);

  private route =
    inject(ActivatedRoute);

  private router =
    inject(Router);

  private dialog =
  inject(MatDialog);


  isEditMode = false;
  esProductoVario = false;

  articuloId?: number;

  articulo?: ArticuloStock;

  movimientos: MovimientoStock[] = [];

  proveedores: Proveedor[] = [];

  etiquetaProveedor = (proveedor: Proveedor): string =>
    `${proveedor.nombre} · ${proveedor.cif}`;


  displayedColumnsMovimientos = [
    'fecha',
    'tipo',
    'cantidad',
    'stock_anterior',
    'stock_resultante',
    'motivo'
  ];


  form = this.fb.group({

    referencia: [
      '',
      Validators.required
    ],

    nombre: [
      '',
      Validators.required
    ],

    descripcion: [''],

    marca: [''],

    categoria: [''],

    ubicacion: [''],

    coste: [
      0,
      [
        Validators.required,
        Validators.min(0)
      ]
    ],

    precio_venta: [
      0,
      [
        Validators.required,
        Validators.min(0)
      ]
    ],

    iva: [
      21,
      [
        Validators.required,
        Validators.min(0)
      ]
    ],

    stock_inicial: [
      0,
      Validators.min(0)
    ],

    stock_minimo: [
      0,
      Validators.min(0)
    ],

    activo: [
      true
    ],

    proveedor_habitual_id: [
      null as number | null
    ],

    controla_stock: [true]

  });


  ngOnInit(): void {

    this.esProductoVario = this.route.snapshot.data['controlaStock'] === false;
    if (this.esProductoVario) this.form.controls.controla_stock.setValue(false);

    this.cargarProveedores();

    const id =
      this.route.snapshot.paramMap.get('id');

    if (id) {

      this.isEditMode = true;

      this.articuloId = Number(id);

      this.cargarArticulo();

    }

  }


  cargarArticulo(): void {

    if (!this.articuloId) {
      return;
    }

    this.stockService
      .getArticulo(
        this.articuloId
      )
      .subscribe({

        next: articulo => {

          this.articulo = articulo;

          this.form.patchValue({

            referencia:
              articulo.referencia,

            nombre:
              articulo.nombre,

            descripcion:
              articulo.descripcion ?? '',

            marca:
              articulo.marca ?? '',

            categoria:
              articulo.categoria ?? '',

            ubicacion:
              articulo.ubicacion ?? '',

            coste:
              articulo.coste,

            precio_venta:
              articulo.precio_venta,

            iva:
              articulo.iva,

            stock_minimo:
              articulo.stock_minimo,

            activo:
              articulo.activo,

            proveedor_habitual_id:
              articulo.proveedor_habitual_id ?? null,

            controla_stock: articulo.controla_stock

          });

          this.form.controls
            .stock_inicial
            .disable();

          this.cargarMovimientos();

        },

        error: err => {

          this.notification.showHttpError(
            err
          );

          void this.router.navigate([
            '/stock'
          ]);

        }

      });

  }


  cargarProveedores(): void {

    this.proveedoresService
      .getProveedores()
      .subscribe({

        next: proveedores => {
          this.proveedores = proveedores;
        },

        error: err => this.notification.showHttpError(err)

      });

  }


  cargarMovimientos(): void {

    if (!this.articuloId) {
      return;
    }

    this.stockService
      .getMovimientos(
        this.articuloId
      )
      .subscribe({

        next: movimientos => {

          this.movimientos =
            movimientos;

        },

        error: err => {

          this.notification.showHttpError(
            err
          );

        }

      });

  }


  guardar(): void {

    // Mostramos y enviamos siempre la misma forma de la referencia. El
    // backend mantiene la comprobación definitiva frente a duplicados.
    const referencia = (
      this.form.controls.referencia.value ?? ''
    ).trim().toUpperCase();

    this.form.controls.referencia.setValue(
      referencia
    );

    if (this.form.invalid) {

      this.form.markAllAsTouched();

      return;

    }

    if (this.isEditMode) {

      const datos: ArticuloStockUpdate = {

        referencia:
          this.form.value.referencia!,

        nombre:
          this.form.value.nombre!,

        descripcion:
          this.form.value.descripcion ?? '',

        marca:
          this.form.value.marca ?? '',

        categoria:
          this.form.value.categoria ?? '',

        ubicacion:
          this.form.value.ubicacion ?? '',

        coste:
          this.form.value.coste!,

        precio_venta:
          this.form.value.precio_venta!,

        iva:
          this.form.value.iva!,

        stock_minimo:
          this.form.value.stock_minimo!,

        activo:
          this.form.value.activo!,

        proveedor_habitual_id:
          this.form.value.proveedor_habitual_id ?? null,

        controla_stock: this.form.value.controla_stock!

      };

      this.stockService
        .actualizarArticulo(
          this.articuloId!,
          datos
        )
        .subscribe({

          next: articulo => {

            this.articulo = articulo;

            this.notification.success(
              'Artículo actualizado correctamente.'
            );

            this.cargarArticulo();

          },

          error: err => {

            this.notification.showHttpError(
              err
            );

          }

        });

      return;
    }


    const datos: ArticuloStockCreate = {

      referencia:
        this.form.value.referencia!,

      nombre:
        this.form.value.nombre!,

      descripcion:
        this.form.value.descripcion ?? '',

      marca:
        this.form.value.marca ?? '',

      categoria:
        this.form.value.categoria ?? '',

      ubicacion:
        this.form.value.ubicacion ?? '',

      coste:
        this.form.value.coste!,

      precio_venta:
        this.form.value.precio_venta!,

      iva:
        this.form.value.iva!,

      stock_inicial:
        this.form.value.stock_inicial!,

      stock_minimo:
        this.form.value.stock_minimo!,

      activo:
        this.form.value.activo!,

      proveedor_habitual_id:
        this.form.value.proveedor_habitual_id ?? null,

      controla_stock: this.esProductoVario ? false : this.form.value.controla_stock!

    };


    this.stockService
      .crearArticulo(
        datos
      )
      .subscribe({

        next: articulo => {

          this.notification.success(
            'Artículo creado correctamente.'
          );

          void this.router.navigate([
            '/stock',
            articulo.id
          ]);

        },

        error: err => {

          this.notification.showHttpError(
            err
          );

        }

      });

  }


  cancelar(): void {

    void this.router.navigate([
      '/stock'
    ]);

  }

  private abrirDialogoMovimiento(
  titulo: string,
  requiereMotivo: boolean,
  accion: (
    cantidad: number,
    motivo?: string
  ) => void
): void {

  const dialogRef =
    this.dialog.open(
      StockMovimientoDialog,
      {
        width: '430px',

        data: {
          titulo,
          requiereMotivo
        }
      }
    );

  dialogRef
    .afterClosed()
    .subscribe(resultado => {

      if (!resultado) {
        return;
      }

      accion(
        resultado.cantidad,
        resultado.motivo
      );

    });

  }

  registrarEntrada(): void {

  if (!this.articuloId) {
    return;
  }

  this.abrirDialogoMovimiento(
    'Registrar entrada de stock',
    false,
    (
      cantidad,
      motivo
    ) => {

      this.stockService
        .entrada(
          this.articuloId!,
          cantidad,
          motivo
        )
        .subscribe({

          next: () => {

            this.notification.success(
              'Entrada registrada correctamente.'
            );

            this.cargarArticulo();

          },

          error: err => {

            this.notification.showHttpError(
              err
            );

          }

        });

    }
  );

  }

  registrarSalida(): void {

  if (!this.articuloId) {
    return;
  }

  this.abrirDialogoMovimiento(
    'Registrar salida de stock',
    false,
    (
      cantidad,
      motivo
    ) => {

      this.stockService
        .salida(
          this.articuloId!,
          cantidad,
          motivo
        )
        .subscribe({

          next: () => {

            this.notification.success(
              'Salida registrada correctamente.'
            );

            this.cargarArticulo();

          },

          error: err => {

            this.notification.showHttpError(
              err
            );

          }

        });

    }
  );

  }

  ajustePositivo(): void {

  if (!this.articuloId) {
    return;
  }

  this.abrirDialogoMovimiento(
    'Ajuste positivo de stock',
    true,
    (
      cantidad,
      motivo
    ) => {

      this.stockService
        .ajustePositivo(
          this.articuloId!,
          cantidad,
          motivo!
        )
        .subscribe({

          next: () => {

            this.notification.success(
              'Ajuste positivo registrado.'
            );

            this.cargarArticulo();

          },

          error: err => {

            this.notification.showHttpError(
              err
            );

          }

        });

    }
  );

  }

  ajusteNegativo(): void {

  if (!this.articuloId) {
    return;
  }

  this.abrirDialogoMovimiento(
    'Ajuste negativo de stock',
    true,
    (
      cantidad,
      motivo
    ) => {

      this.stockService
        .ajusteNegativo(
          this.articuloId!,
          cantidad,
          motivo!
        )
        .subscribe({

          next: () => {

            this.notification.success(
              'Ajuste negativo registrado.'
            );

            this.cargarArticulo();

          },

          error: err => {

            this.notification.showHttpError(
              err
            );

          }

        });

    }
  );

  }

}
/** Formulario de artículo: los cambios de existencias se realizan mediante movimientos. */
