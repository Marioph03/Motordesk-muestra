# MotorDesk

> Para incorporarse al proyecto, consulta primero la
> [guía de desarrollo](docs/guia_desarrollo.md), junto con la documentación de
> [arquitectura](docs/arquitectura.md), [API](docs/api.md) y
> [base de datos](docs/base_datos.md).

**MotorDesk** es una aplicación de gestión empresarial orientada a
talleres de automoción y concesionarios. Centraliza clientes, vehículos,
órdenes de reparación, presupuestos, garantías, facturación, agenda,
almacén, proveedores y usuarios, e incorpora un asistente de
inteligencia artificial integrado.

> **Estado:** MotorDesk v1.0 --- fase final de pruebas y preparación
> para despliegue.

## Funcionalidades

-   **Clientes:** alta, consulta, edición y gestión de datos.
-   **Vehículos:** gestión de vehículos asociados a clientes e historial
    relacionado.
-   **Órdenes de reparación:** estados, mano de obra, piezas, importes y
    vinculación con facturación.
-   **Presupuestos:** creación, seguimiento y generación de PDF.
-   **Garantías:** flujo desde apertura/revisión hasta aprobación,
    reparación y resolución.
-   **Facturación:** facturas desde órdenes, líneas manuales, PDF,
    estado de cobro, email y WhatsApp.
-   **VERIFACTU / AEAT:** integración del sistema de facturación
    verificable, comunicación con AEAT y QR cuando corresponde.
-   **Agenda y citas:** gestión de citas asociadas a clientes y
    vehículos.
-   **Stock / almacén:** artículos, existencias, movimientos y pedidos.
-   **Proveedores:** gestión de proveedores y relación con
    pedidos/almacén.
-   **Usuarios, roles y permisos:** autenticación JWT y autorización por
    permisos.
-   **Dashboard:** métricas, actividad reciente y acciones rápidas.
-   **Excel:** importación y exportación de datos para facilitar
    migraciones desde hojas de cálculo.
-   **MotorDesk AI:** asistente integrado conectado a datos reales
    mediante herramientas controladas.

## Tecnologías

### Frontend

-   Angular
-   TypeScript
-   Angular Standalone Components
-   Angular Material
-   HTML / CSS / SCSS

### Backend

-   Python
-   FastAPI
-   SQLAlchemy
-   Pydantic
-   Alembic
-   JWT

### Datos e integraciones

-   PostgreSQL
-   Groq + GPT-OSS para MotorDesk AI
-   AEAT / VERIFACTU
-   WhatsApp
-   Email
-   Excel
-   Generación de PDF

## Arquitectura

``` text
MotorDesk/
├── frontend/                 # Aplicación Angular
│   ├── src/
│   ├── public/ / assets/
│   ├── package.json
│   └── angular.json
├── backend/                  # API FastAPI
│   ├── app/
│   │   ├── models/
│   │   ├── routers/
│   │   ├── schemas/
│   │   ├── services/
│   │   └── ai/
│   ├── alembic/
│   ├── alembic.ini
│   └── requirements.txt
└── README.md
```

> La estructura exacta puede variar ligeramente según la versión actual
> del repositorio.

## Generar el instalador de Windows

Para distribuir una versión nueva no se deben reutilizar manualmente
carpetas `dist` anteriores. El comando oficial reconstruye desde el código
actual el backend, el frontend, el lanzador y el instalador, y genera una
versión nueva de Inno Setup:

```powershell
.\installer\scripts\build-installer.ps1
```

El resultado se deja en `installer\output`. El script solo borra artefactos
generados de compilaciones anteriores; no toca la base de datos, copias de
seguridad ni archivos `.env`. En instalaciones existentes, el backend nativo
incluye las migraciones Alembic y las aplica antes de aceptar peticiones.

## Requisitos previos

Para desarrollo local:

-   Python 3.x compatible con las dependencias del backend.
-   Node.js y npm.
-   Angular CLI.
-   PostgreSQL.
-   Git, si se utiliza control de versiones.

Comprueba el entorno:

``` powershell
python --version
node --version
npm --version
ng version
psql --version
```

## Instalación

### 1. Backend

Desde la raíz:

``` powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. PostgreSQL

Crea una base de datos para MotorDesk. Ejemplo:

``` sql
CREATE DATABASE motordesk;
```

En producción se recomienda utilizar un usuario específico para la
aplicación con únicamente los privilegios necesarios.

### 3. Variables de entorno

Crea el archivo de entorno utilizado por el backend, por ejemplo
`backend/.env`.

Ejemplo **sin credenciales reales**:

``` dotenv
# PostgreSQL
DATABASE_URL=postgresql://USUARIO:CONTRASENA@localhost:5432/motordesk

