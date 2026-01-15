# Quick Start Guide

Get the B2B Travel Platform up and running in minutes using Docker.

## Prerequisites

- Docker Desktop installed
- Docker Compose installed
- Git (for cloning the repository)

## 5-Minute Setup

### 1. Clone Repository

```bash
git clone <repository-url>
cd TravelApp/BackEnd
```

### 2. Configure Environment

```bash
# Create .env file from template
cp .env.example .env

# Edit .env with your settings
# Minimum required:
# SECRET_KEY=your-secret-key-here
# DEBUG=True
# DOCKER=true
```

### 3. Start Services

```bash
# Start all services (db, web, redis, celery-worker, celery-beat)
docker-compose up -d

# View logs to ensure startup
docker-compose logs -f web
```

### 4. Initialize Database

```bash
# Run migrations
docker-compose exec web python manage.py migrate

# Create superuser
docker-compose exec web python manage.py createsuperuser
```

### 5. Access the Application

- **Django Admin**: http://localhost:8000/admin/
- **API Endpoints**: http://localhost:8000/api/
- **Health Check**: http://localhost:8000/api/healthcheck/

## Common Commands

### Service Management

```bash
# Start all services
docker-compose up -d

# Start in foreground (see logs live)
docker-compose up

# Stop all services
docker-compose down

# Stop and remove volumes (deletes database)
docker-compose down -v

# Restart specific service
docker-compose restart web
```

### Database Operations

```bash
# Run migrations
docker-compose exec web python manage.py migrate

# Create migrations
docker-compose exec web python manage.py makemigrations

# Create superuser
docker-compose exec web python manage.py createsuperuser

# Open Django shell
docker-compose exec web python manage.py shell

# Access PostgreSQL directly
docker-compose exec db psql -U myuser -d mydatabase
```

### Data Synchronization

```bash
# Sync all data from Zego
docker-compose exec web python manage.py sync_zego

# Sync only countries
docker-compose exec web python manage.py sync_zego --countries-only

# Sync only tours
docker-compose exec web python manage.py sync_zego --tours-only

# Sync Unique Inter data
docker-compose exec web python manage.py sync_unique_inter

# Sync Go365 data
docker-compose exec web python manage.py sync_go365

# Audit tour countries
docker-compose exec web python manage.py audit_tour_countries
```

### Viewing Logs

```bash
# All services, follow mode
docker-compose logs -f

# Specific service
docker-compose logs -f web
docker-compose logs -f celery-worker

# Last 100 lines
docker-compose logs --tail=100 web
```

## Troubleshooting

### Port Already in Use

```bash
# Check what's using port 8000
lsof -i :8000

# Stop the conflicting service
# Or change port in docker-compose.yml
```

### Database Connection Issues

```bash
# Check database container is running
docker-compose ps db

# View database logs
docker-compose logs db

# Restart database
docker-compose restart db
```

### Code Changes Not Reflecting

```bash
# Verify volume mount is working
docker-compose exec web ls -la /app

# Restart web service
docker-compose restart web
```

### Reset Everything

```bash
# Stop everything and delete data
docker-compose down -v

# Start fresh
docker-compose up -d

# Re-run migrations
docker-compose exec web python manage.py migrate
```

## First Steps After Setup

### 1. Create Wholesale Providers

Navigate to http://localhost:8000/admin/ and create providers:

**Zego Provider:**
- Name: Zego Travel
- Code: zego
- Base URL: https://www.zegoapi.com
- Token: your-zego-api-token

**Unique Inter Provider:**
- Name: Unique Inter Wholesale
- Code: unique_inter
- Base URL: https://uniqueinterwholesale.com
- Extra: `{"user_email": "your-email@example.com"}`

### 2. Sync Initial Data

```bash
# Sync categories (Unique Inter only)
docker-compose exec web python manage.py sync_unique_inter_categories

# Sync countries and tours
docker-compose exec web python manage.py sync_zego
docker-compose exec web python manage.py sync_unique_inter
```

### 3. Verify API Endpoints

```bash
# Health check
curl http://localhost:8000/api/healthcheck/

# List tours
curl http://localhost:8000/api/tours/

# List program tours
curl http://localhost:8000/api/wholesale/program-tours/
```

## Next Steps

- Read [Project Overview](project-overview.md) for system architecture
- Read [New Developer Guide](new-developer-guide.md) for comprehensive onboarding
- Read [Commands Reference](../development/commands-reference.md) for all available commands
- Read [Provider Integration Guide](../provider-integration/adapter-guide.md) to add new providers

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SECRET_KEY` | Yes | - | Django secret key |
| `DEBUG` | No | `False` | Enable debug mode |
| `DOCKER` | Yes | `false` | Must be `true` for Docker |
| `DB_HOST` | Yes | `db` | PostgreSQL service name |
| `DB_NAME` | Yes | - | Database name |
| `DB_USER` | Yes | - | Database user |
| `DB_PASS` | Yes | - | Database password |
| `WS_API_ENDPOINT_01_URL` | No | - | Zego API base URL |
| `WS_API_ENDPOINT_01_TOKEN` | No | - | Zego API token |

## Docker Services

| Service | Purpose | Ports |
|---------|---------|-------|
| `db` | PostgreSQL database | 5432 (internal) |
| `web` | Django application | 8000 (host:container) |
| `redis` | Message broker & cache | 6379 (internal) |
| `celery-worker` | Background task processor | - |
| `celery-beat` | Scheduled task manager | - |
