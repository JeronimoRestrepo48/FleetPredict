# FleetPredict Pro – Development environment

Predictive maintenance system for transport fleets. Includes vehicle registry, near real-time dashboard, telemetry-pattern alerts, notification center, failure predictions, PDF reports, and maintenance management.

---

## Access credentials

### Administrator (superuser)

There is no default user. Create one after running migrations:

```bash
python manage.py createsuperuser
```

Use **email** (e.g. `admin@fleetpredict.local`), name, and **password**. This user has the *Administrator* role and full access (Django admin at `/admin/`, users, reports, etc.).

### Test drivers (created by seed)

After running `python manage.py seed_simulated_fleet`, 10 drivers are created and assigned to simulated vehicles SIM-001 … SIM-010:

| Email                     | Password        | Assigned vehicle   |
|---------------------------|-----------------|--------------------|
| driver1@fleetpredict.local  | `DriverPass123!` | SIM-001 (Toyota Camry) |
| driver2@fleetpredict.local  | `DriverPass123!` | SIM-002 (Ford Transit) |
| …                         | `DriverPass123!` | …                  |
| driver10@fleetpredict.local | `DriverPass123!` | SIM-010 (Ford F-450 Ambulance) |

Drivers only see their assigned vehicle in list, detail, history, maintenance, and alerts.

### User for reports and predictions (optional)

**Failure predictions** and **Reports** (PDF) views are only available to users with report permission (Administrator or Fleet Manager). To test:

- Use the superuser, or  
- Create a user via **Register** or the admin and assign role *Fleet Manager* or *Administrator*.

---

## Project structure

```
dev/
├── fleetpredict/              # Django project (settings, urls, ASGI/WSGI)
│   ├── context_processors.py   # Unread alerts badge in nav
│   └── ...
├── apps/
│   ├── users/                  # Auth, profiles, roles (FR1, FR21)
│   ├── vehicles/               # Registry, telemetry, alerts, runbooks (FR2, FR6, FR7, FR9)
│   │   ├── services/           # Telemetry patterns and alert evaluation
│   │   ├── notifications.py   # Email for high/critical alerts
│   │   └── management/commands/
│   │       ├── seed_simulated_fleet.py
│   │       └── seed_playbooks_runbooks.py
│   ├── maintenance/            # Maintenance tasks (FR4, FR5, FR23, FR24)
│   │   └── management/commands/
│   │       └── seed_maintenance_tasks.py
│   ├── dashboard/              # Dashboard, SOC, alerts, predictions, audit (FR3, FR7, FR8, FR9, FR11, FR27)
│   └── reports/                # PDF report export (LaTeX) and analytics (FR12–15)
├── templates/                  # HTML and LaTeX templates (reports)
├── static/                     # CSS, JS, images
├── simulators/                 # WebSocket telemetry client
├── requirements.txt
├── manage.py
└── README.md
```

---

## Implemented requirements

### Sprint 1

| ID   | Requirement                           | Status |
|------|----------------------------------------|--------|
| FR1  | Role-based access control              | ✅     |
| FR2  | Vehicle registry                       | ✅     |
| FR3  | Monitoring dashboard                   | ✅     |
| FR4  | Maintenance management system          | ✅     |
| FR5  | Maintenance history per vehicle        | ✅     |
| FR21 | User profile management                | ✅     |

### Sprint 2 and beyond

| ID   | Requirement                                      | Status |
|------|--------------------------------------------------|--------|
| FR6  | Vehicle health indicator (green/yellow/red)      | ✅     |
| FR7  | Notification center and email alerts             | ✅     |
| FR8  | Configurable alert thresholds                    | ✅     |
| FR9  | Failure prediction view and timeframe            | ✅     |
| FR10 | Severity filter in predictions                  | ✅     |
| FR11 | Suggested maintenance (accept/dismiss)          | ✅     |
| FR12–15 | Trends, cost, comparison reports             | ✅     |
| FR16 | Bulk CSV export (vehicles, maintenance)         | ✅     |
| FR22 | Vehicle types CRUD (admin)                      | ✅     |
| FR23 | Maintenance templates CRUD + apply on task create| ✅     |
| FR24 | Work orders (model + list/detail/create/edit)   | ✅     |
| FR25 | Regulatory compliance + expiration alerts        | ✅     |
| FR27 | Audit log (model + list + logging)              | ✅     |
| —    | PDF reports (LaTeX) per vehicle and fleet       | ✅     |
| —    | Seed commands (fleet, playbooks, maintenance)   | ✅     |
| —    | Tests (models, services, views, consumers)      | ✅     |

---

## Installation and setup

### Prerequisites

- Python 3.10 or higher  
- Optional: **LaTeX** (pdflatex) for PDF reports. If not installed, report views will error when generating PDFs.

### Installation

