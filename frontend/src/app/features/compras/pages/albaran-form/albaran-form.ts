import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormArray, FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSelectModule } from '@angular/material/select';
import { finalize } from 'rxjs';

import { AlbaranProveedorService } from '../../services/albaran-proveedor.service';
import { PedidosCompraService } from '../../services/pedidos-compra.service';
import { StockService } from '../../../stock/services/stock.service';
import { ProveedoresService } from '../../../proveedores/services/proveedores.service';
import { ArticuloStock } from '../../../stock/models/articulo-stock';
import { PedidoCompra } from '../../models/pedido-compra';
import { Proveedor } from '../../../proveedores/models/proveedor';
import { NotificationService } from '../../../../shared/services/notification';

@Component({
  selector: 'app-albaran-form',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, MatButtonModule, MatCardModule, MatFormFieldModule, MatIconModule, MatInputModule, MatProgressSpinnerModule, MatSelectModule],
  templateUrl: './albaran-form.html',
  styleUrl: './albaran-form.scss',
})
export class AlbaranForm implements OnInit {
  private readonly fb = inject(FormBuilder);
  private readonly service = inject(AlbaranProveedorService);
  private readonly pedidosService = inject(PedidosCompraService);
  private readonly proveedoresService = inject(ProveedoresService);
  private readonly stockService = inject(StockService);
  private readonly notification = inject(NotificationService);
  private readonly router = inject(Router);
  private readonly route = inject(ActivatedRoute);

  proveedores: Proveedor[] = [];
  pedidos: PedidoCompra[] = [];
  articulos: ArticuloStock[] = [];
  cargando = false;
  guardando = false;
  esDetalle = false;

  readonly form = this.fb.group({
    proveedor_id: [null as number | null, Validators.required],
    pedido_compra_id: [null as number | null],
    numero_proveedor: [''],
    fecha: [this.fechaHoy(), Validators.required],
    observaciones: [''],
    lineas: this.fb.array([]),
  });

  get lineas(): FormArray { return this.form.controls.lineas; }

  ngOnInit(): void {
    const albaranId = Number(this.route.snapshot.paramMap.get('id'));
    this.esDetalle = Number.isInteger(albaranId) && albaranId > 0;
    this.cargarProveedores();
    this.cargarPedidos();
    this.cargarArticulos();
    if (this.esDetalle) {
      this.cargarDetalle(albaranId);
      return;
    }
    const pedidoId = Number(this.route.snapshot.queryParamMap.get('pedido_id') ?? this.route.snapshot.queryParamMap.get('pedido'));
    if (Number.isInteger(pedidoId) && pedidoId > 0) this.cargarPedido(pedidoId);
  }

  cargarProveedores(): void {
    this.proveedoresService.getProveedores().subscribe({
      next: proveedores => this.proveedores = proveedores.filter(proveedor => proveedor.activo),
      error: error => this.notification.showHttpError(error),
    });
  }

  cargarPedidos(): void {
    this.pedidosService.getPedidos().subscribe({
      next: pedidos => this.pedidos = pedidos.filter(pedido => pedido.estado === 'ENVIADO' || pedido.estado === 'RECIBIDO_PARCIAL'),
      error: error => this.notification.showHttpError(error),
    });
  }

  cargarArticulos(): void {
    this.stockService.getArticulos().subscribe({
      next: articulos => this.articulos = articulos.filter(articulo => articulo.activo),
      error: error => this.notification.showHttpError(error),
    });
  }

  cambiarPedido(): void {
    const pedidoId = this.form.controls.pedido_compra_id.value;
    if (!pedidoId) {
      this.lineas.clear();
      return;
    }
    this.cargarPedido(pedidoId);
  }

  cargarPedido(pedidoId: number): void {
    this.cargando = true;
    this.pedidosService.getPedido(pedidoId).subscribe({
      next: pedido => {
        this.cargando = false;
        this.form.patchValue({ proveedor_id: pedido.proveedor_id, pedido_compra_id: pedido.id });
        this.lineas.clear();
        for (const linea of pedido.lineas ?? []) {
          const pedida = Number(linea.cantidad_pedida ?? 0);
          const recibida = Number(linea.cantidad_recibida ?? 0);
          const pendiente = Math.max(0, pedida - recibida);
          if (pendiente > 0) this.lineas.push(this.crearLineaDesdePedido(linea, pedida, recibida, pendiente));
        }
        if (!this.lineas.length) this.notification.success('Este pedido ya está completamente recibido.');
      },
      error: error => { this.cargando = false; this.notification.showHttpError(error); },
    });
  }

  agregarLinea(): void { this.lineas.push(this.crearLineaManual()); }
  eliminarLinea(indice: number): void { this.lineas.removeAt(indice); }

