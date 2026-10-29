import {
  Component,
  inject
} from '@angular/core';

import {
  FormArray,
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

import {
  PedidoCompra
} from '../../models/pedido-compra';


export interface RecepcionPedidoDialogData {
  pedido: PedidoCompra;
}


@Component({
  selector: 'app-recepcion-pedido-dialog',

  standalone: true,

  imports: [
    CommonModule,
    ReactiveFormsModule,

    MatDialogModule,
    MatButtonModule,
    MatFormFieldModule,
    MatInputModule
  ],

  template: `
    <h2 mat-dialog-title>
      Recibir mercancía
    </h2>

    <mat-dialog-content>

      <div class="pedido-info">

        <strong>
          {{ data.pedido.numero }}
        </strong>

        <span>
          {{ data.pedido.proveedor.nombre }}
        </span>

      </div>


      <form
        [formGroup]="form">

        <div
          formArrayName="lineas"
          class="lineas">

          @for (
            control of lineas.controls;
            track $index;
            let i = $index
          ) {

            <div
              class="linea"
              [formGroupName]="i">

              <div class="articulo">

                <strong>
                  {{
                    data.pedido.lineas[i]
                      .referencia
                  }}
                </strong>

                <span>
                  {{
                    data.pedido.lineas[i]
                      .descripcion
                  }}
                </span>

              </div>


              <div class="dato">

                <span>
                  Pedido
                </span>

                <strong>
                  {{
                    data.pedido.lineas[i]
                      .cantidad_pedida
                  }}
                </strong>

              </div>


              <div class="dato">

                <span>
                  Recibido
                </span>

                <strong>
                  {{
                    data.pedido.lineas[i]
                      .cantidad_recibida
                  }}
                </strong>

              </div>


              <div class="dato">

                <span>
                  Pendiente
                </span>

                <strong>
                  {{
                    pendiente(
                      data.pedido.lineas[i]
                    )
                  }}
                </strong>

              </div>


              <mat-form-field
                appearance="outline">

                <mat-label>
                  Recibir ahora
                </mat-label>

                <input
                  matInput
                  type="number"
                  step="0.01"
                  formControlName="cantidad">

              </mat-form-field>

            </div>

          }

        </div>


        <mat-form-field
          appearance="outline"
          class="full-width">

          <mat-label>
            Observaciones
          </mat-label>

          <textarea
            matInput
            rows="3"
            formControlName="observaciones">
          </textarea>

        </mat-form-field>

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
        (click)="confirmar()">

        Confirmar recepción

      </button>

    </mat-dialog-actions>
  `,

  styles: [`
    .pedido-info {
      display: flex;
      flex-direction: column;
      gap: 3px;
      margin-bottom: 18px;
    }

    .pedido-info span {
      opacity: 0.7;
    }

    .lineas {
      display: flex;
      flex-direction: column;
      gap: 10px;
    }

    .linea {
      display: grid;
      grid-template-columns:
        minmax(220px, 2fr)
        90px
        90px
        90px
        140px;

      gap: 12px;
      align-items: center;

      padding: 12px;

      border: 1px solid
        rgba(0, 0, 0, 0.10);

      border-radius: 8px;
    }

    .articulo,
    .dato {
      display: flex;
      flex-direction: column;
      gap: 2px;
    }

    .articulo span,
    .dato span {
      font-size: 12px;
      opacity: 0.65;
    }

    .full-width {
      width: 100%;
      margin-top: 18px;
    }

    @media (max-width: 850px) {

      .linea {
        grid-template-columns: 1fr;
      }

    }
  `]
})
export class RecepcionPedidoDialog {

  private fb =
    inject(FormBuilder);

  private dialogRef =
    inject(
      MatDialogRef<
        RecepcionPedidoDialog
      >
    );

  data =
    inject<RecepcionPedidoDialogData>(
      MAT_DIALOG_DATA
    );


  form = this.fb.group({

    lineas: this.fb.array(
      this.data.pedido.lineas.map(
        linea => {

          const pendiente =
            Number(linea.cantidad_pedida)
            -
            Number(linea.cantidad_recibida);

          return this.fb.group({

            linea_id: [
              linea.id
            ],

            cantidad: [
              pendiente,
              [
                Validators.min(0),
                Validators.max(pendiente)
              ]
            ]

          });

        }
      )
    ),

    observaciones: ['']

  });


  get lineas(): FormArray {

    return this.form.controls
      .lineas as FormArray;

  }


  pendiente(
    linea: {
      cantidad_pedida: number;
      cantidad_recibida: number;
    }
  ): number {

    return (
      Number(linea.cantidad_pedida)
      -
      Number(linea.cantidad_recibida)
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

    const valores =
      this.form.getRawValue();

    const lineas =
      valores.lineas
        .filter(
          linea =>
            Number(linea.cantidad) > 0
        )
        .map(
          linea => ({
            linea_id:
              Number(linea.linea_id),

            cantidad:
              Number(linea.cantidad)
          })
        );

    if (lineas.length === 0) {
      return;
    }

    this.dialogRef.close({

      lineas,

      observaciones:
        valores.observaciones
        ?.trim()
        || null

    });

  }

}
/** Diálogo de recepción parcial que propone únicamente cantidades pendientes. */
