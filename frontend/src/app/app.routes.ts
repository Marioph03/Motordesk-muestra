import { Routes } from '@angular/router';

import { bootstrapGuard } from './core/guards/bootstrap.guard';
import { loginGuard } from './core/guards/login.guard';
import { setupGuard } from './core/guards/setup.guard';

export const routes: Routes = [

  {
    path: '',
    canActivate: [bootstrapGuard],
    loadComponent: () =>
      import('./layout/pages/main-layout/main-layout')
        .then(c => c.MainLayout),

    children: [

      {
        path: '',
        redirectTo: 'dashboard',
        pathMatch: 'full'
      },

      {
        path: 'dashboard',
        loadComponent: () =>
          import('./features/dashboard/pages/dashboard/dashboard')
            .then(c => c.Dashboard)
      },

      {
        path: 'clientes',
        loadComponent: () =>
          import('./features/clientes/pages/clientes-list/clientes-list')
            .then(c => c.ClientesList)
      },

      {
        path: 'clientes/nuevo',
        loadComponent: () =>
          import('./features/clientes/components/cliente-form/cliente-form')
            .then(c => c.ClienteForm)
      },

      {
        path: 'clientes/:id',
        loadComponent: () =>
          import('./features/clientes/components/cliente-form/cliente-form')
            .then(c => c.ClienteForm)
      },

      {
        path: 'vehiculos',
        loadComponent: () =>
          import('./features/vehiculos/pages/vehiculos-list/vehiculos-list')
            .then(c => c.VehiculosList)
      },

      {
        path: 'vehiculos/nuevo',
        loadComponent: () =>
          import('./features/vehiculos/components/vehiculo-form/vehiculo-form')
            .then(c => c.VehiculoForm)
      },

      // Conserva enlaces de versiones anteriores que usaban /editar.
      {
        path: 'vehiculos/:id/editar',
        data: { soloLectura: false },
        loadComponent: () =>
          import('./features/vehiculos/components/vehiculo-form/vehiculo-form')
            .then(c => c.VehiculoForm)
      },

      {
        path: 'vehiculos/:id',
        // La ruta genérica representa una consulta. Las modificaciones usan
        // una ruta explícita para que un enlace de "ver" nunca sea editable.
        data: { soloLectura: true },
        loadComponent: () =>
          import('./features/vehiculos/components/vehiculo-form/vehiculo-form')
            .then(c => c.VehiculoForm)
      },

      {
        path: 'ordenes',
        loadComponent: () =>
          import('./features/ordenes/pages/orden-list/orden-list')
            .then(c => c.OrdenList)
      },

      {
        path: 'ordenes/nuevo',
        loadComponent: () =>
          import('./features/ordenes/components/orden-form/orden-form')
            .then(c => c.OrdenForm)
      },

      {
        path: 'ordenes/:id',
        loadComponent: () =>
          import('./features/ordenes/components/orden-form/orden-form')
            .then(c => c.OrdenForm)
      },

      {
        path: 'proveedores',
        loadChildren: () =>
          import('./features/proveedores/routes')
      },

      {
        path: 'facturas',
        loadComponent: () =>
        import('./features/facturas/pages/facturas-list/facturas-list')
        .then(c => c.FacturasList)
      },

      {
        path: 'facturas/nuevo',
        data: { modoCreacion: true },
        loadComponent: () =>
        import('./features/facturas/components/factura-form/factura-form')
        .then(c => c.FacturaForm)
      },

      // Alias para enlaces guardados de versiones anteriores.
      {
        path: 'facturas/nueva',
        data: { modoCreacion: true },
        loadComponent: () =>
        import('./features/facturas/components/factura-form/factura-form')
        .then(c => c.FacturaForm)
      },

      {
        path: 'facturas/:id',
        loadComponent: () =>
        import('./features/facturas/components/factura-form/factura-form')
        .then(c => c.FacturaForm)
      },

      {
        path: 'actividad',
        loadComponent: () =>
        import('./features/actividad/pages/actividad-list/actividad-list')
        .then(c => c.ActividadList)
      },

      {
        path: 'informes',
        loadComponent: () =>
          import('./features/informes/components/informes/informes')
            .then(c => c.Informes)
      },

      {
        path: 'agenda',
        loadComponent: () =>
          import('./features/agenda/components/cita-list/cita-list')
            .then(c => c.CitaList)
      },

      {
        path: 'agenda/nueva',
        loadComponent: () =>
          import('./features/agenda/components/cita-form/cita-form')
            .then(c => c.CitaForm)
      },

      {
        path: 'agenda/:id',
        loadComponent: () =>
          import('./features/agenda/components/cita-form/cita-form')
            .then(c => c.CitaForm)
      },

      {
        path: 'stock',
        loadComponent: () =>
          import('./features/stock/components/articulo-stock-list/articulo-stock-list')
            .then(c => c.ArticuloStockList)
      },

      {
        path: 'stock/nuevo',
        loadComponent: () =>
          import('./features/stock/components/articulo-stock-form/articulo-stock-form')
            .then(c => c.ArticuloStockForm)
      },

      {
        path: 'stock/reposicion',
        loadComponent: () =>
          import('./features/stock/components/reposicion-stock/reposicion-stock')
            .then(c => c.ReposicionStock)
      },

      {
        path: 'ordenes-internas',
        loadComponent: () => import('./features/ordenes/components/ordenes-internas-list/ordenes-internas-list').then(c => c.OrdenesInternasList)
      },
      {
        path: 'ordenes-internas/nueva',
        loadComponent: () => import('./features/ordenes/components/orden-interna-form/orden-interna-form').then(c => c.OrdenInternaForm)
      },
      {
        path: 'ordenes-internas/:id',
        loadComponent: () => import('./features/ordenes/components/orden-interna-form/orden-interna-form').then(c => c.OrdenInternaForm)
      },

      {
        path: 'stock/productos-varios',
        loadComponent: () =>
          import('./features/stock/components/productos-varios-list/productos-varios-list')
            .then(c => c.ProductosVariosList)
      },

      {
        path: 'stock/productos-varios/nuevo',
        data: { controlaStock: false },
        loadComponent: () =>
          import('./features/stock/components/articulo-stock-form/articulo-stock-form')
            .then(c => c.ArticuloStockForm)
      },

      {
        path: 'stock/productos-varios/:id',
        data: { controlaStock: false },
        loadComponent: () =>
          import('./features/stock/components/articulo-stock-form/articulo-stock-form')
            .then(c => c.ArticuloStockForm)
      },

      {
        path: 'stock/albaranes-venta/nuevo',
        loadComponent: () =>
          import('./features/stock/pages/albaran-venta-form/albaran-venta-form')
            .then(c => c.AlbaranVentaForm)
      },

      {
        path: 'stock/albaranes-venta/:id',
        loadComponent: () =>
          import('./features/stock/pages/albaran-venta-detail/albaran-venta-detail')
            .then(c => c.AlbaranVentaDetail)
      },

      {
        path: 'stock/albaranes-venta',
        loadComponent: () =>
          import('./features/stock/pages/albaranes-venta-list/albaranes-venta-list')
            .then(c => c.AlbaranesVentaList)
      },

      {
        path: 'stock/:id',
        loadComponent: () =>
          import('./features/stock/components/articulo-stock-form/articulo-stock-form')
            .then(c => c.ArticuloStockForm)
      },

      {
        path: 'compras/pedidos',
        loadComponent: () =>
          import('./features/compras/components/pedido-compra-list/pedido-compra-list')
            .then(c => c.PedidoCompraList)
      },

      {
        path: 'compras/pedidos/nuevo',
        loadComponent: () =>
          import('./features/compras/components/pedido-compra-form/pedido-compra-form')
            .then(c => c.PedidoCompraForm)
      },

      {
        path: 'compras/albaranes/nuevo',
        loadComponent: () =>
          import('./features/compras/pages/albaran-form/albaran-form')
            .then(c => c.AlbaranForm)
      },

      {
        path: 'compras/albaranes/:id',
        loadComponent: () =>
          import('./features/compras/pages/albaran-detail/albaran-detail')
            .then(c => c.AlbaranDetail)
      },

      {
        path: 'compras/albaranes',
        loadComponent: () =>
          import('./features/compras/pages/albaranes-list/albaranes-list')
            .then(c => c.AlbaranesList)
      },

      {
        path: 'compras/facturas-proveedor/nueva',
        loadComponent: () =>
          import('./features/compras/pages/factura-proveedor-form/factura-proveedor-form')
            .then(c => c.FacturaProveedorForm)
      },

      {
        path: 'compras/facturas-proveedor/:id',
        loadComponent: () =>
          import('./features/compras/pages/factura-proveedor-detail/factura-proveedor-detail')
            .then(c => c.FacturaProveedorDetail)
      },

      {
        path: 'compras/facturas-proveedor',
        loadComponent: () =>
          import('./features/compras/pages/facturas-proveedor-list/facturas-proveedor-list')
            .then(c => c.FacturasProveedorList)
      },

      {
        path: 'compras/devoluciones/nueva',
        loadComponent: () =>
          import('./features/compras/pages/devolucion-form/devolucion-form')
            .then(c => c.DevolucionForm)
      },

      {
        path: 'compras/devoluciones/:id',
        loadComponent: () =>
          import('./features/compras/pages/devolucion-detail/devolucion-detail')
            .then(c => c.DevolucionDetail)
      },

      {
        path: 'compras/devoluciones',
        loadComponent: () =>
          import('./features/compras/pages/devoluciones-list/devoluciones-list')
            .then(c => c.DevolucionesList)
      },

      {
        path: 'compras/pedidos/:id',
        loadComponent: () =>
          import('./features/compras/components/pedido-compra-form/pedido-compra-form')
            .then(c => c.PedidoCompraForm)
      },

      {
        path: 'compras/nuevo',
        loadComponent: () =>
          import('./features/compras/components/pedido-compra-form/pedido-compra-form')
            .then(c => c.PedidoCompraForm)
      },

      {
        path: 'compras/:id',
        loadComponent: () =>
          import('./features/compras/components/pedido-compra-form/pedido-compra-form')
            .then(c => c.PedidoCompraForm)
      },

      {
        path: 'compras',
        loadComponent: () =>
          import('./features/compras/pages/compras-dashboard/compras-dashboard')
            .then(c => c.ComprasDashboard)
      },

      {
        path: 'configuracion/agenda',
        loadComponent: () =>
          import('./features/configuracion/pages/agenda-config/agenda-config')
            .then(c => c.AgendaConfig)
      },

      {
        path: 'configuracion/taller',
        loadComponent: () =>
          import('./features/configuracion/pages/taller-config/taller-config')
            .then(c => c.TallerConfig)
      },

      {
        path: 'configuracion/documentos',
        loadComponent: () =>
          import('./features/configuracion/pages/documentos-config/documentos-config')
            .then(c => c.DocumentosConfig)
      },

      {
        path: 'configuracion/notificaciones',
        loadComponent: () =>
          import('./features/configuracion/pages/notificaciones-config/notificaciones-config')
            .then(c => c.NotificacionesConfig)
      },

      {
        path: 'configuracion/seguridad',
        loadComponent: () =>
          import('./features/configuracion/pages/seguridad-config/seguridad-config')
            .then(c => c.SeguridadConfig)
      },

      {
        path: 'configuracion/sistema',
        loadComponent: () =>
          import('./features/configuracion/pages/sistema-config/sistema-config')
            .then(c => c.SistemaConfig)
      },

      {
        path: 'configuracion/apariencia',
        loadComponent: () =>
          import('./features/configuracion/pages/apariencia-config/apariencia-config')
            .then(c => c.AparienciaConfig)
      },

      {
        path: 'configuracion/facturacion',
        loadComponent: () =>
          import('./features/configuracion/pages/facturacion-config/facturacion-config')
            .then(c => c.FacturacionConfig)
      },

      {
        path: 'configuracion/certificado-electronico',
        loadComponent: () =>
          import('./features/configuracion/pages/certificado-electronico-config/certificado-electronico-config')
            .then(c => c.CertificadoElectronicoConfig)
      },

      {
        path: 'configuracion/datos',
        loadComponent: () =>
          import('./features/configuracion/pages/importar-exportar/importar-exportar')
            .then(c => c.ImportarExportar)
      },

      {
        path: 'configuracion/email',
        loadComponent: () =>
          import('./features/configuracion/pages/email-config/email-config')
            .then(c => c.EmailConfig)
      },

      {
        path: 'configuracion',
        loadComponent: () =>
          import('./features/configuracion/pages/configuracion/configuracion')
            .then(c => c.Configuracion)
      },

      {
        path: 'personal/planificacion',
        loadComponent: () =>
          import('./features/personal/components/personal-planificacion/personal-planificacion')
            .then(c => c.PersonalPlanificacion)
      },

      {
        path: 'personal/registro-jornada',
        loadComponent: () =>
          import('./features/personal/components/registro-jornada/registro-jornada')
            .then(c => c.RegistroJornada)
      },

      {
        path: 'personal/roles',
        loadComponent: () =>
          import('./features/personal/components/rol-list/rol-list')
            .then(c => c.RolList)
      },

      {
        path: 'personal/roles/nuevo',
        loadComponent: () =>
          import('./features/personal/components/rol-form/rol-form')
            .then(c => c.RolForm)
      },

      {
        path: 'personal/roles/:id',
        loadComponent: () =>
          import('./features/personal/components/rol-form/rol-form')
            .then(c => c.RolForm)
      },

      {
        path: 'personal',
        loadComponent: () =>
          import('./features/personal/components/personal-list/personal-list')
            .then(c => c.PersonalList)
      },

      {
        path: 'personal/nuevo',
        loadComponent: () =>
          import('./features/personal/components/personal-form/personal-form')
            .then(c => c.PersonalForm)
      },

      {
        path: 'personal/:id',
        loadComponent: () =>
          import('./features/personal/components/personal-form/personal-form')
            .then(c => c.PersonalForm)
      }

    ]
  },

  {
    path: 'setup',
    canActivate: [setupGuard],
    loadComponent: () =>
      import('./features/setup/pages/setup/setup')
        .then(c => c.Setup)
  },

  {
    path: 'login',
    canActivate: [loginGuard],
    loadComponent: () =>
      import('./features/login/pages/login/login')
        .then(c => c.Login)
  },

  {
    path: '**',
    redirectTo: ''
  }

];
/** Mapa de rutas lazy-loaded; la protección real permanece en el backend. */
