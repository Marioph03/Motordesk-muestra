import { ChangeDetectorRef, Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSelectModule } from '@angular/material/select';
import { AnalisisExcel, CampoImportacion, MapeoCampo, PreviewImportacion, ResultadoImportacion } from '../../models/importacion-excel';
import { ImportacionesExcelService } from '../../services/importaciones-excel.service';
import { NotificationService } from '../../../../shared/services/notification';

type TipoImportacion = 'clientes' | 'vehiculos' | 'proveedores' | 'articulos';

@Component({ selector: 'app-importar-exportar', standalone: true, imports: [CommonModule, FormsModule, MatButtonModule, MatCardModule, MatFormFieldModule, MatIconModule, MatProgressSpinnerModule, MatSelectModule], templateUrl: './importar-exportar.html', styleUrls: ['./importar-exportar.scss', './importar-exportar-extra.scss'] })
export class ImportarExportar {
  private readonly service = inject(ImportacionesExcelService);
  private readonly notification = inject(NotificationService);
  private readonly cdr = inject(ChangeDetectorRef);
  readonly tipos = [
    { value: 'clientes' as const, label: 'Clientes', icon: 'groups', descripcion: 'Importa clientes desde un archivo Excel.' },
    { value: 'vehiculos' as const, label: 'Vehículos', icon: 'directions_car', descripcion: 'Importa vehículos y vincúlalos con sus propietarios.' },
    { value: 'proveedores' as const, label: 'Proveedores', icon: 'local_shipping', descripcion: 'Migra la base de datos de proveedores.' },
    { value: 'articulos' as const, label: 'Artículos / Stock', icon: 'inventory_2', descripcion: 'Importa referencias y existencias del almacén.' },
  ];
  tipoSeleccionado: TipoImportacion = 'clientes';
  archivoSeleccionado: File | null = null;
  analisis: AnalisisExcel | null = null;
  campos: CampoImportacion[] = [];
  mapeo: Record<string, string | null> = {};
  analizando = false;
  cargandoCampos = false;
  preview: PreviewImportacion | null = null;
  previsualizando = false;
  importando = false;
  exportando = false;
  resultado: ResultadoImportacion | null = null;

  constructor() { this.cargarCampos(); }

  seleccionarTipo(tipo: TipoImportacion): void {
    if (this.tipoSeleccionado === tipo) return;
    this.tipoSeleccionado = tipo;
    this.archivoSeleccionado = null;
    this.analisis = null;
    this.preview = null;
    this.resultado = null;
    this.mapeo = {};
    this.cargarCampos();
  }

  seleccionarArchivo(event: Event): void {
    const input = event.target as HTMLInputElement;
    const archivo = input.files?.[0] ?? null;
    if (!archivo) return;
    if (!archivo.name.toLowerCase().endsWith('.xlsx')) {
      input.value = ''; this.archivoSeleccionado = null;
      this.notification.error('Selecciona un archivo XLSX.');
      return;
    }
    if (archivo.size > 25 * 1024 * 1024) {
      input.value = ''; this.archivoSeleccionado = null;
      this.notification.error('El archivo no puede superar los 25 MB.');
      return;
    }
    this.archivoSeleccionado = archivo;
    this.analisis = null;
    this.preview = null;
    this.resultado = null;
    this.inicializarMapeo();
  }

  analizar(): void {
    if (!this.archivoSeleccionado || this.analizando) return;
    this.analizando = true; this.actualizarVista();
    this.service.analizar(this.archivoSeleccionado).subscribe({
      next: analisis => { this.analisis = analisis; this.analizando = false; this.autodetectarMapeo(); this.actualizarVista(); this.notification.success('Excel analizado correctamente.'); },
      error: error => { this.analizando = false; this.actualizarVista(); this.notification.showHttpError(error); },
    });
  }

  get mapeoValido(): boolean { return this.campos.every(campo => !campo.obligatorio || !!this.mapeo[campo.campo]); }
  get mapeoArray(): MapeoCampo[] { return this.campos.map(campo => ({ campo_motordesk: campo.campo, columna_excel: this.mapeo[campo.campo] ?? null })); }

  previsualizar(): void {
    if (!this.analisis || !this.mapeoValido || this.previsualizando) return;
    this.previsualizando = true; this.preview = null; this.actualizarVista();
    this.service.preview(this.tipoSeleccionado, this.analisis.archivo, this.analisis.hoja_activa, this.mapeoArray).subscribe({
      next: preview => { this.preview = preview; this.previsualizando = false; this.actualizarVista(); },
      error: error => { this.previsualizando = false; this.actualizarVista(); this.notification.showHttpError(error); },
    });
  }

