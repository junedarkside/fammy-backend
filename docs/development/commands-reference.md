# Commands Reference

Complete reference of all Django management commands for the B2B Travel Platform.

## Environment Management

### Virtual Environment

```bash
# Activate virtual environment
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows

# Deactivate virtual environment
deactivate
```

### Docker Services

```bash
# Start all services (development)
docker-compose up

# Start in detached mode (background)
docker-compose up -d

# Stop all services
docker-compose down

# Stop and remove volumes (deletes database)
docker-compose down -v

# View logs for all services
docker-compose logs -f

# View logs for specific service
docker-compose logs -f web
docker-compose logs -f celery-worker

# Rebuild containers
docker-compose up --build

# Force rebuild without cache
docker-compose build --no-cache
```

## Django Management Commands

### Core Commands

```bash
# Run development server (local, not Docker)
python manage.py runserver

# Create database migrations
python manage.py makemigrations

# Apply database migrations
python manage.py migrate

# Create superuser for admin access
python manage.py createsuperuser

# Open Django shell
python manage.py shell

# Check project for issues
python manage.py check

# Collect static files
python manage.py collectstatic
```

### Docker Wrapper Commands

Execute Django commands inside Docker container:

```bash
# Run any management command in Docker
docker-compose exec web python manage.py <command>

# Examples:
docker-compose exec web python manage.py makemigrations
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser
docker-compose exec web python manage.py shell
```

## Data Synchronization Commands

### Zego Provider

```bash
# Sync all data (countries + tours)
docker-compose exec web python manage.py sync_zego

# Sync only countries
docker-compose exec web python manage.py sync_zego --countries-only

# Sync only tours
docker-compose exec web python manage.py sync_zego --tours-only

# Check for updates before syncing
docker-compose exec web python manage.py sync_zego --check-updates
```

### Unique Inter Provider

```bash
# Discover and sync categories (first time setup)
docker-compose exec web python manage.py sync_unique_inter_categories

# Full sync (fetch raw data + process into models)
docker-compose exec web python manage.py sync_unique_inter

# Fetch only (store raw data without processing)
docker-compose exec web python manage.py sync_unique_inter --fetch-only

# Process only (clean and map existing raw data)
docker-compose exec web python manage.py sync_unique_inter --process-only

# Sync specific category only (e.g., category 64 = Vietnam)
docker-compose exec web python manage.py sync_unique_inter --category 64

# Combine options (fetch only for specific category)
docker-compose exec web python manage.py sync_unique_inter --fetch-only --category 59
```

### Go365 Provider

```bash
# Sync data from Go365 provider
docker-compose exec web python manage.py sync_go365
```

## Data Quality Commands

### Country Data Audit

```bash
# Audit all tours with invalid country names
docker-compose exec web python manage.py audit_tour_countries

# Audit specific provider only
docker-compose exec web python manage.py audit_tour_countries --provider-code unique_inter
```

## Database Operations

### PostgreSQL Direct Access

```bash
# Access PostgreSQL directly
docker-compose exec db psql -U myuser -d mydatabase

# Backup database
docker-compose exec db pg_dump -U myuser mydatabase > backup.sql

# Restore database
docker-compose exec -T db psql -U myuser mydatabase < backup.sql
```

### Database Reset

```bash
# Complete database reset (WARNING: deletes all data)
docker-compose down -v
docker-compose up
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser
```

## Celery Operations

### Monitoring

```bash
# View Celery worker logs
docker-compose logs -f celery-worker

# View Celery beat logs
docker-compose logs -f celery-beat

# Check active tasks
docker-compose exec web python manage.py shell
>>> from celery import current_app
>>> current_app.control.inspect().active()
```

### Management

```bash
# Restart Celery worker
docker-compose restart celery-worker

# Restart Celery beat
docker-compose restart celery-beat

# Purge all tasks (use with caution)
docker-compose exec web celery -A Core purge
```

## Development Workflow

### Typical Development Session

```bash
# 1. Start services
docker-compose up -d

# 2. Check logs
docker-compose logs -f web

# 3. Make code changes
# (Edit files in your IDE)

# 4. If needed, restart web service
docker-compose restart web

# 5. Run migrations after model changes
docker-compose exec web python manage.py makemigrations
docker-compose exec web python manage.py migrate

# 6. Create superuser if needed
docker-compose exec web python manage.py createsuperuser

# 7. Access admin at http://localhost:8000/admin/
```

### Testing API Endpoints

```bash
# Health check
curl http://localhost:8000/api/healthcheck/

# List tours
curl http://localhost:8000/api/tours/

# Get specific tour
curl http://localhost:8000/api/tours/tour-slug/

# Trigger provider sync
curl -X POST http://localhost:8000/api/wholesale/providers/zego/sync-program-tours/
```

## Troubleshooting Commands

### Database Connection

```bash
# Check database is running
docker-compose ps db

# Check database logs
docker-compose logs db

# Restart database
docker-compose restart db

# Verify connection
docker-compose exec web python manage.py dbshell
```

### Redis Connection

```bash
# Check Redis is running
docker-compose ps redis

# Check Redis logs
docker-compose logs redis

# Restart Redis
docker-compose restart redis

# Test connection
docker-compose exec redis redis-cli ping
```

### Container Issues

```bash
# Check all containers status
docker-compose ps

# View specific container logs
docker-compose logs web
docker-compose logs celery-worker
docker-compose logs celery-beat

# Restart specific service
docker-compose restart web

# Rebuild and restart
docker-compose up -d --build web
```

### Code Changes Not Reflecting

```bash
# Verify volume mount
docker-compose exec web ls -la /app

# Check if runserver detected changes
docker-compose logs web | grep "Watching for file changes"

# Force restart
docker-compose restart web
```

## Production vs Development

### Development Mode

```bash
# Use docker-compose.yml
docker-compose -f docker-compose.yml up

# Environment variables in .env
DEBUG=True
DOCKER=true
```

### Production Mode

```bash
# Use production compose file (if configured)
docker-compose -f docker-compose-rds.yml up

# Environment variables
DEBUG=False
DOCKER=true
```

## Quick Reference Card

| Command | Purpose |
|---------|---------|
| `docker-compose up -d` | Start all services |
| `docker-compose logs -f web` | View web logs |
| `docker-compose exec web python manage.py migrate` | Run migrations |
| `docker-compose exec web python manage.py createsuperuser` | Create admin user |
| `docker-compose exec web python manage.py sync_zego` | Sync Zego data |
| `docker-compose exec web python manage.py sync_unique_inter` | Sync Unique Inter data |
| `docker-compose restart web` | Restart web service |
| `docker-compose down -v` | Stop and remove all data |
