import { Injectable, inject } from '@angular/core';
import { MatSnackBar } from '@angular/material/snack-bar';
import { Observable } from 'rxjs';
@Injectable({
  providedIn: 'root'
})
export class NotificationService {

  private snackBar = inject(MatSnackBar);

  success(message: string): void {

    this.snackBar.open(
      message,
      'Cerrar',
      {
        duration: 3000,
        horizontalPosition: 'right',
        verticalPosition: 'top'
      }
    );

  }

  error(message: string): void {

    this.snackBar.open(
      message,
      'Cerrar',
      {
        duration: 5000,
        horizontalPosition: 'right',
        verticalPosition: 'top'
      }
    );

  }

  showHttpError(error: any): void {
    const message =
      error?.error?.detail ??
      'Se ha producido un error inesperado.';

    this.error(message);

  }

  info(message: string): void {

  this.snackBar.open(
    message,
    'Cerrar',
    {
      duration: 3000,
      horizontalPosition: 'right',
      verticalPosition: 'top'
    }
  );

}

warning(message: string): void {

  this.snackBar.open(
    message,
    'Cerrar',
    {
      duration: 4000,
      horizontalPosition: 'right',
      verticalPosition: 'top'
    }
  );

  }

}
/** Servicio único para notificaciones de éxito, error y errores HTTP legibles. */