# JWT
SECRET_KEY=CAMBIAR_POR_UN_SECRETO_LARGO_Y_ALEATORIO
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# MotorDesk AI
GROQ_API_KEY=TU_API_KEY_DE_GROQ
GROQ_MODEL=openai/gpt-oss-120b

# Email
SMTP_HOST=TU_SERVIDOR
SMTP_PORT=587
SMTP_USER=TU_USUARIO
SMTP_PASSWORD=TU_CONTRASENA
SMTP_FROM=TU_EMAIL

# WhatsApp / Meta
WHATSAPP_ACCESS_TOKEN=TU_TOKEN
WHATSAPP_PHONE_NUMBER_ID=TU_PHONE_NUMBER_ID

# VERIFACTU / AEAT
AEAT_ENVIRONMENT=TEST
AEAT_CERT_PATH=RUTA_AL_CERTIFICADO
AEAT_CERT_PASSWORD=CONTRASENA_DEL_CERTIFICADO
```

Los nombres exactos deben coincidir con las variables utilizadas
actualmente por el código.

**Nunca subas `.env`, certificados, tokens o claves privadas al
repositorio.**

Ejemplo de `.gitignore`:

``` gitignore
.env
.venv/
__pycache__/
*.pyc
```

Es recomendable mantener un `.env.example` únicamente con valores
ficticios.

### 4. Migraciones

Con el entorno virtual activo:

``` powershell
alembic upgrade head
```

Para consultar la revisión aplicada:

``` powershell
alembic current
```

Si se modifica el modelo:

``` powershell
alembic revision --autogenerate -m "descripcion del cambio"
```

Revisa siempre las migraciones autogeneradas antes de aplicarlas.

### 5. Ejecutar FastAPI

Ejemplo habitual:

``` powershell
uvicorn app.main:app --reload
```

Si la instancia FastAPI está en otro módulo, utiliza la ruta real del
proyecto.

Normalmente:

``` text
http://localhost:8000
```

### 6. Frontend

En otra terminal:

``` powershell
cd frontend
npm install
ng serve
```

Normalmente:

``` text
http://localhost:4200
```

## Puesta en marcha rápida

### Terminal backend

``` powershell
cd backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload
```

### Terminal frontend

``` powershell
cd frontend
ng serve
```

## MotorDesk AI

<img width="275" height="402" alt="image" src="https://github.com/user-attachments/assets/2cacd96d-8638-496c-8854-246318d05941" />


MotorDesk AI utiliza un modelo remoto mediante **Groq**, por lo que no
es necesario desplegar un modelo de IA local en cada taller.

La API key se almacena exclusivamente en el backend:

``` dotenv
GROQ_API_KEY=TU_API_KEY
```

Nunca debe exponerse en Angular.

Arquitectura simplificada:

``` text
Usuario
   ↓
Angular
   ↓
FastAPI
   ├── Autenticación y permisos
   ├── Groq / GPT-OSS
   └── Tools de MotorDesk
            ↓
        PostgreSQL
```

### Seguridad de la IA

El modelo no dispone de acceso SQL libre. Las consultas y operaciones
pasan por herramientas definidas por MotorDesk.

Para escrituras:

``` text
Petición
   ↓
IA propone Action
   ↓
Usuario revisa
   ├── Cancelar
   └── Confirmar
          ↓
       Backend
          ↓
      PostgreSQL
