import { DOCUMENT } from '@angular/common';
import { Injectable, inject } from '@angular/core';

export type TemaAplicacion = 'claro' | 'oscuro';

@Injectable({ providedIn: 'root' })
export class ThemeService {
  private readonly document = inject(DOCUMENT);
  private readonly storageKey = 'motordesk-tema';

  temaActual: TemaAplicacion = 'claro';

  inicializar(): void {
    // Se ejecuta al arrancar para evitar un destello del tema contrario.
    const guardado = localStorage.getItem(this.storageKey);
    this.aplicarTema(guardado === 'oscuro' ? 'oscuro' : 'claro', false);
  }

  aplicarTema(tema: TemaAplicacion, persistir = true): void {
    this.temaActual = tema;
    const raiz = this.document.documentElement;
    // La clase controla variables globales; colorScheme cubre controles nativos.
    raiz.classList.toggle('md-dark-theme', tema === 'oscuro');
    raiz.style.colorScheme = tema === 'oscuro' ? 'dark' : 'light';

    if (persistir) {
      localStorage.setItem(this.storageKey, tema);
    }
  }
}
/** Servicio de preferencia visual persistente entre tema claro y oscuro. */
