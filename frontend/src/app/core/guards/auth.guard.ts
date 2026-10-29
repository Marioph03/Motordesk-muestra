import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';

import { AuthService } from '../auth/auth.service';

export const authGuard: CanActivateFn = () => {

  const authService = inject(AuthService);

  const router = inject(Router);

  if (authService.isLogged()) {

    return true;

  }

  router.navigate(['/login']);

  return false;

};
/** Guardia de navegación que exige una sesión válida antes de cargar rutas privadas. */