  seleccionarArticulo(indice: number): void {
    const control = this.lineas.at(indice);
    const articulo = this.articulos.find(item => item.id === control.value.articulo_stock_id);
    if (articulo) control.patchValue({ referencia: articulo.referencia, descripcion: articulo.nombre, coste_unitario: articulo.coste });
  }

  guardar(): void {
    if (this.esDetalle || this.guardando) return;
    if (this.form.invalid) { this.form.markAllAsTouched(); return; }
    const lineas = this.lineas.controls.map(control => control.getRawValue()).filter(linea => Number(linea.cantidad_recibida) > 0);
    if (!lineas.length) { this.notification.error('Indica al menos una cantidad recibida.'); return; }
    const superaPendiente = lineas.find(linea => linea.cantidad_pendiente !== null && Number(linea.cantidad_recibida) > Number(linea.cantidad_pendiente));
    if (superaPendiente) { this.notification.error(`La cantidad recibida de ${superaPendiente.descripcion || 'un artículo'} supera la pendiente.`); return; }
    const valor = this.form.getRawValue();
    this.guardando = true;
    this.service.crear({
      proveedor_id: valor.proveedor_id!,
      pedido_compra_id: valor.pedido_compra_id || null,
      numero_proveedor: valor.numero_proveedor?.trim() || null,
      fecha: valor.fecha!,
      observaciones: valor.observaciones?.trim() || null,
      lineas: lineas.map(linea => ({ articulo_stock_id: Number(linea.articulo_stock_id), cantidad_recibida: Number(linea.cantidad_recibida), coste_unitario: linea.coste_unitario === null ? null : Number(linea.coste_unitario) })),
    }).pipe(finalize(() => this.guardando = false)).subscribe({
      next: albaran => {
        this.notification.success(`Albarán ${albaran.numero_interno} creado como borrador.`);
        void this.router.navigate(['/compras/albaranes', albaran.id]);
      },
      error: error => { this.notification.showHttpError(error); },
    });
  }

  cancelar(): void { void this.router.navigate(['/compras/albaranes']); }

  private crearLineaManual() {
    return this.fb.group({
      articulo_stock_id: [null as number | null, Validators.required],
      referencia: [{ value: '', disabled: true }], descripcion: [{ value: '', disabled: true }],
      cantidad_pedida: [{ value: null as number | null, disabled: true }], cantidad_recibida_previa: [{ value: null as number | null, disabled: true }], cantidad_pendiente: [{ value: null as number | null, disabled: true }],
      cantidad_recibida: [1, [Validators.required, Validators.min(0.01)]], coste_unitario: [null as number | null, Validators.min(0)],
    });
  }

  private crearLineaDesdePedido(linea: PedidoCompra['lineas'][number], pedida: number, recibida: number, pendiente: number) {
    return this.fb.group({
      articulo_stock_id: [linea.articulo_stock_id, Validators.required], referencia: [{ value: linea.referencia ?? '', disabled: true }], descripcion: [{ value: linea.descripcion ?? '', disabled: true }],
      cantidad_pedida: [{ value: pedida, disabled: true }], cantidad_recibida_previa: [{ value: recibida, disabled: true }], cantidad_pendiente: [{ value: pendiente, disabled: true }],
      cantidad_recibida: [pendiente, [Validators.required, Validators.min(0)]], coste_unitario: [Number(linea.coste_unitario ?? 0), Validators.min(0)],
    });
  }

  private fechaHoy(): string {
    const fecha = new Date();
    return new Date(fecha.getTime() - fecha.getTimezoneOffset() * 60_000).toISOString().slice(0, 10);
  }

  private cargarDetalle(id: number): void {
    this.cargando = true;
    this.service.getById(id).subscribe({
      next: albaran => {
        this.cargando = false;
        this.form.patchValue({ proveedor_id: albaran.proveedor_id, pedido_compra_id: albaran.pedido_compra_id ?? null, numero_proveedor: albaran.numero_proveedor ?? '', fecha: albaran.fecha.slice(0, 10), observaciones: albaran.observaciones ?? '' });
        this.lineas.clear();
        for (const linea of albaran.lineas) this.lineas.push(this.fb.group({ articulo_stock_id: [linea.articulo_stock_id], referencia: [{ value: '', disabled: true }], descripcion: [{ value: '', disabled: true }], cantidad_pedida: [{ value: null, disabled: true }], cantidad_recibida_previa: [{ value: null, disabled: true }], cantidad_pendiente: [{ value: null, disabled: true }], cantidad_recibida: [linea.cantidad_recibida], coste_unitario: [linea.coste_unitario ?? null] }));
        this.form.disable();
      },
      error: error => { this.cargando = false; this.notification.showHttpError(error); },
    });
  }
}
/** Formulario de alta de albarán proveedor antes de afectar al almacén. */