```bash
cd dev
python -m venv venv

# Linux/macOS
source venv/bin/activate
# Windows
# venv\Scripts\activate

pip install -r requirements.txt
```

### Database

SQLite is used by default. No need to create the database manually.

```bash
python manage.py migrate
```

### Environment variables

You can use a `.env` file or export variables. Useful ones:

```bash
# Required in production
DJANGO_SECRET_KEY=your-long-random-secret-key
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=your-domain.com,www.your-domain.com

# Development (defaults if not set)
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

# Optional
SESSION_COOKIE_AGE=1209600          # Seconds (default 14 days)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend   # Console email (dev)
DEFAULT_FROM_EMAIL=FleetPredict <noreply@example.com>
# For real SMTP: EMAIL_HOST, EMAIL_PORT, EMAIL_USE_TLS, EMAIL_HOST_USER, EMAIL_HOST_PASSWORD

# WebSocket telemetry (optional)
TELEMETRY_WS_TOKEN=secret-token   # If set, /ws/telemetry/ requires ?token=...
```

### Create superuser

```bash
python manage.py createsuperuser
```

Use email and password. This user has full access.

---

## Quick start (typical flow)

1. **Environment and migrations**
   ```bash
   cd dev && source venv/bin/activate
   pip install -r requirements.txt
   python manage.py migrate
   python manage.py createsuperuser
   ```

2. **Test data**
   ```bash
   python manage.py seed_simulated_fleet      # Vehicles SIM-001…SIM-010 and 10 drivers
   python manage.py seed_playbooks_runbooks   # Playbooks and runbooks for SOC
   python manage.py seed_maintenance_tasks   # Sample maintenance tasks per vehicle
   ```

3. **Server**
   - HTTP only (no WebSocket): `python manage.py runserver`
   - With WebSocket (live telemetry): `pip install daphne && daphne -b 0.0.0.0 -p 8000 fleetpredict.asgi:application`

4. **Open**  
   http://localhost:8000  
   Log in with the superuser or `driver1@fleetpredict.local` / `DriverPass123!` to see the driver flow.

5. **Telemetry simulator (optional)**  
   With the ASGI server running, in another terminal:
   ```bash
   cd dev
   python -m simulators.telemetry_client --url ws://127.0.0.1:8000/ws/telemetry/ --interval 2
   ```
   This generates alerts (temperature, fuel, etc.) and updates health and live telemetry on the vehicle detail page.

---

## Management commands

| Command | Description |
|---------|-------------|
| `python manage.py seed_simulated_fleet` | Creates vehicle types, 10 vehicles SIM-001…SIM-010 and 10 drivers. Use `--clear` to remove only SIM-* vehicles and recreate. |
| `python manage.py seed_playbooks_runbooks` | Creates playbooks and runbooks per alert type (mark read, create maintenance task, etc.) for the dashboard SOC. |
| `python manage.py seed_maintenance_tasks` | Creates sample maintenance tasks (completed and scheduled) for each SIM-* vehicle. Use `--clear` to remove only seed-created tasks (title prefix `[Seed] `). |

---

## Application routes

### Authentication

| Route | Description |
|-------|-------------|
| `/login/` | Login |
| `/logout/` | Logout |
| `/register/` | User registration |
| `/profile/` | Edit profile and notification preferences |
| `/profile/password/` | Change password |

### Dashboard and alerts

| Route | Description |
|-------|-------------|
| `/` | Dashboard (fleet status, metrics, upcoming maintenance, SOC with alerts and runbooks, FR6 health) |
| `/soc/runbook/` | POST: execute runbook on an alert (mark read, create task, etc.) |
| `/alerts/` | Notification center (FR7): alert list with filters and runbook actions. Unread badge in nav. |
| `/predictions/` | Failure predictions (FR9): recommendations with timeframe and confidence. Report permission required. |
| `/suggested-maintenance/` | FR11: accept or dismiss suggested maintenance from predictions. |
| `/alert-rules/` | FR8: configurable alert thresholds. |
| `/audit-log/` | FR27: audit log list (administrator only). |

### Vehicles

| Route | Description |
|-------|-------------|
| `/vehicles/` | Vehicle list (with health indicator). Drivers see only assigned. |
| `/vehicles/export/csv/` | FR16: bulk export vehicles as CSV. |
| `/vehicles/create/` | Add vehicle (admin/fleet manager) |
| `/vehicles/<id>/` | Detail (live telemetry if ASGI; “Export PDF report” if permitted) |
| `/vehicles/<id>/edit/` | Edit vehicle |
| `/vehicles/<id>/delete/` | Soft delete |
| `/vehicles/<id>/history/` | Maintenance history (completed tasks) |
| `/vehicles/compliance/` | FR25: compliance requirements list. |
| `/vehicles/types/` | FR22: vehicle types (admin only). |

### Maintenance

