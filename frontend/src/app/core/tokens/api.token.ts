import { InjectionToken } from '@angular/core';

export const API_URL = new InjectionToken<string>('API_URL');
/** Token de inyección que centraliza la URL base de la API por entorno. */
