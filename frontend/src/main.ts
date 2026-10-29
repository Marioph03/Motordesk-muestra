import { bootstrapApplication } from '@angular/platform-browser';
import { registerLocaleData } from '@angular/common';
import localeEs from '@angular/common/locales/es';
import { appConfig } from './app/app.config';
import { AppComponent } from './app/app';

// Aplica el formato español a fechas, importes y el resto de pipes de Angular.
registerLocaleData(localeEs);

/**
 * Activa el corrector nativo del navegador en español para toda la aplicación.
 * No corrige el texto por su cuenta: solo muestra sugerencias para que el
 * usuario decida. Los campos no textuales (contraseñas, importes, fechas,
 * matrículas configuradas como number, etc.) quedan fuera automáticamente.
 * Un campo concreto puede excluirse con spellcheck="false" o
 * data-no-spellcheck.
 */
function activarRevisionOrtografica(): void {
  const selector = [
    'textarea',
    'input[type="text"]',
    'input[type="search"]',
    'input:not([type])',
    '[contenteditable="true"]'
  ].join(',');

  const configurar = (elemento: Element): void => {
    if (
      elemento.matches('[spellcheck="false"], [data-no-spellcheck]')
    ) {
      return;
    }

    elemento.setAttribute('lang', 'es');
    elemento.setAttribute('spellcheck', 'true');
  };

  const revisarNodo = (nodo: Node): void => {
    if (!(nodo instanceof Element)) {
      return;
    }

    if (nodo.matches(selector)) {
      configurar(nodo);
    }

    nodo.querySelectorAll(selector).forEach(configurar);
  };

  document.querySelectorAll(selector).forEach(configurar);

  new MutationObserver(registros => {
    for (const registro of registros) {
      registro.addedNodes.forEach(revisarNodo);
    }
  }).observe(document.body, {
    childList: true,
    subtree: true
  });
}

/** Abre el selector nativo al pulsar cualquier fecha, no solo su icono. */
function activarCalendarioEnFechas(): void {
  document.addEventListener('click', evento => {
    const campo = evento.target instanceof HTMLInputElement ? evento.target : null;
    if (campo?.type !== 'date' || campo.disabled || campo.readOnly) {
      return;
    }

    try {
      campo.showPicker?.();
    } catch {
      // Navegadores sin selector programable: conservan su comportamiento nativo.
    }
  });
}

activarRevisionOrtografica();
activarCalendarioEnFechas();

bootstrapApplication(AppComponent, appConfig)
  .catch((err) => console.error(err));
