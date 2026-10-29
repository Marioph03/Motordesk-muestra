import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { catchError, map, of } from 'rxjs';

import { AuthService } from '../auth/auth.service';
import { BootstrapService } from '../services/bootstrap.service';


/** Protege el layout principal segun el estado de la instalacion y la sesion. */
export const bootstrapGuard: CanActivateFn = () => {
  const bootstrapService = inject(BootstrapService);
  const authService = inject(AuthService);
  const router = inject(Router);

  return bootstrapService.obtenerEstado().pipe(
    map(estado => {
      if (estado.requiere_configuracion) {
        return router.createUrlTree(['/setup']);
      }

      if (authService.isLogged()) {
        return true;
      }

      return router.createUrlTree(['/login']);
    }),
    catchError(() => {
      // Sin estado verificable, nunca se muestra el instalador.
      return of(router.createUrlTree(['/login']));
    }),
  );
};
