import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormArray, FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { finalize } from 'rxjs';

import { AlbaranProveedor, LineaAlbaranDevolvible } from '../../models/albaran-proveedor';
import { AlbaranProveedorService } from '../../services/albaran-proveedor.service';
import { DevolucionProveedorService } from '../../services/devolucion-proveedor.service';
import { NotificationService } from '../../../../shared/services/notification';

@Component({ selector: 'app-devolucion-form', standalone: true, imports: [CommonModule, ReactiveFormsModule, MatButtonModule, MatCardModule, MatFormFieldModule, MatIconModule, MatInputModule, MatSelectModule], templateUrl: './devolucion-form.html', styleUrl: './devolucion-form.scss' })
export class DevolucionForm implements OnInit {
  private readonly fb = inject(FormBuilder);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly albaranesService = inject(AlbaranProveedorService);
  private readonly devolucionesService = inject(DevolucionProveedorService);
  private readonly notification = inject(NotificationService);

  albaranes: AlbaranProveedor[] = [];
  albaran?: AlbaranProveedor;
  cargando = false;
  guardando = false;
  readonly motivos = ['DEFECTUOSO', 'ERROR_PEDIDO', 'NO_CORRESPONDE', 'SOBRANTE', 'OTRO'];
  readonly form = this.fb.group({ albaran_origen_id: [null as number | null, Validators.required], motivo: ['DEFECTUOSO', Validators.required], observaciones: [''], lineas: this.fb.array([]) });
  get lineas(): FormArray { return this.form.controls.lineas; }

  ngOnInit(): void {
    this.albaranesService.listar().subscribe({ next: albaranes => this.albaranes = albaranes.filter(albaran => albaran.estado === 'CONFIRMADO'), error: error => this.notification.showHttpError(error) });
    const albaranId = Number(this.route.snapshot.queryParamMap.get('albaran_id'));
    if (Number.isInteger(albaranId) && albaranId > 0) this.cargarAlbaran(albaranId);
  }
  cambiarAlbaran(): void { const id = this.form.controls.albaran_origen_id.value; if (id) this.cargarAlbaran(id); else { this.albaran = undefined; this.lineas.clear(); } }
  cargarAlbaran(id: number): void {
    this.cargando = true;
    this.albaranesService.getById(id).subscribe({
      next: albaran => {
        this.cargando = false;
        if (albaran.estado !== 'CONFIRMADO') { this.notification.error('Solo se puede devolver mercancía de un albarán confirmado.'); return; }
        this.albaran = albaran;
        this.form.controls.albaran_origen_id.setValue(albaran.id);
        this.cargarLineasDevolvibles(albaran.id);
      },
      error: error => { this.cargando = false; this.notification.showHttpError(error); },
    });
  }
  private cargarLineasDevolvibles(albaranId: number): void {
    this.albaranesService.getLineasDevolvibles(albaranId).subscribe({
      next: lineas => {
        this.lineas.clear();
        lineas
          .filter(linea => Number(linea.cantidad_disponible) > 0)
          .forEach(linea => this.lineas.push(this.crearLinea(linea)));
      },
      error: error => this.notification.showHttpError(error),
    });
  }

  guardar(): void {
    if (!this.albaran || this.form.invalid || this.guardando) { this.form.markAllAsTouched(); return; }
    const lineas = this.lineas.controls.map(control => control.getRawValue()).filter(linea => Number(linea.cantidad) > 0);
    if (!lineas.length) { this.notification.error('Indica al menos una cantidad a devolver.'); return; }
    const excedida = lineas.find(linea => Number(linea.cantidad) > Number(linea.cantidad_disponible));
    if (excedida) { this.notification.error(`La cantidad a devolver supera las unidades disponibles en ${excedida.descripcion || 'una línea'}.`); return; }
    this.guardando = true;
    this.devolucionesService.crear({ proveedor_id: this.albaran.proveedor_id, albaran_origen_id: this.albaran.id, motivo: this.form.controls.motivo.value!, observaciones: this.form.controls.observaciones.value?.trim() || null, lineas: lineas.map(linea => ({ linea_albaran_id: Number(linea.linea_albaran_id), articulo_stock_id: Number(linea.articulo_stock_id), cantidad: Number(linea.cantidad) })) }).pipe(finalize(() => this.guardando = false)).subscribe({
      next: devolucion => { this.notification.success(`Devolución ${devolucion.numero} creada como borrador.`); void this.router.navigate(['/compras/devoluciones', devolucion.id]); },
      error: error => { this.notification.showHttpError(error); },
    });
  }
  cancelar(): void { void this.router.navigate(['/compras/devoluciones']); }
  private crearLinea(linea: LineaAlbaranDevolvible) {
    return this.fb.group({
      linea_albaran_id: [linea.linea_albaran_id],
      articulo_stock_id: [linea.articulo_stock_id],
      referencia: [{ value: linea.articulo.referencia ?? '', disabled: true }],
      descripcion: [{ value: linea.articulo.nombre ?? linea.articulo.descripcion ?? `Artículo #${linea.articulo_stock_id}`, disabled: true }],
      cantidad_recibida: [{ value: linea.cantidad_recibida, disabled: true }],
      cantidad_devuelta: [{ value: linea.cantidad_devuelta, disabled: true }],
      cantidad_disponible: [{ value: linea.cantidad_disponible, disabled: true }],
      cantidad: [0, [Validators.required, Validators.min(0)]],
    });
  }
}
/** Formulario de devolución que limita cantidades al stock y origen disponibles. */
