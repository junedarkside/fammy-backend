# Tech Context

## Technologies Used

**Backend:**
- Django 3.x - Web framework
- Python 3.10 - Programming language
- Django REST Framework - API layer
- Celery - Async task queue
- Redis - Message broker & cache

**Database:**
- PostgreSQL 13 - Primary database (Docker)
- Django ORM - Database abstraction

**API Integration:**
- REST APIs - Provider communication
- Requests library - HTTP client
- Provider-specific adapters

**Development:**
- Docker Compose - Container orchestration
- Python venv - Virtual environment
- Git - Version control

## Development Setup

**Docker Compose (Primary):**
```bash
docker-compose up              # Start all services
docker-compose exec web python manage.py <command>
docker-compose logs -f <service>
```

**Key Containers:**
- `web` - Django application (port 8000)
- `db` - PostgreSQL (port 5432)
- `redis` - Redis (port 6379)
- `celery-worker` - Background tasks
- `celery-beat` - Scheduled tasks

**Environment Variables:**
- `.env` file for configuration
- `DOCKER=true` required for PostgreSQL
- `python-decouple` for settings management

## Technical Constraints

**Infrastructure:**
- Docker-based development only (no local SQLite)
- PostgreSQL required (no other databases)
- Celery + Redis required for async tasks

**Provider APIs:**
- Different auth methods per provider
- Rate limits vary by provider
- Some providers have no API (manual entry)
- API documentation may be outdated

**Data Constraints:**
- Provider data quality varies
- Inconsistent field naming
- Some data only in PDFs (not API)
- Country/location validation needed

## Dependencies

**Core Django:**
- django - Web framework
- djangorestframework - API layer
- django-celery-beat - Scheduled tasks
- django-celery-results - Task result backend
- python-decouple - Configuration

**Celery & Redis:**
- celery - Task queue
- redis - Python Redis client
- kombu - Celery messaging

**API & HTTP:**
- requests - HTTP client
- urllib3 - HTTP library

**Database:**
- psycopg2-binary - PostgreSQL adapter
- Django ORM (built-in)

## Tool Usage Patterns

**Docker Compose Commands:**
```bash
# Service management
docker-compose up -d              # Start services
docker-compose down               # Stop services
docker-compose restart <service>  # Restart service

# Django commands
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser
docker-compose exec web python manage.py shell

# Logs
docker-compose logs -f <service>  # Follow logs
docker-compose logs --tail=100 <service>  # Last 100 lines
```

**Django Management Commands:**
```bash
# Provider sync
python manage.py sync_zego
python manage.py sync_unique_inter
python manage.py sync_go365

# Data quality
python manage.py audit_tour_countries

# Standard Django
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py shell
```

**Celery Operations:**
```bash
# Check active tasks
docker-compose exec web python manage.py shell
>>> from celery import current_app
>>> current_app.control.inspect().active()

# Restart workers
docker-compose restart celery-worker
docker-compose restart celery-beat
```

## File Structure Conventions

**Django Apps:**
- Each app has models.py, views.py, urls.py, serializers.py
- Management commands in `management/commands/`
- Templates (if any) in `templates/` directory

**Provider Adapters:**
- Located in `wholesale/` app
- Service classes in `services.py`
- Factory pattern in `api_service.py`
- Management commands for data sync

**Configuration:**
- `Core/settings/` for environment-specific settings
- `.env` for sensitive data
- `docker-compose.yml` for service definitions

## Code Style Guidelines

**Python:**
- PEP 8 compliance
- Type hints for functions
- Docstrings for public methods
- Maximum line length: 100 characters

**Django:**
- Use Django conventions
- Model names: CapitalizedWords
- View names: camelCase
- URL names: lowercase_with_underscores

**API:**
- RESTful endpoints
- Noun-based URLs (/tours/, /providers/)
- HTTP methods for actions (GET, POST, PUT, DELETE)
- kebab-case for URL parameters

## Performance Considerations

**Database:**
- Use `select_related()` for ForeignKeys
- Use `prefetch_related()` for ManyToMany
- Bulk operations for multiple records
- Database indexes on frequently queried fields

**API:**
- Custom pagination for large datasets
- Optimized queries with proper joins
- Cache frequently accessed data
- Rate limiting (planned, not implemented)

**Background Tasks:**
- Bulk operations in Celery tasks
- Chunk large datasets
- Proper error handling and retries
- Task result tracking

## Security Considerations

**Current State:**
- ⚠️ No API authentication (all endpoints public)
- ⚠️ No rate limiting
- ⚠️ No input validation on some endpoints

**Best Practices:**
- Environment variables for secrets
- Never commit API keys
- Use Django's built-in security features
- Validate all user input
- SQL injection protection (Django ORM)

**Planned Enhancements:**
- JWT authentication
- API key authentication
- Rate limiting per client
- Request ID tracking
- CORS configuration

## Monitoring & Debugging

**Logging:**
- Docker logs for all services
- Django logging configured
- Celery task logging

**Health Checks:**
- `/api/healthcheck/` endpoint
- Docker container status
- Celery worker status

**Debugging:**
- Django shell for interactive debugging
- Docker logs for service issues
- Django Debug Toolbar (local only)