```

Las operaciones compuestas pueden utilizar **Workflows** como:

``` text
Cliente → Vehículo → Cita
Cliente → Vehículo → Orden
```

Cuando corresponde, el workflow utiliza una única transacción: si falla
un paso se realiza `ROLLBACK` para evitar dejar datos incompletos.

MotorDesk AI también mantiene contexto conversacional y respeta los
permisos del usuario autenticado.

## Importación y exportación Excel

<img width="1052" height="487" alt="image" src="https://github.com/user-attachments/assets/ddc6f182-f9c7-4544-8238-68c9207e63ca" />


La importación permite migrar información almacenada previamente en
hojas de cálculo, especialmente clientes, vehículos, proveedores y otros
datos compatibles.

Antes de una importación real:

1.  Realiza una copia de seguridad.
2.  Comprueba las columnas del Excel.
3.  Prueba primero con pocos registros.
4.  Revisa duplicados y errores.
5.  Comprueba los datos importados desde el frontend.
6.  Importa la base completa solo después de validar el resultado.

## VERIFACTU

<img width="1037" height="392" alt="image" src="https://github.com/user-attachments/assets/4d163f43-a127-4e5f-a988-f46e7434a391" />


MotorDesk incorpora soporte para VERIFACTU dentro de su módulo de
facturación.

Antes de utilizarlo en producción:

1.  Verifica la normativa vigente.
2.  Configura el entorno correspondiente.
3.  Configura certificados y credenciales de forma segura.
4.  Realiza pruebas controladas.
5.  Comprueba las respuestas de la AEAT.
6.  Verifica el contenido de las facturas y del QR.
7.  Protege certificados, contraseñas y claves privadas.

MotorDesk dispone además de facturación convencional según la
configuración de la instalación.

> Este README describe el proyecto técnicamente y no sustituye la
> documentación oficial de la AEAT ni el asesoramiento fiscal o jurídico
> aplicable.

## Seguridad

-   No almacenar contraseñas en texto plano.
-   Proteger endpoints en el backend, no solo en Angular.
-   Aplicar permisos por usuario/rol.
-   Mantener secretos fuera de Git.
-   Mantener la clave de Groq exclusivamente en backend.
-   No proporcionar acceso SQL directo al modelo de IA.
-   Validar datos importados desde Excel.
-   Requerir confirmación para escrituras propuestas por IA.
-   Utilizar HTTPS en producción.
-   Restringir el acceso a PostgreSQL.
-   Proteger certificados y credenciales de integraciones.
-   Mantener copias de seguridad periódicas.

## Backups

Ejemplo orientativo:

``` powershell
pg_dump -U USUARIO -d motordesk -F c -f motordesk_backup.dump
```

Restauración:

``` powershell
pg_restore -U USUARIO -d motordesk motordesk_backup.dump
```

En producción se recomienda automatizar las copias y comprobar
periódicamente que pueden restaurarse.

## Checklist antes de producción

-   [ ] Backend arranca sin errores.
-   [ ] Frontend compila correctamente.
-   [ ] PostgreSQL está configurado.
-   [ ] Migraciones Alembic aplicadas.
-   [ ] `.env` excluido de Git.
-   [ ] JWT utiliza un secreto seguro.
-   [ ] Roles y permisos probados.
-   [ ] Clientes y vehículos probados.
-   [ ] Órdenes de reparación probadas.
-   [ ] Mano de obra y piezas probadas.
-   [ ] Presupuestos probados.
-   [ ] Garantías probadas.
-   [ ] Facturación convencional probada.
-   [ ] PDF probado.
-   [ ] Email y WhatsApp probados.
-   [ ] Agenda y citas probadas.
-   [ ] Stock, movimientos y pedidos probados.
-   [ ] Importación/exportación Excel probada.
-   [ ] MotorDesk AI probado.
-   [ ] Actions de IA: confirmar/cancelar probado.
-   [ ] Workflows de IA probados.
-   [ ] Permisos de IA probados con usuarios restringidos.
-   [ ] VERIFACTU probado en el entorno correspondiente.
-   [ ] Backups configurados.
-   [ ] Restauración de backup comprobada.
-   [ ] HTTPS configurado en producción.
-   [ ] Datos de prueba eliminados antes del uso real.

## Despliegue

Arquitectura de producción orientativa:

``` text
Usuarios
   ↓
Frontend Angular
   ↓ HTTPS
Backend FastAPI
   ├── PostgreSQL
   ├── Groq
   ├── AEAT
   └── WhatsApp / Email
```

En producción no se recomienda utilizar `ng serve` ni
`uvicorn --reload`. El frontend debe compilarse para producción y el
backend debe ejecutarse mediante una configuración de servidor apropiada
al entorno.

## Estado de MotorDesk v1.0

``` text
Clientes                       ✅
Vehículos                      ✅
Órdenes de reparación          ✅
Presupuestos                   ✅
Garantías                      ✅
Facturación                    ✅
├── Facturación convencional
├── PDF
├── Email / WhatsApp
└── VERIFACTU
Agenda y citas                 ✅
Stock / almacén                ✅
Proveedores / pedidos          ✅
Usuarios / roles / permisos    ✅
Dashboard                      ✅
Importar / exportar Excel      ✅
MotorDesk AI                   ✅
```

La fase final debe centrarse principalmente en pruebas integrales,
corrección de errores, seguridad, backups, migración de datos reales y
despliegue.

## Licencia

Actualmente se considera **software propietario**, salvo que
posteriormente se añada un archivo `LICENSE` indicando otras
condiciones.

Todos los derechos reservados.

------------------------------------------------------------------------

**MotorDesk --- Gestión de taller, facturación y asistencia inteligente
desde una única aplicación.**
