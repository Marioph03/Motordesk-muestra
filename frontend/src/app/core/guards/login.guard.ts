import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { catchError, map, of } from 'rxjs';

import { BootstrapService } from '../services/bootstrap.service';


/** Evita que una instalacion nueva pueda saltarse visualmente el instalador. */
export const loginGuard: CanActivateFn = () => {
  const bootstrapService = inject(BootstrapService);
  const router = inject(Router);

  return bootstrapService.obtenerEstado().pipe(
    map(estado => (
      estado.requiere_configuracion
        ? router.createUrlTree(['/setup'])
        : true
    )),
    // Si el backend no responde, el login sigue accesible para no bloquear UX.
    catchError(() => of(true)),
  );
};
