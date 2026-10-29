import { HttpInterceptorFn } from '@angular/common/http';
import { timeout } from 'rxjs';

// Ninguna petición de interfaz puede dejar un botón bloqueado indefinidamente.
// Las pantallas ya muestran el error de HTTP y liberan su estado de carga.
// Un minuto permite adjuntos y documentos pesados sin ocultar un servidor caído.
export const requestTimeoutInterceptor: HttpInterceptorFn = (request, next) =>
  next(request).pipe(timeout(60_000));
