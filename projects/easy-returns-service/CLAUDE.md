# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is the Easy Returns Service - a Django-based microservice within the Meest Logistics platform that handles parcel returns, carrier integration, pricing calculations, and payment processing for e-commerce logistics operations.

## Repository Structure

### Core Application Structure
- **meestpost_backend/**: Django project configuration and core settings
  - **settings/**: Modular Django settings (django.py, amqp.py, cors.py, etc.)
  - **static/**: Admin interface customizations and branding assets
  - **templates/**: Custom Django admin templates

### Main Application Modules
- **parcels/**: Core logistics functionality - parcel management, carriers, pricing, return orders
- **users/**: User management, customer profiles, and authentication
- **payments/**: Payment processing integration (Portmone, etc.)
- **orders/**: Order management and coupon system
- **messaging/**: Email template system and notification management
- **common/**: Shared utilities, admin customizations, and common components
- **amqp_connection/**: Message broker integration and async task handling

### Supporting Infrastructure
- **docker/**: Docker configuration for production deployment
- **fixtures/**: Database fixtures for permissions and initial data
- **scripts/**: Deployment and utility scripts

## Technology Stack

### Core Framework & Database
- **Django 4.2** - Web framework with REST API capabilities
- **Django REST Framework 3.x** - API development
- **PostgreSQL** - Primary database (via psycopg2)
- **Redis** - Caching and session storage
- **Python 3.12** - Runtime environment

### Key Dependencies & Libraries
- **django-simple-history** - Model change tracking
- **django-countries** - Country field support
- **django-modeltranslation** - Multi-language content
- **django-admin-tools** - Enhanced admin interface
- **django-dynamic-preferences** - Configuration management
- **django-cors-headers** - CORS handling for frontend integration
- **djangorestframework-simplejwt** - JWT authentication
- **celery 5.x** - Asynchronous task processing
- **boto3** - AWS services integration
- **sentry-sdk** - Error monitoring and logging
- **gunicorn** - WSGI HTTP server for production

### Internal Libraries (Sources in `external-sources/`)
These libraries have no public documentation. Source code is available locally for reference.

- **mwl-connection** (v0.6.9) - Internal Meest logistics API client
  - Source: `external-sources/mwl_connection-0.6.9-py3-none-any/mwl_connection/`
  - Provides: `enums` (CountryCode, ReturnPayer, etc.), `company`, `mwl.pdu`, `returns`, `comm`, `exceptions`
  - Used for: All external Meest Logistics API integrations

- **amqp-service** (v0.2.2) - RabbitMQ message handling
  - Source: `external-sources/amqp_service-0.2.2-py3-none-any/amqp_service/`
  - Provides: `Producer`, `declare_amqp`, `ExchangeOptions`

- **django-admin-custom-buttons** (v0.2.0) - Custom admin interface buttons
  - Source: `external-sources/django-admin-custom-buttons-0.2.0/admin_custom_buttons/`
  - Provides: `Button`, `CustomButtonsAdminModel`

- **aio-pika** (v9.5.5) - Async AMQP client for RabbitMQ (less mainstream, source included)
  - Source: `external-sources/aio_pika-9.5.5-py3-none-any/aio_pika/`
  - Provides: `connect_robust`, `ExchangeType`, `AbstractRobustConnection`

### Other Integrations
- **django-weasyprint** - PDF generation for labels and documents
- **xlsxwriter, openpyxl** - Excel file processing
- **requests** - HTTP client for external API integration

### Development & Testing
- **tox** - Testing environment management
- **ruff** - Code formatting and linting
- **mypy** - Static type checking
- **coverage** - Test coverage reporting
- **factory-boy** - Test data generation
- **django-debug-toolbar** - Development debugging

## Architecture Overview

### Core Business Logic
The service manages the complete returns lifecycle:
1. **Parcel Management** (`parcels/models/parcel.py`) - Core parcel entities and status tracking
2. **Carrier Integration** (`parcels/models/carrier.py`) - Multiple shipping carrier support
3. **Pricing Engine** (`parcels/models/pricing.py`) - Dynamic pricing calculations
4. **Return Orders** (`parcels/models/return_order.py`) - Return request processing
5. **Payment Processing** (`payments/models/payment.py`) - Transaction handling

### API Structure
- **Public API** (`/api/`) - External integration endpoints:
  - `/getParcelInfo/` - Parcel information retrieval
  - `/getCarriers/` - Available carriers and pricing
  - `/transaction/` - Transaction processing
  - `/getLabel/` - Shipping label generation
- **Admin API** (`/admin/api/`) - Internal management endpoints
- **Swagger Documentation** - Available at `/swagger/` and `/admin/swagger/`

### Database Architecture
- **User Management**: Custom user model with customer profiles
- **Parcel System**: Hierarchical parcel → parcel_item → pricing structure
- **Historical Tracking**: Simple History integration for audit trails
- **Multi-language**: Model translation support for international operations

## Development Commands

**IMPORTANT: This project uses Poetry for dependency management. All commands should be run using `poetry run` prefix or within a Poetry shell.**

### Environment Setup
```bash
# Install dependencies (including dev dependencies)
poetry install

# Install only production dependencies
poetry install --without dev

# Activate virtual environment (optional - or use 'poetry run' prefix)
poetry shell

# Show virtual environment information
poetry env info

# Database migrations
poetry run python manage.py migrate

# Create superuser
poetry run python manage.py createsuperuser

# Collect static files
poetry run python manage.py collectstatic
```

### Testing and Code Quality
```bash
# Run full test suite with linting (uses tox configuration)
poetry run tox

# Run specific tox environment
poetry run tox -e standard    # Full test suite with formatting and linting
poetry run tox -e tests       # Tests with linting only
poetry run tox -e coverage    # Tests with HTML coverage report

# Run tests only (Django test runner)
poetry run python manage.py test

# Run tests for specific app
poetry run python manage.py test parcels

# Code formatting with ruff
poetry run ruff format ./

# Code linting with auto-fix
poetry run ruff check ./ --fix

# Code linting without fixes (check only)
poetry run ruff check ./

# Test coverage (run tests and generate report)
poetry run coverage run manage.py test
poetry run coverage report

# Test coverage with HTML report
poetry run coverage run manage.py test
poetry run coverage html -d coverage_html_report
```

### Development Server
```bash
# Start development server
poetry run python manage.py runserver

# Start server on specific host/port
poetry run python manage.py runserver 0.0.0.0:8000

# Start production server with Gunicorn
poetry run gunicorn meestpost_backend.wsgi:application --bind 0.0.0.0:9200
```

### Database Operations
```bash
# Create new migration
poetry run python manage.py makemigrations

# Create migration for specific app
poetry run python manage.py makemigrations parcels

# Apply migrations
poetry run python manage.py migrate

# Show migration status
poetry run python manage.py showmigrations

# Database shell
poetry run python manage.py dbshell

# Django shell (Python REPL with Django context)
poetry run python manage.py shell
```

### Celery (Async Tasks)
```bash
# Start Celery worker
poetry run celery -A meestpost_backend worker -l info

# Start Celery beat scheduler
poetry run celery -A meestpost_backend beat -l info

# Start both worker and beat together
poetry run celery -A meestpost_backend worker -l info -B
```

### Docker Development
```bash
# Start local development services (PostgreSQL, Redis, RabbitMQ)
docker-compose -f docker/local/docker-compose.yml up -d

# View logs
docker-compose -f docker/local/docker-compose.yml logs -f

# Stop services
docker-compose -f docker/local/docker-compose.yml down

# Reset database (recreate with fresh volumes)
docker-compose -f docker/local/docker-compose.yml down -v && docker-compose -f docker/local/docker-compose.yml up -d
```

### Utility Commands
```bash
# Clear cache
poetry run python manage.py clearcache

# Generate Swagger schema
poetry run python manage.py generate_swagger

# Check for Django issues
poetry run python manage.py check

# Compile translation messages
poetry run python manage.py compilemessages

# Make translation messages
poetry run python manage.py makemessages

# List all available management commands
poetry run python manage.py help
```

### Notes on Removed Commands
The following commands were listed in previous versions but are **NOT available** in the current environment:
- `mypy ./` - mypy is not installed in the Poetry environment (commented out in tox.ini)

## Configuration

### Environment Variables
The application uses environment-based configuration via `.env` files:
- `SECRET_KEY` - Django secret key
- `DEBUG` - Debug mode (True/False)
- `DB_URL` - Database connection string
- `REDIS_HOST` - Redis server host
- `FRONTEND_BASE_URL` - Frontend application URL
- `BACKEND_BASE_URL` - Backend API URL

### Key Settings Files
- `meestpost_backend/settings/django.py` - Core Django configuration
- `meestpost_backend/settings/amqp.py` - Message broker settings  
- `meestpost_backend/settings/rest_framework.py` - API configuration

## Important Code References

### Core Models
- User management: `users/models/user.py:1`
- Parcel entity: `parcels/models/parcel.py:47`
- Carrier configuration: `parcels/models/carrier.py:1`
- Payment processing: `payments/models/payment.py:1`

### API Endpoints
- Main URL configuration: `meestpost_backend/urls.py:29`
- Parcel API views: `parcels/api/views/`
- Payment webhooks: `payments/api/views/portmone_webhook_views.py:1`

### Admin Interface
- Custom admin site: `meestpost_backend/site.py:1`
- Parcel admin: `parcels/admin/parcel_admin.py:1`
- Admin customizations: `common/admin/`

## Testing Strategy

### Test Structure
- **Unit Tests**: Model and utility function testing
- **API Tests**: REST endpoint testing
- **Admin Tests**: Django admin interface testing
- **Integration Tests**: Cross-module functionality testing

### Test Locations
- Model tests: `*/tests/tests_models/`
- API tests: `*/tests/tests_api/`
- Admin tests: `*/tests/tests_admin/`
- Factory classes: `*/tests/factory/`

### Coverage Requirements
- Maintain test coverage above 80%
- All new features require corresponding tests
- Use factory-boy for consistent test data generation

## Security Considerations

- JWT-based authentication for API access
- CORS configuration for frontend integration
- Environment-based secret management
- Database connection security via environment variables
- Sentry integration for error monitoring and security event tracking
