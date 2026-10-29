import {
  Component,
  OnInit,
  inject
} from '@angular/core';

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

import { CommonModule } from '@angular/common';

import { MatButtonModule } from '@angular/material/button';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';

import {
  ArticuloStock
} from '../../../stock/models/articulo-stock';

import {
  StockService
} from '../../../stock/services/stock.service';

import {
  LineaPedidoCompra
} from '../../models/pedido-compra';


export interface LineaPedidoCompraDialogData {

  linea?: LineaPedidoCompra;

  proveedorId: number;
}


@Component({
  selector: 'app-linea-pedido-compra-dialog',

  standalone: true,

  imports: [
    CommonModule,
    ReactiveFormsModule,

    MatDialogModule,
    MatButtonModule,
    MatFormFieldModule,
    MatInputModule,
    MatSelectModule
  ],

  template: `
    <h2 mat-dialog-title>

      {{
        data.linea
          ? 'Editar artículo'
          : 'Añadir artículo'
      }}

    </h2>

    <mat-dialog-content>

      <form
        [formGroup]="form"
        class="linea-form">

        @if (!articuloManual) {
        <mat-form-field appearance="outline">

          <mat-label>
            Artículo
          </mat-label>

          <mat-select
            formControlName="articulo_stock_id"
            [disabled]="!!data.linea"
            (selectionChange)="
              seleccionarArticulo(
                $event.value
              )
            ">

            @for (
              articulo of articulos;
              track articulo.id
            ) {

              <mat-option
                [value]="articulo.id">

                {{ articulo.referencia }}
                ·
                {{ articulo.nombre }}

              </mat-option>

            }

          </mat-select>

        </mat-form-field>
        } @else {
        <mat-form-field appearance="outline">
          <mat-label>Referencia</mat-label>
          <input matInput formControlName="referencia">
        </mat-form-field>
        <mat-form-field appearance="outline">
          <mat-label>Descripción</mat-label>
          <input matInput formControlName="descripcion">
        </mat-form-field>
        }

        @if (!data.linea) {
        <button mat-stroked-button type="button" (click)="usarArticuloManual()">
          {{ articuloManual ? 'Elegir del almacén' : 'Artículo nuevo' }}
        </button>
        }


        <mat-form-field
          appearance="outline">

          <mat-label>
            Cantidad
          </mat-label>

          <input
            matInput
            type="number"
            step="0.01"
            formControlName="cantidad_pedida">

        </mat-form-field>


        <mat-form-field
          appearance="outline">

          <mat-label>
            Coste unitario
          </mat-label>

          <input
            matInput
            type="number"
            step="0.01"
            formControlName="coste_unitario">

          <span matTextSuffix>
            €
          </span>

        </mat-form-field>


        <mat-form-field
          appearance="outline">

          <mat-label>
            IVA
          </mat-label>

          <input
            matInput
            type="number"
            step="0.01"
            formControlName="iva">

          <span matTextSuffix>
            %
          </span>

        </mat-form-field>


        <div class="preview-total">

          <span>
            Total estimado
          </span>

          <strong>
            {{
              totalEstimado
              | number:'1.2-2'
            }} €
          </strong>

        </div>

      </form>

    </mat-dialog-content>


    <mat-dialog-actions align="end">

      <button
        mat-button
        type="button"
        (click)="cancelar()">

        Cancelar

      </button>

      <button
        mat-flat-button
        color="primary"
        type="button"
        [disabled]="form.invalid"
        (click)="confirmar()">

        Guardar

      </button>

    </mat-dialog-actions>
  `,

  styles: [`
    .linea-form {
      display: flex;
      flex-direction: column;
      gap: 12px;

      min-width: 400px;
      padding-top: 8px;
    }

    .preview-total {
      display: flex;
      justify-content: space-between;
      align-items: center;

      padding: 12px;

      border-radius: 8px;

      background:
        rgba(0, 0, 0, 0.04);
    }

    .preview-total strong {
      font-size: 18px;
    }
  `]
})
export class LineaPedidoCompraDialog
  implements OnInit {

  private fb =
    inject(FormBuilder);

  private stockService =
    inject(StockService);

  private dialogRef =
    inject(
      MatDialogRef<
        LineaPedidoCompraDialog
      >
    );

  data =
    inject<LineaPedidoCompraDialogData>(
      MAT_DIALOG_DATA
    );


  articulos: ArticuloStock[] = [];
  articuloManual = false;


  form = this.fb.group({

    articulo_stock_id: [
      null as number | null,
      Validators.required
    ],

    referencia: [''],
    descripcion: [''],

    cantidad_pedida: [
      1,
      [
        Validators.required,
        Validators.min(0.01)
      ]
    ],

    coste_unitario: [
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
    ]

  });


  ngOnInit(): void {

    this.cargarArticulos();

    if (this.data.linea) {

      this.form.patchValue({

        articulo_stock_id:
          this.data.linea
            .articulo_stock_id,

        cantidad_pedida:
          this.data.linea
            .cantidad_pedida,

        coste_unitario:
          this.data.linea
            .coste_unitario,

        iva:
          this.data.linea.iva

      });

    }

  }


  cargarArticulos(): void {

    this.stockService
      .getArticulos()
      .subscribe({

        next: articulos => {

          this.articulos =
            articulos.filter(
              articulo => articulo.activo
            );

        }

      });

  }


  seleccionarArticulo(
    articuloId: number
  ): void {

    const articulo =
      this.articulos.find(
        item =>
          item.id === articuloId
      );

    if (!articulo) {
      return;
    }

    this.form.patchValue({

      coste_unitario:
        articulo.coste,

      iva:
        articulo.iva

    });

  }

  usarArticuloManual(): void {
    this.articuloManual = !this.articuloManual;
    const articulo = this.form.controls.articulo_stock_id;
    const referencia = this.form.controls.referencia;
    const descripcion = this.form.controls.descripcion;

    articulo.setValue(null);
    referencia.setValue('');
    descripcion.setValue('');
    articulo.setValidators(this.articuloManual ? [] : [Validators.required]);
    referencia.setValidators(this.articuloManual ? [Validators.required] : []);
    descripcion.setValidators(this.articuloManual ? [Validators.required] : []);
    articulo.updateValueAndValidity();
    referencia.updateValueAndValidity();
    descripcion.updateValueAndValidity();
  }


  get totalEstimado(): number {

    const cantidad =
      Number(
        this.form.value
          .cantidad_pedida ?? 0
      );

    const coste =
      Number(
        this.form.value
          .coste_unitario ?? 0
      );

    const iva =
      Number(
        this.form.value.iva ?? 0
      );

    const subtotal =
      cantidad * coste;

    return (
      subtotal
      +
      subtotal * iva / 100
    );

  }


  cancelar(): void {

    this.dialogRef.close();

  }


  confirmar(): void {

    if (this.form.invalid) {

      this.form.markAllAsTouched();

      return;

    }

    this.dialogRef.close(
      this.form.getRawValue()
    );

  }

}
/** Diálogo de alta o edición de una línea de pedido de proveedor. */
