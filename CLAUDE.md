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
docker-compose exec web python manage.py sync_go365   # Sync Go365 data
docker-compose logs -f web              # View logs
```

## Claude Code Skills

Specialized skills for provider integration and debugging:

- **`/debug-provider-sync`** - Diagnose why sync commands don't save data to database
- **`/integrate-provider`** - Add new tour provider by analyzing API and generating code
- **`/validate-models`** - Validate models before sync to prevent constraint violations

See [`.claude/README.md`](.claude/README.md) for detailed skill documentation.

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

### Management Command Best Practices

**CRITICAL: Safe Dictionary Access for Optional Arguments**

When writing Django management commands, ALWAYS use `.get()` method for accessing optional arguments in the `handle()` method:

```python
def handle(self, *args, **options):
    # ✅ GOOD - Safe access, works in all contexts
    tour_id = options.get('tour_id')
    if tour_id:
        tours = [service.get_program_tour_details(tour_id)]

    # ❌ BAD - Raises KeyError when called from Django Admin
    if options['tour_id']:
        tours = [service.get_program_tour_details(options['tour_id'])]
```

**Why**: When commands are called from Django Admin's "Sync Now" button or programmatically, optional arguments may not exist in the `options` dict. Direct dictionary access `options['key']` raises `KeyError`, while `options.get('key')` safely returns `None`.

**Contexts where commands are called**:
- CLI: `python manage.py sync_provider` - All arguments present (with defaults)
- Django Admin: `cmd.handle()` - Optional arguments may NOT exist in dict
- Programmatic: `command.handle()` - Same as Admin
- Celery Tasks: May not pass all arguments

**Real-world fix**: CheckIn Group sync command (2026-01-16)
- Issue: `KeyError: 'tour_id'` when syncing from Django Admin
- Fix: Changed `options['tour_id']` to `options.get('tour_id')` on lines 54, 66, and 94

**Before deploying management commands, verify**:
- [ ] All optional arguments accessed via `.get()`
- [ ] Command works from CLI with no arguments
- [ ] Command works from Django Admin "Sync Now" button
- [ ] No direct dictionary access like `options['key']` for optional args

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

**Go365** (API-based):
- Command: `python manage.py sync_go365`
- Auth: API Key (x-api-key header only)
- API Endpoint: `https://api.kaikongservice.com`
- Data: Tours, countries, periods, pricing, multi-language support (Thai, English, Chinese)
- Features: Search, pagination, detailed tour information
- Commands:
  - `python manage.py sync_go365 --test-connection` (test API connectivity)
  - `python manage.py sync_go365 --tours-only --limit 10` (sync 10 tours)
  - `python manage.py sync_go365 --countries-only` (sync countries)
  - `python manage.py sync_go365 --search "Hong Kong"` (search tours)

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
1. **Check existing adapters first** - If the new provider has the same data structure as an existing provider, reuse the existing adapter
2. **Create new adapter only if needed** - Only create a new adapter class implementing `BaseAPIService` if the data structure differs
3. Implement vendor-specific auth and data mapping
4. Create management command for data sync
5. Configure provider in Django Admin
6. Set up Celery Beat scheduled tasks

**Adapter reuse principle**: Create adapters to map data from providers with different data structures. If a new provider has the same data structure as an existing provider, reuse the existing adapter instead of creating a new one.

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
