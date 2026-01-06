# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is the Cost Module - a FastAPI-based microservice within the Meest Logistics platform that handles invoice processing, cost calculation, cost distribution, pricing specifications, and financial data management for logistics operations.

## Repository Structure

### Core Application Structure
- **mwl_cost/**: Main application package
  - **api/**: FastAPI REST API layer (routes, middlewares, events)
  - **core/**: Core business logic (models, services, DTOs, helpers)
  - **engine/**: Cost calculation engine and specification processing
  - **migrations/**: Alembic database migrations

### Main Application Modules

#### API Layer (`mwl_cost/api/`)
- **server.py**: FastAPI application initialization and lifespan
- **router.py**: API router composition
- **celery.py**: Celery task queue setup
- **routes/**: REST API endpoint handlers
  - `health.py` - Health check endpoints
  - `invoice.py` - Invoice processing
  - `cost_item.py` - Cost item CRUD operations
  - `cost_type.py` - Cost type management
  - `specification.py` - Specification file handling
  - `parcels.py` - Parcel management
  - `distribution_policy.py` - Distribution policy operations
  - `calculating_rule.py` - Calculation rule management
  - `exchange_table.py` - Currency exchange rates
  - `vendor.py` - Vendor management
  - `files.py` - File operations & downloads
  - `note.py` - Notes/audit logging
- **middlewares/**: Authentication and request processing
- **events/**: AMQP consumers and event-triggered tasks

#### Core Layer (`mwl_cost/core/`)
- **config.py**: Pydantic settings and environment configuration
- **db/**: SQLAlchemy ORM models (23 models)
  - `invoice.py` - Invoice domain model
  - `cost_item.py` - Cost item line items
  - `cost_type.py` - Cost categorization
  - `cost_object.py` - Cost distribution targets
  - `distribution_policy.py` - Cost distribution rules
  - `calculating_rule.py` - Calculation logic definitions
  - `specification.py` - Specification document model
  - `exchange_table.py` - Currency exchange rates
  - `vendor.py` - Vendor information
  - `mwl_parcel.py` - Parcel entity
  - `mwl_manifest.py` - Manifest/shipment grouping
  - `note.py` - Audit notes/comments
- **dto/**: Data Transfer Objects (Pydantic models)
- **services/**: Business logic organized by domain (14 service modules)
- **helpers/**: Utility functions (S3, API, DataFrame utilities)
- **enums/**: Type-safe enumerations (25+ enums)
- **filters/**: Query filtering logic
- **tasks/**: Celery async task definitions

#### Engine (`mwl_cost/engine/`)
- **engine.py**: Main cost calculation orchestration
- **cost_items_creation.py**: Cost item generation logic
- **reading_specification.py**: Specification file parsing
- **proxy_mapping.py**: Entity mapping and proxies
- **specification_converter/**: Excel/CSV conversion utilities

### Supporting Infrastructure
- **deployment/**: Docker and deployment configuration
  - `docker/Dockerfile` - Production Docker image
  - `docker/entrypoint.sh` - Container entrypoint
  - `dev/`, `stage/`, `prod/` - Environment-specific scripts
- **docs/**: Documentation and reference data

## Technology Stack

### Core Framework & Database
- **FastAPI** (0.112+) - Modern async REST API framework
- **Python 3.12** - Runtime environment
- **Uvicorn** (0.30+) - ASGI server
- **PostgreSQL 16** - Primary database
- **SQLAlchemy 2.0** - Async ORM with type hints
- **Alembic** - Database migration tool

### Key Dependencies & Libraries
- **Pydantic 2.x** - Data validation and settings
- **Celery 5.3+** - Distributed task queue
- **boto3** - AWS SDK for S3 operations
- **Pandas 2.x** - Data manipulation and Excel processing
- **openpyxl, xlrd, xlwt, xlsxwriter** - Excel file handling
- **httpx** (0.27+) - Async HTTP client
- **sentry-sdk** (2.9+) - Error monitoring
- **loguru** - Structured logging
- **tenacity** - Retry logic

### Internal Libraries (Sources in `external-sources/`)
These libraries have no public documentation. Source code is available locally for reference.

- **sqlalchemy-service** (v1.0.6) - Smartive SQLAlchemy wrapper
  - Source: `external-sources/sqlalchemy_service-1.0.6-py3-none-any/sqlalchemy_service/`
  - Provides: `BaseModel`, `session_manager`, `ComboService`, `FilteringService`, `PaginatingService`, `OrderingService`, `DBManager`, `Filter`, `BaseModelDTO`, `AsyncSQLAlchemyFactory`, pagination schemes

- **amqp-service** (v0.1.3) - Smartive AMQP wrapper
  - Source: `external-sources/amqp_service-0.1.3-py3-none-any/amqp_service/`
  - Provides: `Consumer`, `TaskRouter`, `Task`, `declare_amqp`, `ExchangeOptions`, `QueueOptions`, `RejectMessage`

- **aio-pika** (v9.5.4) - Async AMQP client for RabbitMQ (less mainstream, source included)
  - Source: `external-sources/aio_pika-9.5.4-py3-none-any/aio_pika/`
  - Provides: `connect_robust`, `Channel`, `AbstractRobustConnection`, `ExchangeType`

### Development & Testing
- **pytest 8.x** - Testing framework
- **pytest-asyncio** - Async test support
- **factory-boy** - Test data generation
- **coverage** - Test coverage reporting
- **mypy** - Static type checking with SQLAlchemy plugin
- **ruff** - Code formatting and linting
- **tox** - Testing environment management

## Architecture Overview

### Core Business Logic
The service manages the complete cost calculation lifecycle:
1. **Specification Processing** (`engine/reading_specification.py`) - Parse uploaded specification files
2. **Invoice Management** (`core/services/invoice/`) - Invoice creation and processing
3. **Cost Calculation** (`engine/engine.py`) - Core calculation engine
4. **Distribution Policies** (`core/services/distribution_policy/`) - Define how costs are allocated
5. **Cost Item Generation** (`engine/cost_items_creation.py`) - Generate cost items based on rules
6. **Currency Exchange** (`core/services/exchange/`) - Handle multi-currency operations

### Key Data Flow
1. **Specifications** are uploaded and processed to extract cost data
2. **Invoices** are created with distribution policies that define how costs are allocated
3. **Engine** processes invoices by reading specifications and calculating cost distributions
4. **Cost Items** are generated based on distribution rules and assigned to cost objects (parcels, manifests)

### API Structure
- **Health Endpoints** - `/health/`, `/readiness/`
- **Invoice API** - Invoice CRUD and processing
- **Specification API** - File upload and management
- **Cost Item API** - Cost item operations
- **Distribution Policy API** - Policy management
- **Exchange API** - Currency exchange rates
- **Vendor API** - Vendor management
- **Files API** - File downloads

### Database Architecture
- **Invoice System**: Invoice → Cost Items → Cost Objects hierarchy
- **Specification Processing**: Specification → Mapping → Parsed Data
- **Distribution Rules**: Distribution Policy → Calculating Rules
- **Audit Trail**: Notes for operation logging

## Development Commands

**IMPORTANT: This project uses Poetry for dependency management. All commands should be run using `poetry run` prefix or within a Poetry shell.**

### Environment Setup
```bash
# Install dependencies (including dev dependencies)
poetry install

# Activate virtual environment (optional - or use 'poetry run' prefix)
poetry shell

# Show virtual environment information
poetry env info
```

### Testing and Code Quality
```bash
# Run full test suite with linting and type checking (uses tox configuration)
poetry run tox

# Run specific tox environment
poetry run tox -e standard    # Full test suite with formatting, linting, and coverage
poetry run tox -e tests       # Tests with linting and type checking only
poetry run tox -e coverage    # Tests with HTML coverage report

# Run tests only (pytest)
poetry run pytest

# Run tests for specific module
poetry run pytest mwl_cost/core/tests/tests_services/

# Code formatting with ruff
poetry run ruff format ./

# Code linting with auto-fix
poetry run ruff check ./ --fix

# Code linting without fixes (check only)
poetry run ruff check ./

# Type checking with mypy
poetry run mypy ./

# Test coverage
poetry run coverage run -m pytest
poetry run coverage report

# Test coverage with HTML report
poetry run coverage run -m pytest
poetry run coverage html -d coverage_html_report
```

### Development Server
```bash
# Start development server with auto-reload
poetry run uvicorn mwl_cost.api.server:application --host localhost --port 9300 --reload

# Start production server (4 workers)
poetry run uvicorn mwl_cost.api.server:application --host 0.0.0.0 --port 9300 --workers 4
```

### Database Operations
```bash
# Create new migration (auto-generate from model changes)
poetry run alembic revision --autogenerate -m "description of changes"

# Apply all pending migrations
poetry run alembic upgrade head

# Downgrade one migration
poetry run alembic downgrade -1

# Show migration history
poetry run alembic history

# Show current migration
poetry run alembic current
```

### Celery (Async Tasks)
```bash
# Start Celery worker
poetry run celery -A mwl_cost.api.celery worker -l info
```

### Docker Development
```bash
# Start local development services (PostgreSQL, LocalStack, RabbitMQ)
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Reset database (recreate with fresh volumes)
docker-compose down -v && docker-compose up -d
```

### Running Tests with Docker
The tests require the following environment variables to connect to docker services:

```bash
# Source .env and set required test environment variables
source .env && export TESTING=1 POSTGRES_HOST=localhost:5433 POSTGRES_HOST_RO=localhost:5433 AWS_REGION=us-east-1

# Run all tests
poetry run pytest

# Run specific test module
poetry run pytest mwl_cost/engine/tests/

# Run with verbose output
poetry run pytest -v
```

**Note:** The docker-compose maps PostgreSQL to port 5433 (not 5432), so `POSTGRES_HOST=localhost:5433` is required when running tests locally with docker.

## Configuration

### Environment Variables
The application uses environment-based configuration via `.env` files:

**Database:**
- `POSTGRES_USER` - Database user
- `POSTGRES_PASSWORD` - Database password
- `POSTGRES_HOST` - Database host
- `POSTGRES_HOST_RO` - Read-only replica host
- `POSTGRES_DB` - Database name

**AWS/S3:**
- `S3_URL` - S3 endpoint (LocalStack for dev)
- `AWS_KEY` - AWS access key
- `AWS_SECRET` - AWS secret key
- `S3_STORAGE_BUCKET` - File storage bucket
- `S3_CONFIG_BUCKET` - Configuration bucket

**Message Queue:**
- `AMQP_URL` - RabbitMQ connection URL
- `CELERY_BROKER_URL` - Celery broker URL

**External Services:**
- `MWL_USER_AUTH_BASE_URL` - Auth service URL

**Application:**
- `DEBUG` - Debug mode
- `ENVIRONMENT` - Environment name (local, dev, stage, prod)
- `SYSTEM_CURRENCY` - Default currency (default: "eur")

### Configuration Loading
- **Local development**: Uses `.env` file
- **Non-local environments**: Configuration downloaded from S3 at startup
  - Key: `cost/{ENVIRONMENT}.env`

### Key Configuration Files
- `mwl_cost/core/config.py` - Pydantic settings definition
- `alembic.ini` - Migration configuration
- `test.env` - Testing environment variables

## Important Code References

### Core Models
- Invoice entity: `mwl_cost/core/db/invoice.py`
- Cost item: `mwl_cost/core/db/cost_item.py`
- Distribution policy: `mwl_cost/core/db/distribution_policy.py`
- Calculating rule: `mwl_cost/core/db/calculating_rule.py`
- Specification: `mwl_cost/core/db/specification.py`

### API Endpoints
- Router composition: `mwl_cost/api/router.py`
- Invoice routes: `mwl_cost/api/routes/invoice.py`
- Specification routes: `mwl_cost/api/routes/specification.py`

### Business Logic
- Cost calculation engine: `mwl_cost/engine/engine.py`
- Specification parsing: `mwl_cost/engine/reading_specification.py`
- Cost item generation: `mwl_cost/engine/cost_items_creation.py`

### Services
- Invoice service: `mwl_cost/core/services/invoice/`
- Distribution policy service: `mwl_cost/core/services/distribution_policy/`
- Specification service: `mwl_cost/core/services/specification/`

## Testing Strategy

### Test Structure
- **API Tests**: `mwl_cost/api/tests/tests_api/` - Endpoint testing
- **Service Tests**: `mwl_cost/core/tests/tests_services/` - Business logic testing
- **Model Tests**: `mwl_cost/core/tests/tests_db/` - Database model testing
- **Engine Tests**: `mwl_cost/engine/tests/` - Calculation engine testing
- **DTO Tests**: `mwl_cost/core/tests/tests_dto/` - Data validation testing
- **Factory Classes**: `mwl_cost/core/tests/factory/` - Test data factories (26+)

### Test Configuration
- Session-scoped database with test data reset between tests
- Async test support via pytest-asyncio
- Factory-boy for realistic test data generation

### Coverage Requirements
- Maintain test coverage above 80%
- All new features require corresponding tests
- Use factory-boy for consistent test data generation

## Code Quality Standards

### Type Hints
- Strict mypy enforcement (`disallow_untyped_defs = true`)
- SQLAlchemy mypy plugin enabled

### Linting
- Ruff with rules: E, F, UP, B, SIM, I
- Line length: 120 characters
- Target Python version: 3.12

### Patterns
- Pydantic DTOs for request/response validation
- SQLAlchemy async ORM patterns
- Service layer for business logic
- Factory pattern for test data

## Security Considerations

- HTTP Bearer token authentication
- Custom auth middleware for user context
- Environment-based secret management
- S3-based configuration for non-local environments
- Sentry integration for error monitoring
