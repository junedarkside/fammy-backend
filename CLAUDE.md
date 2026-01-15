# CLAUDE.md

AI assistant instructions for this B2B Travel Platform codebase.

> **Comprehensive documentation**: [`docs/`](docs/) - All project documentation lives here
> **Project overview**: [`readme.md`](readme.md) - Quick project introduction

## Quick Reference

**What this project is**: B2B platform connecting Thai travel agencies with wholesale tour operators via automated data synchronization.

**Key technologies**: Django, PostgreSQL, Redis, Celery, Docker Compose

**Core apps**:
- `Core/` - Project config, settings, URLs, Celery
- `Accounts/` - Email-based user authentication
- `tours/` - Tour management (categories, locations, dates)
- `wholesale/` - Provider integration and API synchronization
- `management/` - Custom Django management commands

**Quick start**:
```bash
docker-compose up -d                    # Start all services
docker-compose exec web python manage.py sync_zego    # Sync Zego data
docker-compose exec web python manage.py sync_unique_inter  # Sync Unique Inter
docker-compose exec web python manage.py sync_checkingroup  # Sync CheckIn Group
docker-compose logs -f web              # View logs
```

## Development Policies

### Code Consistency (MANDATORY)

1. **ALWAYS search before writing** - Find existing patterns to copy
2. **Match existing style exactly** - Naming, formatting, structure
3. **Reuse existing code** - Don't reinvent utilities/helpers
4. **Keep it simple** - YAGNI principle, no over-engineering
5. **Modular over monolithic** - Small, focused functions

**Naming conventions**:
- Classes: `CapitalizedWords`
- Functions/variables: `lowercase_with_underscores`
- Constants: `UPPERCASE_WITH_UNDERSCORES`
- Private: `_leading_underscore`

**Before writing code checklist**:
- [ ] Searched codebase for similar implementations?
- [ ] Found existing patterns to follow?
- [ ] Matched existing naming conventions?
- [ ] Used existing utilities/helpers?
- [ ] Followed existing file structure?

### Code Quality Standards

**Import organization**:
```python
# 1. Standard library
import os
from datetime import datetime

# 2. Third-party
from django.db import models
from rest_framework import serializers

# 3. Local
from .models import Tour
from .services import TourService
```

**File structure** (Django apps):
```
models.py         # Database models
serializers.py    # DRF serializers
views.py          # API views (ViewSets)
urls.py           # URL routing
admin.py          # Django admin config
services.py       # Business logic (complex operations)
utils.py          # Helper functions
```

**Required practices**:
- Type hints on all function signatures
- Google-style docstrings for public methods
- Max line length: 100 characters
- Validate syntax: `python manage.py check`

### Safety Requirements

- **Backward compatibility** - Don't break existing functionality
- **Production safety** - Test before deploying
- **Migration safety** - Use Django migrations properly
- **Error handling** - Handle edge cases and validation

## Provider Integration

### Current Providers

**Zego** (API-based):
- Command: `python manage.py sync_zego`
- Auth: API token
- Data: Tours, countries, pricing, availability

**Unique Inter** (API-based, departure-centric):
- Commands:
  - `python manage.py sync_unique_inter_categories` (discover categories)
  - `python manage.py sync_unique_inter` (full sync)
  - `python manage.py sync_unique_inter --fetch-only` (fetch raw data)
  - `python manage.py sync_unique_inter --process-only` (process raw data)
- Auth: Email-based
- Categories: 59 (Europe), 60 (Russia), 61 (UK), 62 (HK), 63 (Promo), 64 (Vietnam)

**CheckIn Group** (API-based, Thai B2B wholesaler):
- Command: `python manage.py sync_checkingroup`
- Auth: None (public API)
- Data: Tours, periods, complete pricing, availability, commissions
- Data Quality: 85/100 (high quality)

**Go365** (Manual entry):
- Command: `python manage.py sync_go365`
- Data entry via Django Admin or CSV import

### Provider Adapter Pattern

```python
class BaseAPIService:
    def fetch_countries()     # Fetch country/destination data
    def fetch_tours()         # Fetch tour packages
    def fetch_availability()  # Fetch real-time availability
    def authenticate()        # Handle vendor authentication

# Vendor implementations: ZegoAdapter, UniqueInterAdapter, CheckInGroupAdapter, Go365Adapter
```

