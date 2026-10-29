import { ChangeDetectorRef, Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { NotificationService } from '../../../../shared/services/notification';
import { ImportacionesExcelService } from '../../services/importaciones-excel.service';
import { AnalisisExcel } from '../../models/importacion-excel';

@Component({ selector: 'app-datos-config', standalone: true, imports: [CommonModule, RouterLink, MatButtonModule, MatCardModule, MatIconModule, MatProgressSpinnerModule], templateUrl: './datos-config.html', styleUrl: './datos-config.scss' })
export class DatosConfig {
  private readonly service = inject(ImportacionesExcelService);
  private readonly notification = inject(NotificationService);
  private readonly cdr = inject(ChangeDetectorRef);
  analisis?: AnalisisExcel;
  analizando = false;
  archivo?: File;

  seleccionarArchivo(event: Event): void {
    const archivo = (event.target as HTMLInputElement).files?.[0];
    if (!archivo) return;
    if (!archivo.name.toLowerCase().endsWith('.xlsx')) {
      this.notification.error('Selecciona un archivo XLSX válido.');
      return;
    }
    this.archivo = archivo;
    this.analisis = undefined;
  }

  analizar(): void {
    if (!this.archivo || this.analizando) return;
    this.analizando = true;
    this.actualizarVista();
    this.service.analizar(this.archivo).subscribe({
      next: analisis => { this.analisis = analisis; this.analizando = false; this.actualizarVista(); },
      error: error => { this.analizando = false; this.actualizarVista(); this.notification.showHttpError(error); },
    });
  }

  columnasMuestra(): string[] { return this.analisis?.columnas.map(item => item.nombre) ?? []; }
  private actualizarVista(): void { this.cdr.markForCheck(); this.cdr.detectChanges(); }
}
/** Pantalla de migración de datos, accesible desde la portada de configuración. */
