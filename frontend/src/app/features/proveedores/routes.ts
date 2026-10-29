import { Routes } from '@angular/router';
import { ProveedorList } from './components/proveedor-list/proveedor-list';

export default [
  {
    path: '',
    component: ProveedorList
  }
] satisfies Routes;
/** Rutas lazy-loaded del módulo de proveedores. */
