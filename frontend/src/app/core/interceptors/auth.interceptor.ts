import {
  HttpErrorResponse,
  HttpInterceptorFn
} from '@angular/common/http';
import { inject } from '@angular/core';
import { catchError, throwError } from 'rxjs';

import { AuthService } from '../auth/auth.service';

export const authInterceptor: HttpInterceptorFn = (req, next) => {

  const authService = inject(AuthService);

  const token = authService.getToken();

  if (!token) {
    return next(req);
  }

  const clonedRequest = req.clone({

    setHeaders: {

      Authorization: `Bearer ${token}`

    }

  });

  return next(clonedRequest).pipe(
    catchError((error: unknown) => {
      const esEndpointAcceso = /\/auth\/(login|register)/.test(req.url);

      if (
        error instanceof HttpErrorResponse
        && error.status === 401
        && !esEndpointAcceso
      ) {
        // El servidor es la autoridad real para determinar la validez del JWT.
        // Al rechazarlo, eliminamos cualquier estado local y volvemos al acceso.
        authService.finalizarSesionCaducada();
      }

      return throwError(() => error);
    })
  );

};
/** Interceptor que adjunta JWT y reacciona de forma global ante respuestas 401. */
