# Project Brief

## Project Goals

- Connect Thai travel agencies with wholesale tour operators through automated data synchronization
- Normalize tour data from multiple providers into a unified database structure
- Enable B2B customers to browse and book tours from multiple suppliers
- Serve Thai customers with localized tour packages and services

## Core Requirements

- **Multi-Provider Integration**: Connect with multiple wholesale tour operator APIs (Zego, Unique Inter, Go365)
- **Data Normalization**: Standardize data from various API formats into unified models
- **Provider Adapter Pattern**: Abstract vendor-specific implementations behind common interface
- **Django Admin Interface**: Staff can manage tours, providers, and override automated data
- **REST API**: Public API endpoints for tours, providers, and program tours
- **Celery Task Queue**: Background processing for data synchronization
- **Docker Development**: All development done via Docker Compose

## Project Scope

**In Scope:**
- B2B travel platform for Thai market
- Wholesale tour operator aggregation
- Automated data synchronization from multiple providers
- Django admin interface for manual management
- REST API for tour data access
- Provider-specific adapter implementations

**Out of Scope:**
- Direct B2C consumer booking (this is B2B only)
- Payment processing
- Frontend UI layer (backend only)
- Real-time availability from all providers

## Architecture Pattern

**Monolithic Django Application** with modular apps:
- `Core/` - Project configuration, URLs, Celery setup
- `Accounts/` - Custom user authentication (email-based)
- `tours/` - Internal tour management
- `wholesale/` - Provider integration and data sync
- `management/` - Custom Django management commands

## Provider Integrations

**Currently Integrated:**
- **Zego Travel** - API-based with token authentication
- **Unique Inter Wholesale** - API-based with email authentication, departure-centric data
- **Go365** - Manual entry/CSV import (no API)

**Provider Adapter Factory:**
```python
class APIServiceFactory:
    @staticmethod
    def create_service(provider) -> BaseAPIService:
        # Returns provider-specific service implementation
```

## Data Sync Strategy

- **Two-Stage Sync** (Unique Inter): Fetch raw data → Process and normalize
- **Bulk Operations**: Batch database writes for performance
- **Scheduled Tasks**: Celery Beat for periodic updates
- **Manual Triggers**: API endpoints and management commands for on-demand sync

## Documentation Structure

All project documentation is organized in `docs/` directory:
- `docs/README.md` - Documentation index
- `docs/getting-started/` - Quick start, project overview, developer guide
- `docs/development/` - Commands reference, development policies
- `docs/api/` - API overview and endpoints
- `docs/provider-integration/` - Provider adapter guides
- `docs/architecture/` - System design, database, data consistency
- `docs/reference/` - Travel industry guide, admin improvements
