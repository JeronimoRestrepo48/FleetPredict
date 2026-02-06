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
- PostgreSQL 14+

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

1. Create PostgreSQL database:
```sql
CREATE DATABASE fleetpredict;
CREATE USER postgres WITH PASSWORD 'postgres';
GRANT ALL PRIVILEGES ON DATABASE fleetpredict TO postgres;
```

2. Or use SQLite for development:
```bash
export USE_SQLITE=True
```

### Environment Variables

Create a `.env` file or set environment variables:

```bash
# Django
DJANGO_SECRET_KEY=your-secret-key-here
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

# Database (PostgreSQL)
DB_NAME=fleetpredict
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5432

# Or use SQLite
USE_SQLITE=True
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
python manage.py runserver
```

Application will be available at: http://localhost:8000

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
| `/` | Dashboard (fleet status, metrics) |

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
- PostgreSQL / SQLite
- Bootstrap 5 (CDN)

### Architecture
- Monolithic Django MVT (Models, Views, Templates)
- Session-based authentication
- Server-rendered HTML templates

## Development Notes

- The system is designed to **support decision-making**, not make automatic decisions
- All maintenance suggestions are recommendations for human review
- Role-based access control ensures proper authorization
