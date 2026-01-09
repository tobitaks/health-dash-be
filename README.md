# HealthDash - Hospital Management System

A comprehensive multi-tenant SaaS hospital management platform built with Django REST Framework, designed for clinics to manage patients, appointments, consultations, prescriptions, lab orders, and billing.

## Features

### Core Modules

- **Patient Management** - Patient registration, demographic data, contact information, medical history tracking
- **Appointment Scheduling** - Service-based appointments with date/time management and status tracking
- **Consultations** - Clinical encounters with vital signs, chief complaints, diagnoses, and clinical notes
- **Prescriptions** - Medicine catalog with dosage forms, prescription generation with multiple items
- **Lab Orders** - Laboratory test catalog, order management, results tracking with abnormal flags
- **Billing & Invoicing** - Invoice generation, line items, discount support (fixed/percentage), payment recording

### Platform Features

- **Multi-tenant Architecture** - Clinic-based data isolation ensuring each clinic only accesses their own data
- **Role-based Access Control** - Custom roles with granular policy-based permissions
- **User Management** - Staff management with role assignments
- **Service Catalog** - Configurable clinic services with pricing

## Tech Stack

| Layer | Technology |
|-------|------------|
| **Language** | Python 3.12 |
| **Framework** | Django 5.x, Django REST Framework |
| **Database** | PostgreSQL |
| **Cache** | Redis |
| **Task Queue** | Celery |
| **Authentication** | JWT (SimpleJWT), django-allauth |
| **Infrastructure** | Docker, Docker Compose |
| **Code Quality** | Ruff (linting/formatting), pre-commit hooks |

## Architecture

```
apps/
├── api/              # REST API endpoints and views
├── appointments/     # Appointment scheduling
├── billing/          # Invoices and payments
├── chat/             # Real-time messaging
├── clinic/           # Clinic and service management
├── consultations/    # Patient consultations
├── lab_orders/       # Laboratory orders and results
├── medicines/        # Medicine catalog
├── patients/         # Patient records
├── prescriptions/    # Prescription management
├── users/            # User, role, and permission management
└── utils/            # Shared utilities and base models
```

### Key Design Patterns

- **BaseModel** - All models inherit from a base class with `created_at` and `updated_at` timestamps
- **Clinic Tenancy** - Automatic queryset filtering by user's clinic via `ClinicQuerySetMixin`
- **Nested Serializers** - Support for creating parent-child records in single API calls (e.g., Invoice with InvoiceItems)
- **ID Generation** - Human-readable sequential IDs per clinic (e.g., `PT-2026-0001`, `INV-2026-0001`)

## Testing

Comprehensive test coverage with **400+ unit tests** across 11 apps:

| App | Tests | Coverage |
|-----|-------|----------|
| patients | 30 | Models, serializers, ID generation |
| appointments | 35 | Models, serializers, validation |
| clinic | 34 | Clinic, services, serializers |
| medicines | 30 | Medicine catalog, form/category choices |
| prescriptions | 40 | Prescriptions, items, nested creation |
| lab_orders | 38 | Lab tests, orders, results tracking |
| users | 71 | Users, roles, policies, permissions |
| billing | 50 | Invoices, payments, discounts |
| consultations | - | Consultation workflow |
| chat | - | Messaging |
| utils | - | Sanitization utilities |

Run tests:

```bash
make test
```

Run specific app tests:

```bash
make test ARGS='apps.billing.tests'
```

## Quick Start

### Prerequisites

- [Docker](https://www.docker.com/get-started) and [Docker Compose](https://docs.docker.com/compose/install)
- On Windows: [make](https://stackoverflow.com/a/57042516/8207)

### Installation

1. Clone the repository:

```bash
git clone https://github.com/tobitaks/health-dash-be.git
cd health-dash-be
```

2. Initialize the application:

```bash
make init
```

This will:
- Build and start PostgreSQL and Redis
- Build and start Django dev server
- Build and start Celery worker
- Build front-end assets
- Run database migrations

3. Access the application at [http://localhost:8000](http://localhost:8000)

### Common Commands

```bash
make start          # Start all services
make stop           # Stop all services
make test           # Run all tests
make shell          # Open Django shell
make dbshell        # Open PostgreSQL shell
make migrations     # Create new migrations
make migrate        # Apply migrations
make ruff           # Run linter and formatter
```

## API Endpoints

The REST API follows standard conventions:

| Resource | Endpoints |
|----------|-----------|
| Authentication | `/api/auth/register/`, `/api/auth/login/`, `/api/auth/logout/` |
| Patients | `/api/patients/` |
| Appointments | `/api/appointments/` |
| Consultations | `/api/consultations/` |
| Prescriptions | `/api/prescriptions/` |
| Lab Orders | `/api/lab-orders/` |
| Billing | `/api/invoices/` |
| Staff | `/api/staff/` |
| Roles | `/api/roles/` |

API documentation available at `/api/schema/` (OpenAPI/Swagger).

## Development

### Code Quality

```bash
make ruff-format    # Format code
make ruff-lint      # Lint and auto-fix
make ruff           # Run both
```

### Git Hooks

Install pre-commit hooks:

```bash
uv run pre-commit install --install-hooks
```

### Native Installation (without Docker)

```bash
# Install dependencies
uv sync

# Create database
createdb dash_hospital_mngt

# Run migrations
uv run manage.py migrate

# Start server
uv run manage.py runserver
```

## License

See [LICENSE.md](LICENSE.md) for details.
