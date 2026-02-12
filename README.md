# FleetPredict Pro – Entorno de desarrollo

Sistema de mantenimiento predictivo para flotas de transporte. Incluye registro de vehículos, dashboard en tiempo (casi) real, alertas por patrones de telemetría, centro de notificaciones, predicción de fallas, reportes PDF y gestión de mantenimiento.

---

## Credenciales de acceso

### Usuario administrador (superuser)

No hay usuario por defecto. Debes crearlo tras las migraciones:

```bash
python manage.py createsuperuser
```

Indica **email** (ej. `admin@fleetpredict.local`), nombre y **contraseña**. Este usuario tiene rol *Administrator* y acceso a todo (admin Django en `/admin/`, usuarios, reportes, etc.).

### Conductores de prueba (creados por seed)

Tras ejecutar `python manage.py seed_simulated_fleet` se crean 10 conductores asignados a los vehículos simulados SIM-001 … SIM-010:

| Email                     | Contraseña     | Vehículo asignado |
|---------------------------|----------------|--------------------|
| driver1@fleetpredict.local  | `DriverPass123!` | SIM-001 (Toyota Camry) |
| driver2@fleetpredict.local  | `DriverPass123!` | SIM-002 (Ford Transit) |
| …                         | `DriverPass123!` | …                  |
| driver10@fleetpredict.local | `DriverPass123!` | SIM-010 (Ford F-450 Ambulance) |

Los conductores solo ven su vehículo asignado en lista, detalle, historial, mantenimiento y alertas.

### Usuario para reportes y predicción (opcional)

Las vistas **Predicción de fallas** y **Reportes** (PDF) solo están disponibles para usuarios con permiso de reportes (Administrator o Fleet Manager). Para probar:

- Usa el superuser, o  
- Crea un usuario desde **Register** o desde el admin y asígnale rol *Fleet Manager* o *Administrator*.

---

## Estructura del proyecto

```
dev/
├── fleetpredict/              # Proyecto Django (settings, urls, ASGI/WSGI)
│   ├── context_processors.py   # Badge de alertas no leídas en nav
│   └── ...
├── apps/
│   ├── users/                  # Autenticación, perfiles, roles (FR1, FR21)
│   ├── vehicles/               # Registro, telemetría, alertas, runbooks (FR2, FR6, FR7, FR9)
│   │   ├── services/           # Patrones de telemetría y evaluación de alertas
│   │   ├── notifications.py   # Envío de emails por alertas high/critical
│   │   └── management/commands/
│   │       ├── seed_simulated_fleet.py
│   │       └── seed_playbooks_runbooks.py
│   ├── maintenance/            # Tareas de mantenimiento (FR4, FR5)
│   │   └── management/commands/
│   │       └── seed_maintenance_tasks.py
│   ├── dashboard/             # Dashboard, SOC, alertas, predicción (FR3, FR7, FR9)
│   └── reports/               # Exportación de reportes PDF (LaTeX)
├── templates/                 # Plantillas HTML y LaTeX (reports)
├── static/                    # CSS, JS, imágenes
├── simulators/                # Cliente de telemetría por WebSocket
├── requirements.txt
├── manage.py
└── README.md
```

---

## Requisitos implementados

### Sprint 1

| ID   | Requisito                              | Estado |
|------|----------------------------------------|--------|
| FR1  | Control de acceso por roles            | ✅     |
| FR2  | Registro de vehículos                  | ✅     |
| FR3  | Dashboard de monitoreo                 | ✅     |
| FR4  | Sistema de gestión de mantenimiento    | ✅     |
| FR5  | Historial de mantenimiento por vehículo| ✅     |
| FR21 | Gestión de perfil de usuario          | ✅     |

### Sprint 2

