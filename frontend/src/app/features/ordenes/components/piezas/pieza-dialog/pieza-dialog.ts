import { Component, Inject, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import {
  FormBuilder,
  ReactiveFormsModule,
  Validators
} from '@angular/forms';

import {
  MAT_DIALOG_DATA,
  MatDialogModule,
  MatDialogRef
} from '@angular/material/dialog';

import { MatButtonModule } from '@angular/material/button';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';

import { Pieza } from '../../../models/pieza';
import { PiezaCreate } from '../../../models/pieza-create';
import { PiezaUpdate } from '../../../models/pieza-update';
import { PiezasService } from '../../../services/piezas.service';

import { Proveedor } from '../../../../proveedores/models/proveedor';
import { ProveedoresService } from '../../../../proveedores/services/proveedores.service';
import { MatSelectModule } from '@angular/material/select';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { MatIconModule } from '@angular/material/icon';
import { StockService } from '../../../../stock/services/stock.service';
import { ArticuloStock } from '../../../../stock/models/articulo-stock';
import { AutocompleteSelect } from '../../../../../shared/components/autocomplete-select/autocomplete-select';

import { NotificationService } from '../../../../../shared/services/notification';

interface DialogData {
  ordenId: number;
  pieza?: Pieza;
  esGarantia?: boolean;
}

@Component({
  selector: 'app-pieza-dialog',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    MatDialogModule,
    MatButtonModule,
    MatFormFieldModule,
    MatInputModule,
    MatSelectModule
    ,MatCheckboxModule,
    AutocompleteSelect,
    MatIconModule
  ],
  templateUrl: './pieza-dialog.html',
  styleUrl: './pieza-dialog.scss'
})
export class PiezaDialog implements OnInit {

  private fb = inject(FormBuilder);

  private piezasService = inject(PiezasService);

  private proveedoresService = inject(ProveedoresService);

  private stockService = inject(StockService);

  private notification = inject(NotificationService);

  private dialogRef = inject(MatDialogRef<PiezaDialog>);

  proveedores: Proveedor[] = [];

  etiquetaProveedor = (proveedor: Proveedor): string =>
    `${proveedor.nombre} · ${proveedor.cif}`;

  etiquetaArticulo = (articulo: ArticuloStock): string =>
    `${articulo.referencia} · ${articulo.nombre} · Stock: ${articulo.stock_actual}`;

  articulosStock: ArticuloStock[] = [];

  origenPieza: 'MANUAL' | 'ALMACEN' = 'MANUAL';

  cantidadOriginal = 0;

  articuloStockOriginalId: number | null = null;

  isEditMode = false;

  form = this.fb.group({

    descripcion: [
      '',
      Validators.required
    ],

    cantidad: [
      1,
      [
        Validators.required,
        Validators.min(0.01)
      ]
    ],

    precio_unitario: [
      0,
      [
        Validators.required,
        Validators.min(0)
      ]
    ],

    proveedor_id: [null as number | null],

    articulo_stock_id: [null as number | null],

    referencia: [''],

    descuento_porcentaje: [
      0,
      [
        Validators.min(0),
        Validators.max(100)
      ]
    ],
    cubierto_garantia: [false]

  });

  constructor(
    @Inject(MAT_DIALOG_DATA)
    public data: DialogData
  ) {}

  ngOnInit(): void {

    this.isEditMode = !!this.data.pieza;

    if (this.data.pieza?.articulo_stock_id) {
      this.origenPieza = 'ALMACEN';
    }

    if (this.data.pieza) {
      this.cantidadOriginal = Number(this.data.pieza.cantidad);
      this.articuloStockOriginalId =
        this.data.pieza.articulo_stock_id ?? null;
    }

    this.cargarArticulosStock();

    this.proveedoresService
      .getProveedores()
      .subscribe({

        next: proveedores => {

          this.proveedores = proveedores;

        },

        error: err => console.error(err)

      });

    this.form.setValue({

      descripcion: this.data.pieza?.descripcion ?? '',

      cantidad: this.data.pieza?.cantidad ?? 1,

      precio_unitario: this.data.pieza?.precio_unitario ?? 0,

      proveedor_id: this.data.pieza?.proveedor_id ?? null,

      articulo_stock_id: this.data.pieza?.articulo_stock_id ?? null,

      referencia: this.data.pieza?.referencia ?? '',

      descuento_porcentaje: this.data.pieza?.descuento_porcentaje ?? 0,
      cubierto_garantia: this.data.pieza?.cubierto_garantia ?? false

    });

  }

