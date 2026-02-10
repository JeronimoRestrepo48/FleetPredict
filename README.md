# FleetPredict Pro - Development Environment

Predictive Fleet Maintenance System for transportation fleets.

## Project Structure

```
dev/
├── fleetpredict/          # Django project
├── apps/
│   ├── users/             # Authentication & Profiles (FR1, FR21)
│   ├── vehicles/          # Vehicle Registry (FR2)
│   ├── maintenance/       # Maintenance Management (FR4, FR5)
│   └── dashboard/         # Dashboard (FR3)
├── templates/             # HTML templates (base, registration, app-specific)
├── static/                # CSS, JS, Bootstrap assets
├── media/                 # User uploads
├── requirements.txt
└── manage.py
```

## Sprint 1 Requirements Implemented

| ID | Requirement | Status |
|----|-------------|--------|
| FR1 | Role-based access control | ✅ |
| FR2 | Vehicle registry | ✅ |
| FR3 | Monitoring dashboard | ✅ |
| FR4 | Maintenance management system | ✅ |
| FR5 | Maintenance history per vehicle | ✅ |
| FR21 | User profile management | ✅ |

## Setup

### Prerequisites
- Python 3.10+

### Installation

```bash
# Navigate to dev folder
cd dev

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Linux/Mac:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Database Setup

SQLite is used by default for development. No manual database setup is required; the `db.sqlite3` file will be created automatically after running migrations.

### Environment Variables

Create a `.env` file or set environment variables:

```bash
# Django
DJANGO_SECRET_KEY=your-secret-key-here
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
```

### Run Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### Create Superuser

```bash
python manage.py createsuperuser
```

### Run Development Server

```bash
# HTTP only (WSGI)
python manage.py runserver
```

For **WebSocket telemetry** (simulators), run the ASGI server:

```bash
pip install daphne   # if not already installed
daphne -b 0.0.0.0 -p 8000 fleetpredict.asgi:application
```

Application will be available at: http://localhost:8000

### Simulated fleet and telemetry

1. **Seed 10 simulated vehicles** (SIM-001 … SIM-010) and vehicle types:
   ```bash
   python manage.py seed_simulated_fleet
   ```
   Use `--clear` to remove existing SIM-* vehicles and re-seed.

2. **Run telemetry simulators** (10 WebSocket clients sending real-time data):
   ```bash
   cd dev
   python -m simulators.telemetry_client --url ws://127.0.0.1:8000/ws/telemetry/ --interval 2
   ```
   Ensure the backend is running with ASGI (daphne) so `/ws/telemetry/` is available. Telemetry is stored in `VehicleTelemetry`; pattern evaluation creates `VehicleAlert` records (FR6/FR7/FR9).

3. **Drivers:** The same `seed_simulated_fleet` command creates 10 drivers (`driver1@fleetpredict.local` … `driver10@fleetpredict.local`) and assigns each to SIM-001 … SIM-010. Default password: `DriverPass123!`. Drivers see only their assigned vehicle and its live telemetry on the vehicle detail page.

4. **SOC playbooks and runbooks:** Seed default playbooks and runbooks for the dashboard SOC:
   ```bash
   python manage.py seed_playbooks_runbooks
   ```
   The dashboard shows a "Centro de operaciones (SOC)" section with high/critical alerts, suggested steps (playbooks), and runbook buttons (e.g. Mark as read, Create maintenance task).

**Live telemetry in the UI:** Open a vehicle detail page (e.g. `/vehicles/<id>/`) while the simulators are running and the ASGI server is up; the page subscribes via WebSocket to that vehicle’s telemetry and shows Encendido/Apagado (green/red) and live readings.

## Routes (MVT)

### Authentication
| Path | Description |
|------|-------------|
| `/login/` | Login |
| `/logout/` | Logout |
| `/register/` | User registration |
| `/profile/` | Profile edit |
| `/profile/password/` | Change password |

### Dashboard
| Path | Description |
|------|-------------|
| `/` | Dashboard (fleet status, metrics, SOC alerts with playbooks/runbooks) |
| `/soc/runbook/` | POST: execute runbook for an alert (internal) |

### Vehicles
| Path | Description |
|------|-------------|
| `/vehicles/` | List vehicles |
| `/vehicles/create/` | Create vehicle |
| `/vehicles/<id>/` | Vehicle detail |
| `/vehicles/<id>/edit/` | Edit vehicle |
| `/vehicles/<id>/delete/` | Delete vehicle (soft) |
| `/vehicles/<id>/history/` | Maintenance history |

### Maintenance
| Path | Description |
|------|-------------|
| `/maintenance/` | List tasks |
| `/maintenance/create/` | Create task |
| `/maintenance/<id>/` | Task detail |
| `/maintenance/<id>/edit/` | Edit task |
| `/maintenance/<id>/complete/` | Mark complete |
| `/maintenance/<id>/documents/` | Upload document |

### Users (Admin only)
| Path | Description |
|------|-------------|
| `/users/` | List users |
| `/users/<id>/` | User detail |

## User Roles

| Role | Permissions |
|------|-------------|
| Administrator | Full access to all features |
| Fleet Manager | Manage vehicles, maintenance, view reports |
| Mechanic | View/manage maintenance tasks |
| Driver | View assigned vehicles and maintenance |

## Technologies

### Backend
- Django 5.0+
- SQLite (default dev database)
- Bootstrap 5 (CDN)

### Architecture
- Monolithic Django MVT (Models, Views, Templates)
- Session-based authentication
- Server-rendered HTML templates
- Django Channels + WebSocket for real-time telemetry (`/ws/telemetry/`)
- Pattern/AI service: evaluates telemetry and creates `VehicleAlert` (high temp, anomalous fuel, harsh driving, idle, maintenance due, statistical anomaly)

## Security (production)

When `DEBUG` is `False`, the following hardening is applied automatically in settings:

- **SECURE_SSL_REDIRECT** and **SECURE_PROXY_SSL_HEADER**: enforce HTTPS.
- **SESSION_COOKIE_SECURE**, **CSRF_COOKIE_SECURE**: cookies sent only over HTTPS.
- **SESSION_COOKIE_HTTPONLY**, **SESSION_COOKIE_SAMESITE**: mitigate XSS and CSRF.
- **SECURE_BROWSER_XSS_FILTER**, **SECURE_CONTENT_TYPE_NOSNIFF**, **X_FRAME_OPTIONS**: headers for browser security.

Set in production:

- `DJANGO_SECRET_KEY`: strong random value (do not use the default).
- `DJANGO_DEBUG=False`
- `DJANGO_ALLOWED_HOSTS`: comma-separated list of allowed hosts.

Report PDF generation escapes user-supplied data before injecting into LaTeX templates to prevent command injection. WebSocket subscription to vehicle telemetry requires an authenticated session; the telemetry ingestion endpoint can be protected with `TELEMETRY_WS_TOKEN` in settings (query param `token`).

## Development Notes

- The system is designed to **support decision-making**, not make automatic decisions
- All maintenance suggestions are recommendations for human review
- Role-based access control ensures proper authorization
