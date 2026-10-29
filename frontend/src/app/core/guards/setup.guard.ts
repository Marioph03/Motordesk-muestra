import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { catchError, map, of } from 'rxjs';

import { BootstrapService } from '../services/bootstrap.service';


export const setupGuard: CanActivateFn = () => {

  const bootstrapService = inject(BootstrapService);
  const router = inject(Router);

  return bootstrapService.obtenerEstado().pipe(

    map(estado => {

      if (!estado.requiere_configuracion) {

        return router.createUrlTree([
          '/login'
        ]);

      }

      return true;

    }),

    catchError(() => {

      /*
       * No mostramos el asistente si no podemos confirmar
       * que la instalación realmente necesita configurarse.
       */
      return of(
        router.createUrlTree(['/login'])
      );

    })

  );

};