| ID   | Requisito                                      | Estado |
|------|------------------------------------------------|--------|
| FR6  | Indicador de salud (verde/amarillo/rojo) por vehículo | ✅ |
| FR7  | Centro de notificaciones y alertas por email   | ✅     |
| FR9  | Vista “Predicción de fallas” y plazo (timeframe)| ✅   |
| —    | Reportes PDF (LaTeX) por vehículo y flota      | ✅     |
| —    | Seed de tareas de mantenimiento de ejemplo    | ✅     |
| —    | Tests (modelos, servicios, vistas, consumers) | ✅    |
| —    | Hardening de seguridad (settings, permisos, escape LaTeX) | ✅ |

---

## Instalación y configuración

### Requisitos previos

- Python 3.10 o superior  
- Opcional: **LaTeX** (pdflatex) para generar reportes PDF. Si no está instalado, las vistas de reportes devolverán error al generar el PDF.

### Instalación

```bash
cd dev
python -m venv venv

# Linux/macOS
source venv/bin/activate
# Windows
# venv\Scripts\activate

pip install -r requirements.txt
```

### Base de datos

Por defecto se usa SQLite. No hace falta crear la base manualmente.

```bash
python manage.py migrate
```

### Variables de entorno

Puedes usar un archivo `.env` o exportar variables. Las siguientes son las más útiles:

```bash
# Obligatorias en producción
DJANGO_SECRET_KEY=tu-clave-secreta-muy-larga-y-aleatoria
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=tu-dominio.com,www.tu-dominio.com

# Desarrollo (valores por defecto si no se definen)
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

# Opcionales
SESSION_COOKIE_AGE=1209600          # Segundos (por defecto 14 días)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend   # Emails en consola (dev)
DEFAULT_FROM_EMAIL=FleetPredict <noreply@ejemplo.com>
# Para SMTP real: EMAIL_HOST, EMAIL_PORT, EMAIL_USE_TLS, EMAIL_HOST_USER, EMAIL_HOST_PASSWORD

# WebSocket ingesta de telemetría (opcional)
TELEMETRY_WS_TOKEN=token-secreto   # Si se define, /ws/telemetry/ exige ?token=...
```

### Crear superuser

```bash
python manage.py createsuperuser
```

Indica email y contraseña. Este usuario tendrá acceso total.

---

## Arranque rápido (flujo típico)

1. **Entorno y migraciones**
   ```bash
   cd dev && source venv/bin/activate
   pip install -r requirements.txt
   python manage.py migrate
   python manage.py createsuperuser
   ```

2. **Datos de prueba**
   ```bash
   python manage.py seed_simulated_fleet      # Vehículos SIM-001…SIM-010 y 10 conductores
   python manage.py seed_playbooks_runbooks  # Playbooks y runbooks para el SOC
   python manage.py seed_maintenance_tasks    # Tareas de mantenimiento de ejemplo por vehículo
   ```

3. **Servidor**
   - Solo HTTP (sin WebSocket): `python manage.py runserver`
   - Con WebSocket (telemetría en vivo): `pip install daphne && daphne -b 0.0.0.0 -p 8000 fleetpredict.asgi:application`

4. **Abrir**  
   http://localhost:8000  
   Iniciar sesión con el superuser o con `driver1@fleetpredict.local` / `DriverPass123!` para ver el flujo de conductor.

5. **Simulador de telemetría (opcional)**  
   Con el servidor ASGI en marcha, en otra terminal:
   ```bash
   cd dev
   python -m simulators.telemetry_client --url ws://127.0.0.1:8000/ws/telemetry/ --interval 2
   ```
   Así se generan alertas (temperatura, combustible, etc.) y se actualiza el indicador de salud y la telemetría en vivo en la ficha del vehículo.

---

## Comandos de gestión

