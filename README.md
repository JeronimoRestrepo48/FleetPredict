# FleetPredict Pro - Development Environment

Predictive Fleet Maintenance System for transportation fleets.

## Project Structure

```
dev/
├── backend/                    # Django REST Framework API
│   ├── fleetpredict/          # Main Django project
│   ├── apps/
│   │   ├── users/             # Authentication & Profiles (FR1, FR21)
│   │   ├── vehicles/          # Vehicle Registry (FR2)
│   │   ├── maintenance/       # Maintenance Management (FR4, FR5)
│   │   └── dashboard/         # Dashboard API (FR3)
│   ├── requirements.txt
│   └── manage.py
├── frontend/                   # React + Vite Application
│   ├── src/
│   │   ├── components/        # Reusable components
│   │   ├── pages/             # Page components
│   │   ├── services/          # API services
│   │   ├── context/           # React context
│   │   └── App.jsx
│   ├── package.json
│   └── vite.config.js
└── README.md
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

## Backend Setup

### Prerequisites
- Python 3.10+
- PostgreSQL 14+

### Installation

```bash
# Navigate to backend folder
cd dev/backend

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

# CORS
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
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

Backend will be available at: http://localhost:8000

## Frontend Setup

### Prerequisites
- Node.js 18+
- npm or yarn

### Installation

```bash
# Navigate to frontend folder
cd dev/frontend

# Install dependencies
npm install
```

### Environment Variables

Create a `.env` file:

```bash
VITE_API_URL=http://localhost:8000/api
```

### Run Development Server

```bash
npm run dev
```

Frontend will be available at: http://localhost:5173

## API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register/` | User registration |
| POST | `/api/auth/login/` | User login (JWT) |
| POST | `/api/auth/logout/` | User logout |
| POST | `/api/auth/token/refresh/` | Refresh JWT token |

### Users
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/users/profile/` | Get current user profile |
| PUT | `/api/users/profile/` | Update profile |
| POST | `/api/users/profile/change-password/` | Change password |
| GET | `/api/users/` | List users (admin only) |
| GET | `/api/users/{id}/` | Get user details (admin only) |

### Vehicles
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/vehicles/` | List vehicles |
| POST | `/api/vehicles/` | Create vehicle |
| GET | `/api/vehicles/{id}/` | Get vehicle details |
| PUT | `/api/vehicles/{id}/` | Update vehicle |
| DELETE | `/api/vehicles/{id}/` | Delete vehicle |
| GET | `/api/vehicles/{id}/history/` | Get maintenance history |

### Maintenance
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/maintenance/` | List maintenance tasks |
| POST | `/api/maintenance/` | Create task |
| GET | `/api/maintenance/{id}/` | Get task details |
| PUT | `/api/maintenance/{id}/` | Update task |
| DELETE | `/api/maintenance/{id}/` | Delete task |
| POST | `/api/maintenance/{id}/complete/` | Mark as complete |
| POST | `/api/maintenance/{id}/status/` | Change status |
| POST | `/api/maintenance/{id}/documents/` | Upload document |
| POST | `/api/maintenance/{id}/comments/` | Add comment |

### Dashboard
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/dashboard/summary/` | Get dashboard data |
| GET | `/api/dashboard/stats/` | Get quick stats |

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
- Django REST Framework
- djangorestframework-simplejwt (JWT Auth)
- PostgreSQL / SQLite

### Frontend
- React 18
- Vite
- TailwindCSS
- Axios
- React Router DOM

## Development Notes

- The system is designed to **support decision-making**, not make automatic decisions
- All maintenance suggestions are recommendations for human review
- Role-based access control ensures proper authorization
