# System Patterns

## System Architecture

**Monolithic Django Application** with modular app structure:

```
TravelApp/BackEnd/
├── Core/                 # Django project configuration
│   ├── settings/         # Environment-specific settings
│   ├── urls.py          # Main URL configuration
│   └── wsgi.py          # WSGI application
├── Accounts/            # Custom user authentication (email-based)
├── tours/               # Internal tour management
├── wholesale/           # Provider integration & data sync
└── management/          # Custom Django management commands
```

**Docker Services:**
- `db` - PostgreSQL 13-alpine
- `web` - Django application (Python 3.10-alpine)
- `redis` - Message broker & cache
- `celery-worker` - Background task processor
- `celery-beat` - Scheduled task manager

## Key Technical Decisions

**Backend Framework:**
- Django for ORM, admin, and project structure
- Django REST Framework for API endpoints
- Celery + Redis for async tasks
- PostgreSQL for relational data

**Development Environment:**
- Docker Compose for all services
- PostgreSQL (no SQLite support)
- Live code reloading via volume mounts
- Environment-based configuration

**Provider Integration:**
- Provider adapter pattern for API abstraction
- Two-stage sync for complex data (fetch → process)
- Bulk database operations for performance
- Django admin for manual overrides

## Design Patterns in Use

**Provider Adapter Pattern:**
```python
class BaseAPIService:
    def fetch_countries()           # Abstract method
    def fetch_tours()               # Abstract method
    def fetch_availability()        # Abstract method
    def authenticate()              # Abstract method

class ZegoAPIService(BaseAPIService):
    # Zego-specific implementation

class UniqueInterAPIService(BaseAPIService):
    # Unique Inter-specific implementation
```

**Factory Pattern:**
```python
class APIServiceFactory:
    @staticmethod
    def create_service(provider) -> BaseAPIService:
        # Returns provider-specific service
```

**Service Layer Pattern:**
- Business logic in service classes
- Views handle HTTP concerns only
- Models handle data persistence only

**Repository Pattern (Django ORM):**
- Models abstract database access
- Manager classes for complex queries
- QuerySets for data retrieval

## Component Relationships

**Data Flow:**
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Tour Operator │───▶│  Provider Adapter │───▶│   Travel Agency  │
│     APIs        │    │     Services     │    │   B2B Portal    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │   Django Models  │
                    │ • ProgramTour    │
                    │ • Period         │
                    │ • Country        │
                    │ • Provider       │
                    └──────────────────┘
```

**API Layer:**
- Django REST Framework ViewSets
- Serializers for data validation
- Custom pagination for enhanced metadata

**Task Queue:**
- Celery Beat schedules periodic syncs
- Celery Worker processes async tasks
- Redis as message broker

## Critical Implementation Paths

**Provider Data Sync:**
1. Provider configured in Django Admin
2. APIServiceFactory creates provider-specific service
3. Service fetches data from external API
4. Data normalized to unified models
5. Bulk database operations for performance
6. Django admin for manual review/override

**API Request Flow:**
1. Request hits Django URLs
2. Routed to appropriate ViewSet
3. Serializer validates data
4. Business logic in service layer
5. Database operations via ORM
6. Response serialized and returned

**Celery Task Flow:**
1. Celery Beat triggers scheduled task
2. Task queued in Redis
3. Celery Worker picks up task
4. Provider service invoked
5. Data synced to database
6. Result stored/returned

## Data Model Patterns

**Provider Abstraction:**
- `Provider` model stores credentials
- `ProviderCategory` for provider-specific categories
- `RawVendorData` preserves original API responses
- `ProgramTour` / `Period` for normalized tour data

**Tour Management:**
- `Tour` model for internal tours
- `TravelDate` for specific departures
- `FlashSale` for time-based discounts
- `Country`, `Location`, `Airline`, `Operator` relationships

**Custom User Model:**
- `Accounts.Account` for email-based authentication
- Extends Django's AbstractBaseUser
- No username field (email only)

## URL Patterns

**API Endpoints:**
- `/api/healthcheck/` - Health check
- `/api/tours/` - Tour CRUD operations
- `/api/wholesale/providers/` - Provider management
- `/api/wholesale/call-external-api/{company}/` - API proxy
- `/api/wholesale/program-tours/` - Provider tours

**Admin Interface:**
- `/admin/` - Django admin
- Provider management
- Tour management
- Data quality monitoring

## Configuration Patterns

**Environment-Based Settings:**
- `Core/settings/` directory
- Separate files for base, development, production
- `python-decouple` for environment variables
- `DOCKER=true` triggers PostgreSQL mode

**Provider Configuration:**
- Stored in `Provider` model (database)
- `extra` JSON field for provider-specific settings
- Managed via Django Admin
- No code changes for new providers