  importar(): void {
    if (!this.analisis || !this.preview || this.preview.validas === 0 || this.importando) return;
    this.importando = true;
    this.resultado = null;
    this.actualizarVista();
    this.service.importar(this.tipoSeleccionado, this.analisis.archivo, this.analisis.hoja_activa, this.mapeoArray).subscribe({
      next: resultado => {
        this.resultado = resultado;
        this.importando = false;
        this.notification.success(`${resultado.importados} registros importados correctamente.`);
        this.previsualizar();
        this.actualizarVista();
      },
      error: error => { this.importando = false; this.actualizarVista(); this.notification.showHttpError(error); },
    });
  }

  cambiarHoja(hoja: string): void {
    if (!this.analisis || hoja === this.analisis.hoja_activa || this.analizando) return;
    this.analizando = true; this.preview = null; this.resultado = null; this.actualizarVista();
    this.service.analizarHoja(this.analisis.archivo, hoja).subscribe({
      next: analisis => { this.analisis = analisis; this.inicializarMapeo(); this.autodetectarMapeo(); this.analizando = false; this.actualizarVista(); },
      error: error => { this.analizando = false; this.actualizarVista(); this.notification.showHttpError(error); },
    });
  }

  exportar(): void {
    if (this.exportando) return;
    this.exportando = true; this.actualizarVista();
    this.service.exportar(this.tipoSeleccionado).subscribe({
      next: archivo => {
        const enlace = document.createElement('a');
        enlace.href = URL.createObjectURL(archivo);
        enlace.download = `motordesk_${this.tipoSeleccionado}.xlsx`;
        enlace.click(); URL.revokeObjectURL(enlace.href);
        this.exportando = false; this.actualizarVista();
      },
      error: error => { this.exportando = false; this.actualizarVista(); this.notification.showHttpError(error); },
    });
  }

  private cargarCampos(): void {
    this.cargandoCampos = true; this.actualizarVista();
    this.service.getCampos(this.tipoSeleccionado).subscribe({
      next: respuesta => { this.campos = respuesta.campos; this.inicializarMapeo(); this.cargandoCampos = false; this.actualizarVista(); },
      error: error => { this.cargandoCampos = false; this.actualizarVista(); this.notification.showHttpError(error); },
    });
  }
  private inicializarMapeo(): void { this.mapeo = Object.fromEntries(this.campos.map(campo => [campo.campo, null])); }
  private autodetectarMapeo(): void {
    if (!this.analisis) return;
    const columnas = this.analisis.columnas.map(columna => ({ original: columna.nombre, normalizada: this.normalizar(columna.nombre) }));
    for (const campo of this.campos) {
      const encontrada = columnas.find(columna => this.aliasCampo(campo.campo).includes(columna.normalizada));
      if (encontrada) this.mapeo[campo.campo] = encontrada.original;
    }
  }
  private aliasCampo(campo: string): string[] {
    const aliases: Record<string, string[]> = {
      nombre: ['nombre', 'cliente', 'nombrecliente', 'razonsocial'], apellidos: ['apellidos', 'apellido'], dni_nif: ['dni', 'nif', 'dninif', 'cif', 'documento'], telefono: ['telefono', 'movil', 'telefono1', 'tlf'], email: ['email', 'correo', 'correoelectronico'], direccion: ['direccion', 'domicilio'], codigo_postal: ['cp', 'codigopostal', 'postal'], localidad: ['localidad', 'poblacion', 'municipio'], provincia: ['provincia'], observaciones: ['observaciones', 'observacion', 'notas', 'comentarios'], matricula: ['matricula'], marca: ['marca'], modelo: ['modelo'], version: ['version'], bastidor: ['bastidor', 'vin'], kilometros: ['kilometros', 'km'], combustible: ['combustible'], cliente_dni_nif: ['dnipropietario', 'nifpropietario', 'cliente', 'clientedni'], nif_cif: ['nif', 'cif', 'nifcif'], referencia: ['referencia', 'ref', 'codigo'], descripcion: ['descripcion'], stock_actual: ['stock', 'stockactual', 'existencias'], stock_minimo: ['stockminimo', 'minimo'], coste_unitario: ['coste', 'costeunitario', 'preciocompra'],
    };
    return aliases[campo] ?? [this.normalizar(campo)];
  }
  private normalizar(valor: string): string { return valor.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase().replace(/[^a-z0-9]/g, ''); }
  private actualizarVista(): void {
    // No forzamos detectChanges durante la creación del componente: Angular
    // puede estar todavía en modo de actualización y lanza una aserción.
    this.cdr.markForCheck();
  }
}
/** Flujo guiado de análisis, mapeo, vista previa e importación de Excel. */