| Comando | Descripción |
|---------|-------------|
| `python manage.py seed_simulated_fleet` | Crea tipos de vehículo, 10 vehículos SIM-001…SIM-010 y 10 conductores. Opción `--clear` para borrar solo vehículos SIM-* y volver a crearlos. |
| `python manage.py seed_playbooks_runbooks` | Crea playbooks y runbooks por tipo de alerta (marcar leída, crear tarea de mantenimiento, etc.) para el SOC del dashboard. |
| `python manage.py seed_maintenance_tasks` | Crea tareas de mantenimiento de ejemplo (completadas y programadas) para cada vehículo SIM-*. Opción `--clear` para borrar solo las tareas creadas por este seed (título con prefijo `[Seed] `). |

---

## Rutas de la aplicación

### Autenticación

| Ruta | Descripción |
|------|-------------|
| `/login/` | Inicio de sesión |
| `/logout/` | Cerrar sesión |
| `/register/` | Registro de usuario |
| `/profile/` | Editar perfil y preferencias de notificaciones |
| `/profile/password/` | Cambiar contraseña |

### Dashboard y alertas

| Ruta | Descripción |
|------|-------------|
| `/` | Dashboard (estado de flota, métricas, mantenimiento próximo, SOC con alertas y runbooks, salud FR6) |
| `/soc/runbook/` | POST: ejecutar runbook sobre una alerta (marcar leída, crear tarea, etc.) |
| `/alerts/` | Centro de notificaciones (FR7): listado de alertas con filtros y acciones runbook. Badge de no leídas en el nav. |
| `/predictions/` | Predicción de fallas (FR9): recomendaciones con plazo y confianza. Solo usuarios con permiso de reportes. |

### Vehículos

| Ruta | Descripción |
|------|-------------|
| `/vehicles/` | Lista de vehículos (con indicador de salud). Conductores solo ven los asignados. |
| `/vehicles/create/` | Alta de vehículo (admin/fleet manager) |
| `/vehicles/<id>/` | Detalle (telemetría en vivo si hay ASGI, botón “Exportar reporte PDF” si tienes permiso) |
| `/vehicles/<id>/edit/` | Editar vehículo |
| `/vehicles/<id>/delete/` | Borrado lógico |
| `/vehicles/<id>/history/` | Historial de mantenimiento (tareas completadas) |

### Mantenimiento

| Ruta | Descripción |
|------|-------------|
| `/maintenance/` | Lista de tareas |
| `/maintenance/create/` | Crear tarea |
| `/maintenance/<id>/` | Detalle de tarea |
| `/maintenance/<id>/edit/` | Editar tarea |
| `/maintenance/<id>/complete/` | Marcar completada |
| `/maintenance/<id>/documents/` | Subir documentos |

### Reportes (solo con permiso de reportes)

| Ruta | Descripción |
|------|-------------|
| `/reports/` | Página de reportes: enlace a reporte flota y explicación del reporte por vehículo |
| `/reports/vehicle/<id>/` | Descarga PDF del reporte de un vehículo (cabecera, historial mantenimiento, alertas recientes, última telemetría) |
| `/reports/fleet/` | Descarga PDF del reporte de flota (resumen por vehículo: salud, última alerta, próximo mantenimiento, km) |

### Usuarios (solo administrador)

| Ruta | Descripción |
|------|-------------|
| `/users/` | Lista de usuarios |
| `/users/<id>/` | Detalle de usuario |

### Admin Django

| Ruta | Descripción |
|------|-------------|
| `/admin/` | Panel de administración (superuser) |

---

## Roles y permisos

| Rol | Permisos |
|-----|----------|
| **Administrator** | Todo: usuarios, vehículos, mantenimiento, reportes, predicción, alertas, admin Django. |
| **Fleet Manager** | Gestionar vehículos y mantenimiento; ver reportes, predicción y centro de alertas. |
| **Mechanic** | Ver y gestionar tareas de mantenimiento. |
| **Driver** | Ver solo sus vehículos asignados, su mantenimiento e historial; centro de alertas filtrado por sus vehículos. No ve reportes ni predicción de fallas. |

---

## Telemetría y simuladores

