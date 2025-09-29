# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Local Development
```bash
# Activate virtual environment
source venv/bin/activate

# Run migrations and start development server
python manage.py makemigrations
python manage.py migrate
python manage.py runserver

# Create superuser
python manage.py createsuperuser

# Create new Django app
python manage.py startapp [appname]
```

### Docker Development
```bash
# Start local development with Docker
docker-compose -f docker-compose.yml up

# Create superuser in Docker environment
docker-compose -f docker-compose.yml run --rm web sh -c "python manage.py createsuperuser"

# View Docker logs
docker-compose -f docker-compose.yml logs

# Production mode (with RDS)
docker-compose -f docker-compose-rds.yml up
```

### Data Synchronization
```bash
# Sync all data from active wholesalers
python manage.py sync_zego_data

# Sync specific wholesaler
python manage.py sync_zego_data --wholesaler "WholesalerName"

# Sync only countries or tours
python manage.py sync_zego_data --countries-only
python manage.py sync_zego_data --tours-only

# Check for updates before syncing
python manage.py sync_zego_data --check-updates
```

## Project Architecture

### Core Structure
- **Core/**: Django project configuration with settings, URLs, Celery setup
- **Accounts/**: Custom user authentication using email-based login
- **tours/**: Travel tour management with categories, types, locations, and flash sales
- **wholesale/**: Wholesale travel provider integration with external API synchronization
- **management/**: Custom Django management commands for data operations

### Database Configuration
The project uses conditional database settings:
- **Docker mode** (`DOCKER=true`): PostgreSQL with configurable credentials
- **Local development**: SQLite3 database
- Configuration managed through environment variables with `python-decouple`

### Key Models and Relationships

#### Tours App
- **Tour**: Main tour entity with operator, locations, categories, and travel dates
- **TravelDate**: Specific departure dates with pricing and availability
- **FlashSale**: Time-based discount system for travel dates
- **Location, Country, Airline, Operator**: Supporting entities for tour organization

#### Wholesale App
- **Wholesaler**: External API providers (e.g., Zego) with authentication tokens
- **ProgramTour**: Synchronized tour programs from wholesalers with detailed itineraries
- **Period**: Specific tour periods with pricing, availability, and booking status
- **Flight, Itinerary**: Detailed tour components including flight schedules and daily activities
- **Location**: Hierarchical location structure linked to countries and wholesalers

### Celery Configuration
- **Redis**: Used as message broker and result backend
- **Celery Beat**: Scheduled task management using django-celery-beat
- **Workers**: Background task processing for data synchronization
- Environment-aware Redis connection (Docker vs local)

### API Integration
- RESTful endpoints for tour management and wholesale data
- External API synchronization with wholesaler systems
- Custom management commands for bulk data operations
- Django REST Framework for API serialization

### Environment Configuration
Key environment variables:
- `DOCKER`: Boolean flag for deployment mode
- `DB_*`: Database connection parameters
- `SECRET_KEY`, `DEBUG`: Standard Django settings
- `CELERY_BROKER_URL`, `CACHE_LOCATION_URL`: Redis configuration
- `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`: Security settings

### Data Synchronization Pattern
The wholesale app implements a comprehensive data sync service that:
1. Fetches data from external wholesaler APIs
2. Synchronizes countries, locations, and program tours
3. Maintains relationship integrity between entities
4. Provides status tracking and error handling
5. Supports incremental updates and full synchronization

### Custom User Model
Uses `Accounts.Account` as the custom user model for email-based authentication instead of username-based login.