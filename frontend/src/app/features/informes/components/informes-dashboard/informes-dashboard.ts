import { ChangeDetectorRef, Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { finalize, timeout } from 'rxjs';

import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatTabsModule } from '@angular/material/tabs';

import { NotificationService } from '../../../../shared/services/notification';
import { InformeGeneral } from '../../models/informe-general';
import { InformesService } from '../../services/informes.service';
import { ClientesService } from '../../../clientes/services/clientes.service';
import { ProveedoresService } from '../../../proveedores/services/proveedores.service';
import { FacturaProveedorService } from '../../../compras/services/factura-proveedor.service';
import { Cliente } from '../../../clientes/models/cliente';
import { Proveedor } from '../../../proveedores/models/proveedor';
import { FacturaProveedor } from '../../../compras/models/factura-proveedor';

@Component({
  selector: 'app-informes-dashboard',
  standalone: true,
  imports: [
    CommonModule, ReactiveFormsModule, MatButtonModule, MatCardModule,
    MatFormFieldModule, MatIconModule, MatInputModule, MatTabsModule, MatSelectModule
  ],
  templateUrl: './informes-dashboard.html',
  styleUrl: './informes-dashboard.scss'
})
export class InformesDashboard implements OnInit {
  private readonly fb = inject(FormBuilder);
  private readonly informesService = inject(InformesService);
  private readonly clientesService = inject(ClientesService);
  private readonly proveedoresService = inject(ProveedoresService);
  private readonly facturasProveedorService = inject(FacturaProveedorService);
  private readonly notification = inject(NotificationService);
  private readonly cdr = inject(ChangeDetectorRef);

  readonly form = this.fb.nonNullable.group({
    desde: [this.primerDiaMes(), Validators.required],
    hasta: [this.hoy(), Validators.required],
    cliente_id: [null as number | null],
    proveedor_id: [null as number | null],
    gasto_id: [null as number | null],
  });

  informe?: InformeGeneral;
  cargando = false;
  pdfCargando?: string;
  excelCargando?: string;
  clientes: Cliente[] = [];
  proveedores: Proveedor[] = [];
  gastos: FacturaProveedor[] = [];

  ngOnInit(): void {
    this.cargar();
    this.clientesService.getClientesSelect().subscribe({ next: datos => this.clientes = datos });
    this.proveedoresService.getProveedores().subscribe({ next: datos => this.proveedores = datos.filter(item => item.activo) });
    this.facturasProveedorService.listar().subscribe({ next: datos => this.gastos = datos });
  }

  cargar(): void {
    if (this.form.invalid || this.cargando) {
      this.form.markAllAsTouched();
      return;
    }

    const { desde, hasta, cliente_id, proveedor_id, gasto_id } = this.form.getRawValue();
    if (hasta < desde) {
      this.notification.error('La fecha hasta no puede ser anterior a la fecha desde.');
      return;
    }

    this.cargando = true;
    this.informesService.getResumenGeneral(
      `${desde}T00:00:00`,
      `${this.diaSiguiente(hasta)}T00:00:00`,
      { cliente_id, proveedor_id, gasto_id }
    ).pipe(
      timeout(10_000),
      finalize(() => {
        this.cargando = false;
        this.cdr.markForCheck();
      })
    ).subscribe({
      next: informe => this.informe = informe,
      error: error => this.notification.showHttpError(error)
    });
  }

  verPdf(tipo: 'general' | 'facturacion' | 'clientes' | 'compras-gastos'): void {
    if (this.form.invalid || this.pdfCargando) {
      return;
    }

    const { desde, hasta, cliente_id, proveedor_id, gasto_id } = this.form.getRawValue();
    this.pdfCargando = tipo;
    this.informesService.getPdf(
      tipo,
      `${desde}T00:00:00`,
      `${this.diaSiguiente(hasta)}T00:00:00`,
      { cliente_id, proveedor_id, gasto_id }
    ).pipe(finalize(() => {
      this.pdfCargando = undefined;
      this.cdr.markForCheck();
    })).subscribe({
      next: blob => {
        const url = window.URL.createObjectURL(blob);
        window.open(url, '_blank');
        window.setTimeout(() => window.URL.revokeObjectURL(url), 60_000);
      },
      error: error => this.notification.showHttpError(error)
    });
  }

  exportarExcel(tipo: 'facturacion' | 'clientes' | 'compras-gastos'): void {
    if (this.form.invalid || this.excelCargando) {
      return;
    }

    const { desde, hasta, cliente_id, proveedor_id, gasto_id } = this.form.getRawValue();
    this.excelCargando = tipo;
    this.informesService.getExcel(
      tipo,
      `${desde}T00:00:00`,
      `${this.diaSiguiente(hasta)}T00:00:00`,
      { cliente_id, proveedor_id, gasto_id }
    ).pipe(finalize(() => {
      this.excelCargando = undefined;
      this.cdr.markForCheck();
    })).subscribe({
      next: blob => {
        const url = window.URL.createObjectURL(blob);
        const enlace = document.createElement('a');
        enlace.href = url;
        enlace.download = `informe_${tipo}_${desde}_${hasta}.xlsx`;
        enlace.click();
        window.URL.revokeObjectURL(url);
      },
      error: error => this.notification.showHttpError(error)
    });
  }

  numero(valor: number | string | null | undefined): number {
    return Number(valor ?? 0);
  }

  getAlturaFacturacion(total: number | string): number {
    const datos = this.informe?.facturacion.evolucion_diaria ?? [];
    if (!datos.length) {
      return 0;
    }

    const maximo = Math.max(...datos.map(item => this.numero(item.total)));
    if (maximo <= 0) {
      return 0;
    }

    return Math.max(5, (this.numero(total) / maximo) * 100);
  }

  private hoy(): string {
    return this.formatoFecha(new Date());
  }

  private primerDiaMes(): string {
    const fecha = new Date();
    fecha.setDate(1);
    return this.formatoFecha(fecha);
  }

  private diaSiguiente(fecha: string): string {
    const resultado = new Date(`${fecha}T12:00:00`);
    resultado.setDate(resultado.getDate() + 1);
    return this.formatoFecha(resultado);
  }

  private formatoFecha(fecha: Date): string {
    const ano = fecha.getFullYear();
    const mes = String(fecha.getMonth() + 1).padStart(2, '0');
    const dia = String(fecha.getDate()).padStart(2, '0');
    return `${ano}-${mes}-${dia}`;
  }
}
/** Acceso rápido desde Dashboard al informe operativo completo por rango. */