| Route | Description |
|-------|-------------|
| `/maintenance/` | Task list |
| `/maintenance/export/csv/` | FR16: bulk export maintenance as CSV. |
| `/maintenance/create/` | Create task (supports ?template=<id>) |
| `/maintenance/templates/` | FR23: maintenance templates CRUD. |
| `/maintenance/work-orders/` | FR24: work orders list. |
| `/maintenance/<id>/` | Task detail |
| `/maintenance/<id>/edit/` | Edit task |
| `/maintenance/<id>/complete/` | Mark completed |
| `/maintenance/<id>/documents/` | Upload documents |

### Reports (report permission required)

| Route | Description |
|-------|-------------|
| `/reports/` | Reports page: fleet report and per-vehicle report; analytics (trends, cost, comparison). |
| `/reports/vehicle/<id>/` | Download PDF for one vehicle. |
| `/reports/fleet/` | Download fleet PDF. |
| `/reports/trends/` | FR12: maintenance trends. |
| `/reports/cost/` | FR13: cost report. |
| `/reports/comparison/` | FR14/15: comparison report. |

### Users (administrator only)

| Route | Description |
|-------|-------------|
| `/users/` | User list |
| `/users/<id>/` | User detail |

### Django admin

| Route | Description |
|-------|-------------|
| `/admin/` | Admin panel (superuser) |

---

## Roles and permissions

| Role | Permissions |
|------|-------------|
| **Administrator** | Full: users, vehicles, maintenance, reports, predictions, alerts, vehicle types, audit log, Django admin. |
| **Fleet Manager** | Manage vehicles and maintenance; view reports, predictions, alerts, compliance, alert rules. |
| **Mechanic** | View and manage maintenance tasks. |
| **Driver** | View only assigned vehicles, their maintenance and history; alerts filtered by their vehicles. No reports or failure predictions. |

---

## Telemetry and simulators

- **Ingest:** Simulators (or devices) send JSON over WebSocket to `/ws/telemetry/`. Can be protected with `TELEMETRY_WS_TOKEN` (URL query `token`).
- **Patterns:** After each reading is saved, patterns (high temperature, anomalous fuel, maintenance by km/time, etc.) are evaluated and `VehicleAlert` records are created with severity and, when applicable, `timeframe_text` (FR9).
- **Email alerts (FR7):** For high or critical alerts, email is sent to users with report permission and notification preferences enabled (`email_enabled`, `critical_alerts` in profile).
- **Browser subscription:** The vehicle detail page subscribes via WebSocket to that vehicle’s updates; only if the user is allowed to see it (drivers only their vehicle).

---

## PDF reports

- **Requirement:** Have `pdflatex` installed to generate PDFs. If not installed, download views will return 500 when generating.
- **Vehicle report content:** Vehicle data, maintenance history table, recent alerts, latest telemetry.
- **Fleet report:** Summary table (vehicle, health, latest alert, upcoming maintenance, mileage).
- **Security:** Data inserted into LaTeX templates is escaped to avoid command injection. Only users with report permission and only for vehicles they can see may download each report.

---

## Tests

Run tests for the main apps:

```bash
python manage.py test apps.vehicles.tests apps.maintenance.tests apps.dashboard.tests apps.users.tests apps.reports --verbosity=1
```

E2E tests (Playwright):

```bash
cd dev && npm install && npx playwright install
python manage.py runserver &
npx playwright test
```

---

## Security (production)

With `DEBUG=False`, settings automatically apply:

- HTTPS redirect and proxy headers.
- Session and CSRF cookies over HTTPS only, HttpOnly, SameSite.
- Security headers (XSS filter, X-Content-Type-Options, X-Frame-Options).

In production you must set:

- `DJANGO_SECRET_KEY`: random and secure (do not use the default).
- `DJANGO_DEBUG=False`
- `DJANGO_ALLOWED_HOSTS`: comma-separated allowed hosts.

Additionally: PDF generation escapes data in LaTeX templates; WebSocket subscription to telemetry requires an authenticated session and permission on the vehicle; WebSocket ingest can be protected with `TELEMETRY_WS_TOKEN`.

---

## Technologies

- **Backend:** Django 5.x, SQLite (development), Bootstrap 5 (templates).
- **Architecture:** MVT, session auth, server-rendered HTML.
- **Real time:** Django Channels and WebSocket for telemetry ingest and subscription.
- **Alerts:** Pattern service over recent telemetry (temperature, fuel, maintenance by km/days, etc.) creating `VehicleAlert` and optionally sending email.

---

## Development notes

- The system **supports human decisions**: maintenance recommendations and failure predictions are not executed automatically; they are shown on the dashboard, alert center, and predictions so the user can act (runbooks, tasks, etc.).
- Role-based access is enforced on lists, detail, history, maintenance, reports, predictions, and runbook execution.
- For development without real SMTP, use the console backend (`EMAIL_BACKEND=...console...`); messages are printed to the server output.