**Adding new vendors**:
1. Create adapter class implementing `BaseAPIService`
2. Implement vendor-specific auth and data mapping
3. Create management command for data sync
4. Configure provider in Django Admin
5. Set up Celery Beat scheduled tasks

### Data Normalization

All providers normalize to:
- **Countries**: ISO standard codes
- **Pricing**: THB (Thai Baht)
- **Dates**: YYYY-MM-DD format
- **Categories**: Internal category system
- **Commissions**: Standard agent/sales structure

## Docker Development

### Services

| Service | Purpose | Ports |
|---------|---------|-------|
| db | PostgreSQL 13 | 5432 (internal) |
| web | Django app | 8000 |
| redis | Message broker | 6379 (internal) |
| celery-worker | Background tasks | - |
| celery-beat | Scheduled tasks | - |

### Common Commands

```bash
# Start/stop
docker-compose up -d                    # Start all services
docker-compose down                     # Stop services
docker-compose down -v                  # Stop and delete database

# Management
docker-compose exec web python manage.py createsuperuser
docker-compose exec web python manage.py makemigrations
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py shell

# Logs
docker-compose logs -f                  # All services
docker-compose logs -f web              # Specific service
docker-compose logs --tail=100 web      # Last 100 lines

# Database
docker-compose exec db psql -U myuser -d mydatabase
docker-compose exec db pg_dump -U myuser mydatabase > backup.sql
docker-compose exec -T db psql -U myuser mydatabase < backup.sql

# Rebuild
docker-compose up --build               # Rebuild containers
```

### Troubleshooting

**Database connection**: Ensure `DB_HOST=db` in `.env` (not localhost)

**Code not reflecting**: Check volume mount with `docker-compose exec web ls -la /app`

**Celery issues**:
```bash
docker-compose restart celery-worker
docker-compose logs -f celery-worker
```

**Complete reset** (last resort):
```bash
docker-compose down -v
docker-compose up
```

## Data Quality Management

### Country Validation (Unique Inter)

Inconsistent API data may extract invalid country names ("Christmas", "Winter" vs actual countries).

**Audit**:
```bash
docker-compose exec web python manage.py audit_tour_countries
```

**Fix**: Manually update via Django Admin or re-process with improved extraction

**Admin indicators**:
- ✓ Green: Valid country (has Country FK)
- ⚠ Orange: Needs review (extracted but no FK)
- ✗ Red: Missing data

## Environment Variables

**Required** (.env file):
```bash
DOCKER=true                          # Enable PostgreSQL
SECRET_KEY=your-secret-key
DB_HOST=db
DB_NAME=mydatabase
DB_USER=myuser
DB_PASS=mypassword
```

**Optional**:
```bash
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
WS_API_ENDPOINT_01_URL=https://www.zegoapi.com/v1.5
WS_API_ENDPOINT_01_TOKEN=your-token
```

## Documentation Structure

All documentation in [`docs/`](docs/):

- `docs/README.md` - Documentation index
- `docs/getting-started/` - Quick start, project overview
- `docs/development/` - Commands reference, policies
- `docs/api/` - API endpoints documentation
- `docs/provider-integration/` - Provider adapter guides
- `docs/architecture/` - System design, database
- `docs/reference/` - Travel industry guide

**Before creating docs**:
1. Search existing docs with `grep -r "keyword" docs/`
2. Update existing docs rather than create duplicates
3. Add to `docs/README.md` index
4. Use consistent formatting

**DO NOT create documentation in project root** - use `docs/` directory.

## Key Models

**Tours app**: Tour, TravelDate, FlashSale, Location, Country, Airline, Operator

**Wholesale app**: Provider, ProviderCategory, RawVendorData, ProgramTour, Period, Flight, Itinerary, Country, Location

## Custom User Model

Uses `Accounts.Account` - email-based authentication (not username).

## Architecture

```
Tour Operators (APIs)
    ↓
Provider Adapters (BaseAPIService implementations)
    ↓
Django Models (ProgramTour, Period, Country, Provider)
    ↓
Travel Agencies (Thai B2B Portal)
```

**Provider Adapter Benefits**:
- Easy addition of new operators
- Consistent data processing
- Isolated provider logic
- Simplified testing
