import { ChangeDetectorRef, Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { finalize } from 'rxjs';
import { AutocompleteSelect } from '../../../../shared/components/autocomplete-select/autocomplete-select';

import { FacturaProveedorService } from '../../services/factura-proveedor.service';
import { Proveedor } from '../../../proveedores/models/proveedor';
import { ProveedoresService } from '../../../proveedores/services/proveedores.service';
import { NotificationService } from '../../../../shared/services/notification';

@Component({
  selector: 'app-factura-proveedor-form', standalone: true,
  imports: [CommonModule, RouterLink, ReactiveFormsModule, MatButtonModule, MatCardModule, MatFormFieldModule, MatIconModule, MatInputModule, MatSelectModule, AutocompleteSelect],
  templateUrl: './factura-proveedor-form.html', styleUrl: './factura-proveedor-form.scss',
})
export class FacturaProveedorForm implements OnInit {
  private readonly fb = inject(FormBuilder);
  private readonly router = inject(Router);
  private readonly facturasService = inject(FacturaProveedorService);
  private readonly proveedoresService = inject(ProveedoresService);
  private readonly notification = inject(NotificationService);
  private readonly changeDetector = inject(ChangeDetectorRef);
  proveedores: Proveedor[] = [];
  cargando = false;
  guardando = false;
  readonly form = this.fb.group({
    proveedor_id: [null as number | null, Validators.required],
    numero_factura: ['', [Validators.required, Validators.maxLength(100)]],
    tipo_gasto: ['COMPRA' as const, Validators.required],
    fecha_factura: [this.fechaHoy(), Validators.required],
    fecha_vencimiento: [null as string | null],
    base_imponible: [0, [Validators.required, Validators.min(0)]],
    porcentaje_iva: [21, [Validators.required, Validators.min(0), Validators.max(100)]],
    porcentaje_retencion: [0, [Validators.required, Validators.min(0), Validators.max(100)]],
    observaciones: [''],
    albaranes_ids: [[] as number[]],
  });

  ngOnInit(): void {
    this.cargarDatos();
  }
  get cuotaIva(): number {
    const base = Number(this.form.controls.base_imponible.value ?? 0);
    return Number((base * Number(this.form.controls.porcentaje_iva.value ?? 0) / 100).toFixed(2));
  }
  get cuotaRetencion(): number {
    const base = Number(this.form.controls.base_imponible.value ?? 0);
    return Number((base * Number(this.form.controls.porcentaje_retencion.value ?? 0) / 100).toFixed(2));
  }
  get totalCalculado(): number {
    return Number((Number(this.form.controls.base_imponible.value ?? 0) + this.cuotaIva - this.cuotaRetencion).toFixed(2));
  }
  mostrarProveedor(proveedor: Proveedor): string {
    return proveedor.cif ? `${proveedor.nombre} · ${proveedor.cif}` : proveedor.nombre;
  }
  guardar(): void {
    if (this.guardando) return;
    if (this.form.invalid) { this.form.markAllAsTouched(); return; }
    const value = this.form.getRawValue();
    this.guardando = true;
    this.facturasService.crear({
      proveedor_id: value.proveedor_id!, numero_factura: value.numero_factura!.trim(), tipo_gasto: value.tipo_gasto!, fecha_factura: value.fecha_factura!,
      fecha_vencimiento: value.fecha_vencimiento || null, base_imponible: Number(value.base_imponible), porcentaje_iva: Number(value.porcentaje_iva), porcentaje_retencion: Number(value.porcentaje_retencion),
      observaciones: value.observaciones?.trim() || null, albaranes_ids: [],
    }).pipe(finalize(() => this.guardando = false)).subscribe({
      next: factura => { this.notification.success('Factura de proveedor registrada correctamente.'); void this.router.navigate(['/compras/facturas-proveedor', factura.id]); },
      error: error => { this.notification.showHttpError(error); },
    });
  }
  cancelar(): void { void this.router.navigate(['/compras/facturas-proveedor']); }
  private cargarDatos(): void {
    this.cargando = true;
    let pendientes = 1;
    const finalizar = () => { pendientes--; if (!pendientes) { this.cargando = false; this.actualizarVista(); } };
    this.proveedoresService.getProveedores().subscribe({ next: proveedores => { this.proveedores = proveedores.filter(item => item.activo); finalizar(); }, error: error => { finalizar(); this.notification.showHttpError(error); } });
  }
  private actualizarVista(): void {
    this.changeDetector.markForCheck();
    this.changeDetector.detectChanges();
  }
  private fechaHoy(): string { const fecha = new Date(); return new Date(fecha.getTime() - fecha.getTimezoneOffset() * 60_000).toISOString().slice(0, 10); }
}
/** Formulario de factura proveedor que vincula albaranes confirmados disponibles. */