  cargarArticulosStock(): void {
    this.stockService.getArticulos().subscribe({
      next: articulos => {
        this.articulosStock = articulos.filter(
          articulo => articulo.activo && articulo.stock_actual > 0
        );
      },
      error: err => this.notification.showHttpError(err)
    });
  }

  seleccionarArticuloStock(
    articuloId: number | null
  ): void {
    if (!articuloId) {
      return;
    }

    const articulo = this.articulosStock.find(
      item => item.id === articuloId
    );

    if (!articulo) {
      return;
    }

    this.form.patchValue({
      articulo_stock_id: articulo.id,
      referencia: articulo.referencia,
      descripcion: articulo.nombre,
      precio_unitario: articulo.precio_venta
    });
  }

  cambiarOrigen(
    origen: 'MANUAL' | 'ALMACEN'
  ): void {
    this.origenPieza = origen;

    if (origen === 'MANUAL') {
      this.form.patchValue({
        articulo_stock_id: null
      });
    }
  }

  get articuloStockSeleccionado(): ArticuloStock | undefined {
    const articuloId = this.form.value.articulo_stock_id;

    if (!articuloId) {
      return undefined;
    }

    return this.articulosStock.find(
      articulo => articulo.id === articuloId
    );
  }

  get stockDisponible(): number {
    const articulo = this.articuloStockSeleccionado;

    if (!articulo) {
      return 0;
    }

    let disponible = Number(articulo.stock_actual);

    if (
      this.isEditMode
      && articulo.id === this.articuloStockOriginalId
    ) {
      disponible += this.cantidadOriginal;
    }

    return disponible;
  }

  get cantidadSuperaStock(): boolean {
    if (this.origenPieza !== 'ALMACEN') {
      return false;
    }

    const cantidad = Number(this.form.value.cantidad ?? 0);

    return cantidad > this.stockDisponible;
  }

  get importeSinIva(): number {
    const cantidad = Number(this.form.value.cantidad ?? 0);
    const precio = Number(this.form.value.precio_unitario ?? 0);
    const descuento = Number(
      this.form.value.descuento_porcentaje ?? 0
    );

    return cantidad * precio * (1 - descuento / 100);
  }

  guardar(): void {

    if (this.cantidadSuperaStock) {
      this.notification.error(
        `No hay suficiente stock. Disponibles: ${this.stockDisponible}`
      );

      return;
    }

    if (this.form.invalid) {

      this.form.markAllAsTouched();

      return;

    }

    if (this.isEditMode) {

      const valores = this.form.getRawValue();

      const pieza: PiezaUpdate = {
        ...valores,
        articulo_stock_id: valores.articulo_stock_id ?? null
      };

      this.piezasService
        .update(
          this.data.ordenId,
          this.data.pieza!.id,
          pieza
        )
        .subscribe({

          next: () => this.dialogRef.close(true),

          error: err => console.error(err)

        });

    } else {

      const valores = this.form.getRawValue();

      const pieza: PiezaCreate = {
        ...valores,
        articulo_stock_id: valores.articulo_stock_id ?? null
      };

      this.piezasService
        .create(
          this.data.ordenId,
          pieza
        )
        .subscribe({

          next: () => this.dialogRef.close(true),

          error: err => console.error(err)

        });

    }

  }

  cancelar(): void {

    this.dialogRef.close(false);

  }

}
/** Diálogo de selección y cantidades de pieza para una orden de reparación. */
