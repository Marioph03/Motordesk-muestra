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
  LineaPedidoCompra
} from '../../models/pedido-compra';

import {
  RecepcionPedidoDialog
} from '../recepcion-pedido-dialog/recepcion-pedido-dialog';

import {
  ActivatedRoute,
  Router,
  RouterLink
} from '@angular/router';

import {
  MatDialog
} from '@angular/material/dialog';

import {
  LineaPedidoCompraDialog
} from '../linea-pedido-compra-dialog/linea-pedido-compra-dialog';

import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatDividerModule } from '@angular/material/divider';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatTableModule } from '@angular/material/table';
import { MatChipsModule } from '@angular/material/chips';
import { finalize } from 'rxjs';

import {
  PedidoCompra
} from '../../models/pedido-compra';

import {
  PedidosCompraService
} from '../../services/pedidos-compra.service';

import {
  NotificationService
} from '../../../../shared/services/notification';

import {
  ProveedoresService
} from '../../../proveedores/services/proveedores.service';

import {
  Proveedor
} from '../../../proveedores/models/proveedor';
import { AutocompleteSelect } from '../../../../shared/components/autocomplete-select/autocomplete-select';
import { AuthService } from '../../../../core/auth/auth.service';


@Component({
  selector: 'app-pedido-compra-form',

  standalone: true,

  imports: [
    CommonModule,
    ReactiveFormsModule,
    RouterLink,

    MatButtonModule,
    MatCardModule,
    MatDividerModule,
    MatFormFieldModule,
    MatIconModule,
    MatInputModule,
    MatSelectModule,
    MatTableModule,
    MatChipsModule,
    AutocompleteSelect
  ],

  templateUrl: './pedido-compra-form.html',
  styleUrl: './pedido-compra-form.scss'
})
export class PedidoCompraForm implements OnInit {

  private fb = inject(FormBuilder);

  private pedidosService =
    inject(PedidosCompraService);

  private proveedorService =
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


  pedido?: PedidoCompra;

  pedidoId?: number;

  proveedores: Proveedor[] = [];

  etiquetaProveedor = (proveedor: Proveedor): string =>
    `${proveedor.nombre} · ${proveedor.cif}`;

  isEditMode = false;

  loading = false;
  guardando = false;


  displayedColumns = [
    'referencia',
    'descripcion',
    'cantidad',
    'recibida',
    'coste',
    'iva',
    'total',
    'acciones'
  ];


  form = this.fb.group({

    proveedor_id: [
      null as number | null,
      Validators.required
    ],

    observaciones: ['']

  });


  ngOnInit(): void {

    this.cargarProveedores();

    const id =
      this.route.snapshot
        .paramMap
        .get('id');

    if (id) {

      this.isEditMode = true;

      this.pedidoId = Number(id);

      this.cargarPedido();

    }

  }


  cargarProveedores(): void {

    this.proveedorService
      .getProveedores()
      .subscribe({

        next: proveedores => {

          this.proveedores =
            proveedores.filter(
              proveedor =>
                proveedor.activo
            );

        },

        error: err => {

          this.notification
            .showHttpError(err);

        }

      });

  }


  cargarPedido(): void {

    if (!this.pedidoId) {
      return;
    }

    this.loading = true;

    this.pedidosService
      .getPedido(this.pedidoId)
      .subscribe({

        next: pedido => {

          this.pedido = pedido;

          this.form.patchValue({

            proveedor_id:
              pedido.proveedor_id,

            observaciones:
              pedido.observaciones ?? ''

          });

          if (
            pedido.estado !== 'BORRADOR'
          ) {

            this.form.disable();

          }

          this.loading = false;

        },

        error: err => {

          this.loading = false;

          this.notification
            .showHttpError(err);

        }

      });

  }


  guardar(): void {

    if (this.form.invalid || this.guardando) {

      this.form.markAllAsTouched();

      return;

    }


    if (!this.isEditMode) {
      this.guardando = true;

      this.pedidosService
        .crearPedido({

          proveedor_id:
            this.form.value
              .proveedor_id!,

          observaciones:
            this.form.value
              .observaciones ?? ''

        })
        .pipe(finalize(() => this.guardando = false))
        .subscribe({

          next: pedido => {

            this.notification.success(
              'Pedido creado correctamente.'
            );

            void this.router.navigate([
              '/compras/pedidos',
              pedido.id
            ]);

          },

          error: err => {

            this.notification
              .showHttpError(err);

          }

        });

      return;
    }

    this.guardando = true;
    this.pedidosService
      .actualizarPedido(
        this.pedidoId!,
        {
          proveedor_id:
            this.form.value
              .proveedor_id!,

          observaciones:
            this.form.value
              .observaciones ?? ''
        }
      )
      .pipe(finalize(() => this.guardando = false))
      .subscribe({

        next: () => {

          this.notification.success(
            'Pedido actualizado correctamente.'
          );

          this.cargarPedido();

        },

        error: err => {

          this.notification
            .showHttpError(err);

        }

      });

  }


