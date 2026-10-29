import { Injectable, inject } from '@angular/core';
import { MatDialog } from '@angular/material/dialog';
import { map, Observable } from 'rxjs';

import {
  ConfirmDialog,
  ConfirmDialogData,
} from '../components/confirm-dialog/confirm-dialog';


/** Centraliza las confirmaciones antes de acciones con impacto operativo. */
@Injectable({ providedIn: 'root' })
export class ConfirmationService {
  private readonly dialog = inject(MatDialog);

  confirmar(data: ConfirmDialogData): Observable<boolean> {
    return this.dialog.open(ConfirmDialog, {
      data,
      disableClose: true,
      autoFocus: false,
    }).afterClosed().pipe(map(confirmado => confirmado === true));
  }
}
