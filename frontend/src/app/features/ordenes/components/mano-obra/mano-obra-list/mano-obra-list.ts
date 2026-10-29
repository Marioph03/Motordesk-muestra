import {
  Component,
  EventEmitter,
  Input,
  OnChanges,
  Output,
  inject,
  ChangeDetectorRef
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

import { ManoObra } from '../../../models/mano-obra';
import { ManoObraService } from '../../../services/mano-obra.service';
import { ManoObraDialog } from '../mano-obra-dialog/mano-obra-dialog';

@Component({
  selector: 'app-mano-obra-list',
  standalone: true,
  imports: [
    MatTableModule,
    MatButtonModule,
    MatIconModule,
    MatCard,
    MatCardContent,
    DecimalPipe
  ],
  templateUrl: './mano-obra-list.html',
  styleUrl: './mano-obra-list.scss'
})
export class ManoObraList implements OnChanges {

  @Input({ required: true }) ordenId!: number;

  @Input() soloLectura = false;
  @Input() esGarantia = false;

  @Output() actualizado = new EventEmitter<void>();

  private manoObraService = inject(ManoObraService);

  private dialog = inject(MatDialog);

  manoObra: ManoObra[] = [];

  private cdr = inject(ChangeDetectorRef);

  readonly instanceId = Math.random().toString(36).substring(2, 8);

  displayedColumns: string[] = [
  'concepto',
  'horas',
  'precioHora',
  'descuento',
  'cobertura',
  'total',
  'acciones'
  ];

  ngOnChanges(): void {
    this.displayedColumns = this.esGarantia
      ? ['concepto', 'codigoManoObra', 'horas', 'precioHora', 'descuento', 'cobertura', 'total', 'acciones']
      : ['concepto', 'horas', 'precioHora', 'descuento', 'total', 'acciones'];
    if (this.ordenId) this.cargar();
  }

  cargar(): void {

  this.manoObraService
    .getByOrden(this.ordenId)
    .subscribe({

      next: data => {

        this.manoObra = [...data];

        this.cdr.detectChanges();

      },

      error: err => console.error(err)

    });

  }

  abrirDialogoNuevaOperacion(): void {

    const dialogRef = this.dialog.open(
      ManoObraDialog,
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

  editar(linea: ManoObra): void {

    const dialogRef = this.dialog.open(
      ManoObraDialog,
      {
        width: '600px',
        data: {
          ordenId: this.ordenId,
          linea
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

  eliminar(linea: ManoObra): void {

    const confirmar = confirm(
      `¿Deseas eliminar la operación "${linea.concepto}"?`
    );

    if (!confirmar) {
      return;
    }

    this.manoObraService
      .delete(
        this.ordenId,
        linea.id
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
/** Subcomponente que muestra y administra trabajos de mano de obra de una orden. */
