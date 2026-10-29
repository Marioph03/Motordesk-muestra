import { Component, inject } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { ThemeService, TemaAplicacion } from '../../../../core/services/theme.service';

@Component({
  selector: 'app-apariencia-config',
  standalone: true,
  imports: [MatButtonModule, MatCardModule, MatIconModule],
  templateUrl: './apariencia-config.html',
  styleUrl: './apariencia-config.scss'
})
export class AparienciaConfig {
  readonly themeService = inject(ThemeService);

  cambiarTema(tema: TemaAplicacion): void {
    this.themeService.aplicarTema(tema);
  }
}
/** Preferencia de tema global: se delega su persistencia en ThemeService. */
