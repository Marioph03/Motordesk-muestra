// Punto de entrada estable para el módulo de Informes.
// La implementación visual y la lógica se mantienen en InformesDashboard
// para evitar duplicar el formulario, las pestañas y las consultas al backend.
export {
  InformesDashboard as Informes
} from '../informes-dashboard/informes-dashboard';
/** Pantalla de informes por rango con datos agregados sin cálculos locales críticos. */
