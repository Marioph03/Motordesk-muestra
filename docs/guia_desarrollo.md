# Guía de desarrollo de MotorDesk

Esta guía sirve como punto de entrada para quien mantenga MotorDesk. Resume
la organización del código y las reglas que conviene respetar al añadir una
funcionalidad.

## Arquitectura

MotorDesk se divide en dos aplicaciones:

- `frontend/`: Angular con componentes *standalone*, Angular Material y SCSS.
- `backend/`: FastAPI, SQLAlchemy, Pydantic y Alembic sobre PostgreSQL.

El frontend nunca aplica reglas de negocio definitivas. Puede ocultar acciones
por permisos para mejorar la experiencia, pero el backend vuelve a comprobar
autenticación, permisos y validaciones antes de leer o modificar datos.

## Backend

La aplicación se inicia en `backend/app/main.py`. Ahí se configuran CORS,
archivos estáticos, routers, tareas de mantenimiento y la auditoría HTTP.

La estructura de una funcionalidad normal es:

```text
api/v1/<modulo>.py       Endpoint HTTP y conversión de errores a respuestas.
schemas/<modulo>.py      Contratos Pydantic de entrada y salida.
services/<modulo>_service.py
                         Reglas de negocio, validaciones y transacciones.
repositories/<modulo>_repository.py
                         Consultas SQLAlchemy reutilizables.
models/<modulo>.py       Modelo persistente SQLAlchemy.
```

Reglas importantes:

1. Los routers deben ser pequeños: reciben datos, invocan servicios y devuelven
   errores HTTP apropiados.
2. Las reglas de negocio y las validaciones viven en `services/`.
3. Una operación compuesta debe usar una sola transacción. No introduzcas
   `commit()` intermedios si cliente, vehículo y orden deben ser atómicos.
4. Toda modificación de modelos requiere registrar el modelo en
   `app/models/__init__.py` para que Alembic lo detecte, generar una migración,
   revisarla y finalmente ejecutar `alembic upgrade head`.
5. No guardes secretos en modelos, logs ni auditorías. El módulo de auditoría
   de IA dispone de `sanitizar_auditoria()` para datos estructurados.

## Autenticación y permisos

Los JWT se validan en el backend mediante `get_current_user`. Para proteger un
endpoint se utiliza `require_permission("modulo.accion")`. El rol `ADMIN`
mantiene acceso de salvaguarda, pero los demás usuarios se validan contra los
permisos realmente asignados a su rol.

El token de acceso dura seis horas según la configuración del backend. En el
frontend, `AuthService` programa su caducidad y el interceptor reacciona ante
un `401`: ambos limpian la sesión y redirigen a `/login`.

## Frontend

Las rutas están centralizadas en `frontend/src/app/app.routes.ts`. La ruta raíz
carga `MainLayout`, que contiene sidebar, topbar, `router-outlet` y el
asistente MotorDesk AI. Las rutas públicas, como `/login`, permanecen fuera del
layout protegido.

Organización habitual de cada módulo:

```text
features/<modulo>/
  models/       Interfaces TypeScript del contrato API.
  services/     Cliente HTTP del módulo.
  pages/        Pantallas asociadas a rutas.
  components/   Componentes reutilizables del módulo.
```

El tema claro/oscuro depende de variables CSS globales. Antes de añadir un
color fijo, revisa `frontend/src/styles/_variables.scss` y los estilos globales
para que la pantalla funcione en ambos temas y en móvil.

## MotorDesk AI

La IA está diseñada para consultar datos con herramientas explícitas y para
proponer cambios sin ejecutarlos directamente.

```text
Usuario autenticado
  -> MotorAIService
  -> filtrado de tools por permisos e intención
  -> Groq
  -> tool_registry
  -> servicios/repositorios de MotorDesk
```

- No existe ni debe añadirse una herramienta SQL genérica.
- Las acciones y workflows requieren confirmación explícita desde la interfaz.
- Los workflows compuestos se ejecutan de forma atómica.
- La memoria conversacional es temporal y está en RAM; no es una auditoría.
- `ai_auditoria` guarda trazabilidad de herramientas, permisos, acciones y
  workflows, sin almacenar secretos.
- Las definiciones de herramientas se seleccionan por intención para no superar
  el límite de tokens del proveedor.

## Pruebas mínimas antes de entregar un cambio

```powershell
# Backend
cd backend
..\.venv\Scripts\python.exe -m compileall app
..\.venv\Scripts\alembic.exe current

# Frontend
cd ..\frontend
npm.cmd run build
```

Además, prueba el flujo funcional afectado desde la interfaz: éxito, validación
de datos, falta de permisos, modo claro y oscuro cuando la pantalla tenga UI.

## Convención de comentarios

Los comentarios explican el **porqué**, no repiten el **qué** de una línea
evidente. Son especialmente necesarios en:

- límites de seguridad y permisos;
- transacciones y `commit`/`rollback`;
- compatibilidad con datos heredados;
- reglas fiscales, VERI*FACTU y generación de documentos;
- decisiones de rendimiento, como paginación o selección de tools de IA.

Mantén los comentarios en español y actualízalos al cambiar la regla que
describen.
