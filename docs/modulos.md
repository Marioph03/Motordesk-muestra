# Módulos y flujos de negocio

Esta referencia complementa la guía de desarrollo. Indica qué módulo es dueño
de cada regla importante y qué datos se actualizan en cada flujo.

## Clientes y vehículos

- Un cliente puede tener varios vehículos.
- La matrícula identifica operativamente al vehículo y se normaliza antes de
  comprobar duplicados.
- Los servicios validan los datos de propiedad; las pantallas solo presentan el
  formulario y las sugerencias de búsqueda.

Puntos de entrada: `api/v1/clientes.py`, `api/v1/vehiculos.py`, sus servicios,
repositorios y componentes dentro de `frontend/src/app/features`.

## Órdenes, presupuestos y garantías

```text
Cliente -> Vehículo -> Orden de reparación -> Factura
                                  |
                                  +-> Presupuesto / garantía cuando procede
```

- Una orden puede contener mano de obra, piezas, observaciones y personal
  asignado.
- El importe de una orden no equivale a facturación real: solo las facturas
  válidas entran en los indicadores económicos.
- Las garantías se representan como órdenes de tipo `GA`; sus estados y fecha
  de resolución permiten el seguimiento y los informes.

Al modificar estados o importes, revisa los servicios de órdenes, facturas y
garantías antes de cambiar la interfaz: existen validaciones cruzadas y reglas
de stock.

## Facturación, cobros y VERI*FACTU

- Una factura puede estar en borrador, emitida, anulada u otros estados del
  flujo fiscal configurado.
- Los pagos registrados son la fuente de verdad del importe pendiente; no se
  debe deducir solo a partir de `estado_cobro`.
- Los registros VERI*FACTU, su encadenamiento y QR pertenecen al backend.
  Cualquier cambio fiscal requiere pruebas específicas y no debe hacerse como
  una mejora visual aislada.
- El modo de pruebas se mantiene separado de los datos económicos reales.

Los PDFs leen la configuración de Taller y Documentos. Nunca vuelvas a dejar
datos comerciales, teléfono o logo fijados en un generador concreto.

## Agenda y personal

- Las citas validan horario del taller, cierres excepcionales, solapes y
  disponibilidad del personal.
- Una ausencia se guarda como rango de fechas y bloquea la asignación cuando se
  solapa.
- Citas y órdenes admiten personal asignado mediante relaciones N:M.

Al editar fechas hay que volver a validar tanto nuevos trabajadores como los ya
asignados. Esta regla vive en el servicio, no en Angular.

## Stock y compras

```text
Artículo bajo mínimo -> Reposición -> Pedido de compra
Pedido recibido -> Entrada de stock
Albarán confirmado -> Factura de proveedor / posible devolución
Orden de reparación -> Consumo o devolución de stock
```

- `MovimientoStock` es el historial de existencias; úsalo para informes de
  consumo y nunca modifiques stock directamente sin crear el movimiento
  correspondiente.
- `ENTRADA_COMPRA` diferencia las recepciones de compra de las entradas
  manuales.
- Las líneas de pedido almacenan coste histórico. Los análisis de compras no
  deben depender únicamente del coste actual del artículo.
- Un albarán confirmado o una devolución afecta a stock una sola vez; los
  servicios protegen la idempotencia de esos flujos.

## Configuración

La configuración está dividida por responsabilidad:

- Taller: identidad, dirección y logo.
- Agenda: horario, duración por defecto y cierres.
- Documentos: campos visibles, textos predeterminados y pie.
- Notificaciones: qué alertas muestra el dashboard.
- Facturación: comportamiento fiscal y modo de pruebas.
- Seguridad y sistema: credenciales, sesión, copias y salud del sistema.

Los cambios de configuración deben aplicarse a los servicios que producen el
resultado final (PDF, validación de cita o dashboard), no limitarse a guardar
un valor desde una pantalla.

## Informes y dashboard

Los informes consultan rangos y agregados reales del backend. El dashboard es
una visión operativa rápida, mientras que Informes permite detalle por periodo.
No calcules totales financieros en Angular: recibe los valores ya calculados y
formateados desde la API.

## MotorDesk AI y auditoría

Las consultas IA utilizan herramientas de lectura explícitas y filtradas por
permiso. Las modificaciones pasan por una propuesta y confirmación visible:

```text
Prompt -> tool de propuesta -> tarjeta de confirmación -> endpoint confirmado
```

Los workflows reúnen pasos dependientes en una única transacción. La auditoría
`ai_auditoria` registra intentos, resultados y autorizaciones, pero no guarda
contraseñas, tokens ni claves API.