  enviarPedido(): void {

    if (!this.pedidoId) {
      return;
    }

    this.pedidosService
      .enviarPedido(
        this.pedidoId
      )
      .subscribe({

        next: () => {

          this.notification.success(
            'Pedido enviado correctamente.'
          );

          this.cargarPedido();

        },

        error: err => {

          this.notification
            .showHttpError(err);

        }

      });

  }


  cancelarPedido(): void {

    if (!this.pedidoId) {
      return;
    }

    this.pedidosService
      .cancelarPedido(
        this.pedidoId
      )
      .subscribe({

        next: () => {

          this.notification.success(
            'Pedido cancelado.'
          );

          this.cargarPedido();

        },

        error: err => {

          this.notification
            .showHttpError(err);

        }

      });

  }


  volver(): void {

    void this.router.navigate([
      '/compras/pedidos'
    ]);

  }


  get editable(): boolean {

    return (
      !this.pedido
      ||
      this.pedido.estado === 'BORRADOR'
    );

  }


  get puedeRecibir(): boolean {

    return (
      this.pedido?.estado === 'ENVIADO'
      ||
      this.pedido?.estado
        === 'RECIBIDO_PARCIAL'
    );

  }

  agregarLinea(): void {

  if (
    !this.pedidoId
    ||
    !this.pedido
  ) {
    return;
  }

  const dialogRef =
    this.dialog.open(
      LineaPedidoCompraDialog,
      {
        width: '500px',

        data: {
          proveedorId:
            this.pedido.proveedor_id
        }
      }
    );

  dialogRef
    .afterClosed()
    .subscribe(resultado => {

      if (!resultado) {
        return;
      }

      this.pedidosService
        .añadirLinea(
          this.pedidoId!,
          resultado
        )
        .subscribe({

          next: () => {

            this.notification.success(
              'Artículo añadido al pedido.'
            );

            this.cargarPedido();

          },

          error: err => {

            this.notification
              .showHttpError(err);

          }

        });

    });

  }

  editarLinea(
  linea: LineaPedidoCompra
): void {

  if (!this.pedido) {
    return;
  }

  const dialogRef =
    this.dialog.open(
      LineaPedidoCompraDialog,
      {
        width: '500px',

        data: {
          proveedorId:
            this.pedido.proveedor_id,

          linea
        }
      }
    );

  dialogRef
    .afterClosed()
    .subscribe(resultado => {

      if (!resultado) {
        return;
      }

      this.pedidosService
        .actualizarLinea(
          linea.id,
          {
            cantidad_pedida:
              resultado.cantidad_pedida,

            coste_unitario:
              resultado.coste_unitario,

            iva:
              resultado.iva
          }
        )
        .subscribe({

          next: () => {

            this.notification.success(
              'Artículo actualizado.'
            );

            this.cargarPedido();

          },

          error: err => {

            this.notification
              .showHttpError(err);

          }

        });

    });

  }

  eliminarLinea(
  linea: LineaPedidoCompra
): void {

  const confirmar =
    window.confirm(
      `¿Eliminar ${linea.descripcion} del pedido?`
    );

  if (!confirmar) {
    return;
  }

  this.pedidosService
    .eliminarLinea(
      linea.id
    )
    .subscribe({

      next: () => {

        this.notification.success(
          'Artículo eliminado del pedido.'
        );

        this.cargarPedido();

      },

      error: err => {

        this.notification
          .showHttpError(err);

      }

    });

  }

  registrarAlbaran(): void {

    if (!this.pedidoId) {
      return;
    }

    void this.router.navigate(
      ['/compras/albaranes/nuevo'],
      {
        queryParams: {
          pedido_id: this.pedidoId
        }
      }
    );

  }

  recibirMercancia(): void {

    if (!this.pedido) {
      return;
    }

  const dialogRef =
    this.dialog.open(
      RecepcionPedidoDialog,
      {
        width: '950px',

        maxWidth: '95vw',

        data: {
          pedido: this.pedido
        }
      }
    );

  dialogRef
    .afterClosed()
    .subscribe(resultado => {

      if (!resultado) {
        return;
      }

      this.pedidosService
        .recibirPedido(
          this.pedido!.id,
          resultado
        )
        .subscribe({

          next: pedido => {

            const mensaje =
              pedido.estado === 'RECIBIDO'
                ? 'Pedido recibido completamente.'
                : 'Recepción parcial registrada correctamente.';

            this.notification.success(
              mensaje
            );

            this.cargarPedido();

          },

          error: err => {

            this.notification
              .showHttpError(err);

          }

        });

    });

  }


  generarPdf(): void {

    if (!this.pedidoId) {
      return;
    }

    this.pedidosService
      .getPdf(this.pedidoId)
      .subscribe({
        next: blob => {
          const url = window.URL.createObjectURL(blob);
          window.open(url, '_blank');
          window.setTimeout(
            () => window.URL.revokeObjectURL(url),
            60_000
          );
        },
        error: err => {
          this.notification.showHttpError(err);
        }
      });

  }

}
/** Ficha de pedido: edición de líneas, envío, recepción y PDF de compra. */
