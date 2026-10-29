# Pruebas funcionales — Personal, permisos y disponibilidad

Fecha: 21/08/2026

Resultado general: **OK**.

## Registros de prueba conservados

| Elemento | Identificador | Dónde verlo |
| --- | --- | --- |
| Rol sin permisos | `QA_SIN_PERMISOS_20260821` | Personal → Roles y permisos |
| Usuario disponible | ID `3` — `QA Disponible Personal 2026` | Personal → Equipo |
| Usuario ausente | ID `4` — `QA Ausente Personal 2026` | Personal → Equipo |
| Vacaciones QA | Ausencia ID `1` | Ficha del usuario QA Ausente |
| Cita QA | Cita ID `6` — `QA Personal 2026 · Cita asignada` | Agenda y ficha de QA Disponible |
| Orden QA | Orden ID `18` — `QA Personal 2026 · Orden asignada` | Órdenes y ficha de QA Disponible |

## Casos validados

- El usuario con rol QA sin permisos recibe `403` al consultar `/personal/disponibilidad`.
- Un ADMIN recibe `200` en esa misma consulta.
- `GET /usuarios/` responde `200` y serializa correctamente los usuarios QA.
- El rol `ADMIN` no puede desactivarse.
- No se puede crear una cita con `QA Ausente Personal 2026` durante sus vacaciones.
- No se puede reasignar la cita QA a esa persona ausente.
- No se puede reasignar la orden QA a esa persona ausente.
- La planificación semanal devuelve tanto el bloque de vacaciones como el bloque de cita QA.
- El resumen operativo del usuario disponible contiene su cita y su orden QA.

## Nota de revisión visual

En **Personal → Planificación** se muestran actualmente ausencias y citas porque son los únicos elementos con intervalos temporales reales. Las órdenes QA aparecen en la ficha de la persona, pero no como bloque semanal hasta que las órdenes incorporen `fecha_prevista_salida`.

El script reproducible usado en la prueba se conserva en `backend/.tmp_personal_module_check.py`.
