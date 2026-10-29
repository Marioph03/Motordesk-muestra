import { ApplicationConfig, LOCALE_ID } from '@angular/core';
import { provideRouter } from '@angular/router';
import { provideHttpClient, withInterceptors } from '@angular/common/http';
import { authInterceptor } from './core/interceptors/auth.interceptor';
import { requestTimeoutInterceptor } from './core/interceptors/request-timeout.interceptor';

import { routes } from './app.routes';
import { API_URL } from './core/tokens/api.token';


export const appConfig: ApplicationConfig = {
  providers: [
  {
    provide: LOCALE_ID,
    useValue: 'es-ES'
  },

  provideRouter(routes),

  provideHttpClient(
    withInterceptors([
      authInterceptor,
      requestTimeoutInterceptor,
    ])
  ),

  {
    provide: API_URL,
    useValue: '/backend'
  }

]
};
/** Proveedores globales: router, HTTP y configuración de la aplicación. */