- **Ingesta:** Los simuladores (o dispositivos) envían JSON por WebSocket a `/ws/telemetry/`. Se puede proteger con `TELEMETRY_WS_TOKEN` (parámetro `token` en la URL).
- **Patrones:** Tras guardar cada lectura se evalúan patrones (temperatura alta, combustible anómalo, mantenimiento por km/tiempo, etc.) y se crean `VehicleAlert` con severidad y, cuando aplica, `timeframe_text` (FR9).
- **Alertas por email (FR7):** Si la alerta es high o critical, se envía email a usuarios con permiso de reportes y preferencias de notificación activas (`email_enabled`, `critical_alerts` en el perfil).
- **Suscripción en el navegador:** La ficha del vehículo se suscribe por WebSocket a las actualizaciones de ese vehículo; solo si el usuario tiene permiso para verlo (conductores solo su vehículo).

---

## Reportes PDF

- **Requisito:** Tener `pdflatex` instalado en el sistema para generar los PDF. Si no está instalado, las vistas de descarga devolverán error 500 al generar.
- **Contenido reporte por vehículo:** Datos del vehículo, tabla de historial de mantenimiento, alertas recientes, última telemetría.
- **Reporte flota:** Tabla resumen (vehículo, salud, última alerta, próximo mantenimiento, kilometraje).
- **Seguridad:** Los datos que se insertan en las plantillas LaTeX se escapan para evitar inyección de comandos. Solo usuarios con permiso de reportes y solo para vehículos que pueden ver pueden descargar cada reporte.

---

## Tests

Ejecutar todos los tests de las apps principales:

```bash
python manage.py test apps.vehicles.tests apps.maintenance.tests apps.dashboard.tests apps.users.tests --verbosity=1
```

Incluyen: modelos (salud, alertas, runbooks, mantenimiento), servicios de patrones de telemetría, vistas por rol (conductores solo sus vehículos), ejecución de runbooks, historial. Los tests del consumer de WebSocket se omiten si no está instalado el paquete `channels`.

---

## Seguridad (producción)

Con `DEBUG=False`, en `settings` se aplica automáticamente:

- Redirección HTTPS y cabecera de proxy.
- Cookies de sesión y CSRF solo por HTTPS, HttpOnly, SameSite.
- Cabeceras de seguridad (XSS filter, X-Content-Type-Options, X-Frame-Options).

En producción es necesario definir:

- `DJANGO_SECRET_KEY`: valor aleatorio y seguro (no usar el valor por defecto).
- `DJANGO_DEBUG=False`
- `DJANGO_ALLOWED_HOSTS`: hosts permitidos separados por comas.

Además: la generación de PDF escapa los datos en plantillas LaTeX; la suscripción WebSocket a telemetría exige sesión autenticada y permiso sobre el vehículo; la ingesta WebSocket puede protegerse con `TELEMETRY_WS_TOKEN`.

---

## Tecnologías

- **Backend:** Django 5.x, SQLite (desarrollo), Bootstrap 5 (plantillas).
- **Arquitectura:** MVT, autenticación por sesión, HTML renderizado en servidor.
- **Tiempo real:** Django Channels y WebSocket para ingesta y suscripción a telemetría.
- **Alertas:** Servicio de patrones sobre telemetría reciente (temperatura, combustible, mantenimiento por km/días, etc.) que crea `VehicleAlert` y opcionalmente envía email.

---

## Notas de desarrollo

- El sistema **apoya la decisión humana**: las recomendaciones de mantenimiento y predicción de fallas no se ejecutan solas; se presentan en el dashboard, centro de alertas y predicción para que el usuario actúe (runbooks, tareas, etc.).
- El control de acceso por rol está aplicado en listas, detalle, historial, mantenimiento, reportes, predicción y ejecución de runbooks.
- Para desarrollo con emails sin SMTP real se usa el backend de consola (`EMAIL_BACKEND=...console...`); los mensajes se imprimen en la salida del servidor.
