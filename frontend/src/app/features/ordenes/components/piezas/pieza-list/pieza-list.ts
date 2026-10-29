import {
  Component,
  EventEmitter,
  Input,
  OnChanges,
  Output,
  inject
} from '@angular/core';

import { DecimalPipe } from '@angular/common';

import { MatTableModule } from '@angular/material/table';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import {
  MatCard,
  MatCardContent
} from '@angular/material/card';
import { MatDialog } from '@angular/material/dialog';
import { MatChipsModule } from '@angular/material/chips';

import { Pieza } from '../../../models/pieza';
import { PiezasService } from '../../../services/piezas.service';
import { PiezaDialog } from '../pieza-dialog/pieza-dialog';
import { ChangeDetectorRef } from '@angular/core';

@Component({
  selector: 'app-pieza-list',
  standalone: true,
  imports: [
    MatTableModule,
    MatButtonModule,
    MatIconModule,
    MatChipsModule,
    MatCard,
    MatCardContent,
    DecimalPipe
  ],
  templateUrl: './pieza-list.html',
  styleUrl: './pieza-list.scss'
})
export class PiezaList implements OnChanges {

  @Input({ required: true }) ordenId!: number;

  @Input() soloLectura = false;
  @Input() esGarantia = false;

  @Output() actualizado = new EventEmitter<void>();

  private piezasService = inject(PiezasService);

  private dialog = inject(MatDialog);

  piezas: Pieza[] = [];

  readonly instanceId = Math.random().toString(36).substring(2, 8);

  private cdr = inject(ChangeDetectorRef);

  displayedColumns: string[] = [
  'referencia',
  'descripcion',
  'cantidad',
  'precioUnitario',
  'descuento',
  'cobertura',
  'total',
  'origen',
  'acciones'
  ];

  ngOnChanges(): void {
    this.displayedColumns = this.esGarantia
      ? ['referencia', 'descripcion', 'cantidad', 'precioUnitario', 'descuento', 'cobertura', 'total', 'origen', 'acciones']
      : ['referencia', 'descripcion', 'cantidad', 'precioUnitario', 'descuento', 'total', 'origen', 'acciones'];
    if (this.ordenId) this.cargar();
  }

  cargar(): void {

  this.piezasService
    .getByOrden(this.ordenId)
    .subscribe({

      next: data => {

    this.piezas = [...data];

    queueMicrotask(() => {
      this.cdr.detectChanges();
    });

},

      error: err => console.error(err)

    });

  }

  abrirDialogoNuevaPieza(): void {

    const dialogRef = this.dialog.open(
      PiezaDialog,
      {
        width: '600px',
        data: {
          ordenId: this.ordenId
          ,esGarantia: this.esGarantia
        }
      }
    );

    dialogRef.afterClosed().subscribe(result => {

      if (result) {

        this.cargar();

        this.actualizado.emit();

      }

    });

  }

  editar(pieza: Pieza): void {

    const dialogRef = this.dialog.open(
      PiezaDialog,
      {
        width: '600px',
        data: {
          ordenId: this.ordenId,
          pieza
          ,esGarantia: this.esGarantia
        }
      }
    );

    dialogRef.afterClosed().subscribe(result => {

      if (result) {

        this.cargar();

        this.actualizado.emit();

      }

    });

  }

  eliminar(pieza: Pieza): void {

    const confirmar = confirm(
      `¿Deseas eliminar la pieza "${pieza.descripcion}"?`
    );

    if (!confirmar) {

      return;

    }

    this.piezasService
      .delete(
        this.ordenId,
        pieza.id
      )
      .subscribe({

        next: () => {

          this.cargar();

          this.actualizado.emit();

        },

        error: err => console.error(err)

      });

  }

}
/** Subcomponente que muestra y administra piezas imputadas a una orden. */
