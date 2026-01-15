# New Developer Guide - TravelApp B2B Travel Platform

## Welcome to the Team!

This guide will help you get started with the TravelApp B2B travel platform. Our system is a sophisticated Django-based application that aggregates tour data from multiple wholesale travel providers and serves it to B2B clients.

## Team Culture & Principles

### Our Development Philosophy
- **Professional Travel Industry Focus**: We build enterprise-grade systems for the travel industry
- **No Over-Engineering**: Simple, maintainable solutions over complex architectures
- **Reuse Existing Components**: Leverage our proven patterns and utilities
- **Modular Design**: Avoid monolithic structures and spaghetti code
- **Production Safety**: Never break existing production functionality

### Code Quality Standards
- **PEP 8 Compliance**: All code must follow Python style guidelines
- **Type Hints**: Required for all functions and methods
- **Documentation**: Comprehensive docstrings for all public methods
- **Testing**: Write tests for all new functionality
- **Code Reviews**: All code requires peer review before merge

## Getting Started

### Prerequisites
- Python 3.9+
- Docker & Docker Compose
- Git
- PostgreSQL client tools (optional, for local development)

### Development Environment Setup

#### 1. Clone and Setup Repository
```bash
git clone <repository-url>
cd TravelApp/BackEnd
```

#### 2. Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

#### 3. Environment Configuration
```bash
# Copy environment template
cp .env.example .env

# Edit .env with your configuration
# At minimum, set:
# SECRET_KEY=your-secret-key-here
# DEBUG=True
# DOCKER=false
```

#### 4. Database Setup
```bash
# Create and apply migrations
python manage.py makemigrations
python manage.py migrate

# Create superuser for admin access
python manage.py createsuperuser

# Load initial data (countries, categories, etc.)
python manage.py loaddata initial_data.json
```

#### 5. Start Development Server
```bash
python manage.py runserver
```

Visit http://localhost:8000/admin to access Django admin.

### Docker Development Setup

```bash
# Start all services
docker-compose -f docker-compose.yml up

# View logs
docker-compose -f docker-compose.yml logs -f

# Stop services
docker-compose -f docker-compose.yml down
```

## System Architecture Overview

### Application Structure
```
TravelApp/BackEnd/
├── Core/                 # Django project configuration
│   ├── settings/         # Environment-specific settings
│   ├── urls.py          # Main URL configuration
│   └── wsgi.py          # WSGI configuration
├── Accounts/            # Custom user authentication
├── tours/               # Internal tour management
├── wholesale/           # Provider integration
├── management/          # Django management commands
└── tests/               # Test suite
```

### Key Components

#### 1. Provider Adapter System
Located in `wholesale/services/`, this is our core abstraction for handling different travel provider APIs.

**Key Files:**
- `provider_factory.py` - Factory pattern for provider services
- `base_provider.py` - Abstract base class for providers
- `zego_service.py` - Zego API integration
- `unique_inter_service.py` - Unique Inter API integration

#### 2. Data Synchronization Services
Located in `wholesale/services/`, handles data syncing from external providers.

**Key Files:**
- `sync_service.py` - Main synchronization orchestration
- `data_processor.py` - Data validation and processing
- `country_normalizer.py` - Country name standardization

#### 3. Business Logic Layer
Located in `tours/services/`, contains core business logic.

**Key Files:**
- `pricing_service.py` - Pricing calculations
- `availability_service.py` - Availability management
- `flash_sale_service.py` - Promotion management

## Development Workflow

### 1. Feature Development

#### Create Feature Branch
```bash
git checkout -b feature/your-feature-name
```

#### Development Process
1. **Understand Requirements**: Read the ticket or specification thoroughly
2. **Explore Existing Code**: Look for similar patterns in the codebase
3. **Reuse Components**: Check if existing utilities or services can be reused
4. **Write Code**: Follow our coding standards and patterns
5. **Write Tests**: Ensure comprehensive test coverage
6. **Run Tests**: All tests must pass before submitting

#### Example: Adding a New Provider

1. **Create Provider Service**:
```python
# wholesale/services/new_provider_service.py
from .base_provider import BaseProvider

class NewProviderService(BaseProvider):
    def __init__(self, provider):
        super().__init__(provider)
        self.base_url = provider.base_url
        self.api_key = provider.token

    def fetch_countries(self):
        # Implement country fetching logic
        pass

    def fetch_tours(self, category_id=None):
        # Implement tour fetching logic
        pass

    def process_tour_data(self, raw_data):
        # Implement data processing logic
        pass
```

2. **Register in Factory**:
```python
# wholesale/services/provider_factory.py
from .new_provider_service import NewProviderService

PROVIDER_SERVICES = {
    'zego': ZegoService,
    'unique_inter': UniqueInterService,
    'new_provider': NewProviderService,  # Add this
}
```

3. **Add Tests**:
```python
# tests/test_new_provider_service.py
class NewProviderServiceTest(TestCase):
    def setUp(self):
        self.provider = Provider.objects.create(
            name='New Provider',
            code='new_provider',
            base_url='https://api.newprovider.com',
            token='test-token'
        )
        self.service = NewProviderService(self.provider)

    def test_fetch_countries(self):
        # Test country fetching
        pass
```

### 2. Testing Strategy

#### Test Structure
```
tests/
├── unit/                 # Unit tests
│   ├── test_models.py
│   ├── test_services.py
│   └── test_utils.py
├── integration/          # Integration tests
│   ├── test_api.py
│   └── test_sync.py
└── fixtures/             # Test data
```

#### Running Tests
```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test tests.unit.test_services

# Run with coverage
coverage run --source='.' manage.py test
coverage report
coverage html
```

#### Test Writing Guidelines

**Unit Tests:**
```python
from django.test import TestCase
from wholesale.services.pricing_service import PricingService

class PricingServiceTest(TestCase):
    def setUp(self):
        self.service = PricingService()

    def test_calculate_total_price_with_single_supplement(self):
        base_price = Decimal('1000.00')
        single_supplement = Decimal('200.00')

        total = self.service.calculate_total_price(
            base_price,
            single_supplement=single_supplement
        )

        self.assertEqual(total, Decimal('1200.00'))
```

**Integration Tests:**
```python
from rest_framework.test import APITestCase
from rest_framework import status

class TourAPITestCase(APITestCase):
    def setUp(self):
        self.user = Account.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)

    def test_list_tours_with_filters(self):
        response = self.client.get('/api/v1/tours/?country=FR')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
```

### 3. Database Migrations

#### Creating Migrations
```bash
# Create migration for changes
python manage.py makemigrations

# Create migration for specific app
python manage.py makemigrations tours

# Create empty migration for data migrations
python manage.py makemigrations --empty wholesale
```

#### Migration Best Practices
1. **Always review migrations** before applying
2. **Provide descriptive migration names**
3. **Handle data migrations separately** from schema migrations
4. **Test migrations on copy of production data**

#### Example Data Migration
```python
# wholesale/migrations/0002_populate_countries.py
from django.db import migrations

def populate_countries(apps, schema_editor):
    Country = apps.get_model('wholesale', 'Country')
    Country.objects.bulk_create([
        Country(code='FR', name='France'),
        Country(code='IT', name='Italy'),
        # ... more countries
    ])

class Migration(migrations.Migration):
    dependencies = [
        ('wholesale', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(populate_countries),
    ]
```

### 4. Code Review Process

#### Before Submitting Pull Request
1. **Self-Review**: Review your own code first
2. **Run Tests**: Ensure all tests pass
3. **Check Code Quality**: Run flake8 and black
4. **Update Documentation**: Update relevant documentation
5. **Write Clear Commit Messages**: Use conventional commit format

#### Pull Request Template
```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No breaking changes (or clearly documented)
```

#### Code Review Guidelines
- **Focus on Logic**: Review business logic and implementation
- **Check Patterns**: Ensure consistent patterns are used
- **Security Review**: Check for security vulnerabilities
- **Performance Review**: Consider performance implications
- **Testing**: Verify adequate test coverage

## Common Development Tasks

### 1. Adding New API Endpoint

#### Step 1: Create Serializer
```python
# tours/serializers.py
from rest_framework import serializers
from .models import Tour

class TourSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tour
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')

    def validate_base_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Price must be positive")
        return value
```

#### Step 2: Create View
```python
# tours/views.py
from rest_framework import viewsets
from .models import Tour
from .serializers import TourSerializer

class TourViewSet(viewsets.ModelViewSet):
    queryset = Tour.objects.all()
    serializer_class = TourSerializer
    filterset_fields = ['country', 'category']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'base_price', 'created_at']
```

#### Step 3: Register URLs
```python
# tours/urls.py
from rest_framework.routers import DefaultRouter
from .views import TourViewSet

router = DefaultRouter()
router.register(r'tours', TourViewSet)

urlpatterns = router.urls
```

### 2. Adding Management Command

#### Create Command File
```python
# management/commands/sync_provider_data.py
from django.core.management.base import BaseCommand
from wholesale.services.sync_service import SyncService

class Command(BaseCommand):
    help = 'Sync data from wholesale providers'

    def add_arguments(self, parser):
        parser.add_argument('--provider', type=str, help='Provider code')
        parser.add_argument('--full-sync', action='store_true', help='Perform full sync')

    def handle(self, *args, **options):
        provider_code = options.get('provider')
        full_sync = options.get('full_sync', False)

        sync_service = SyncService()

        if provider_code:
            sync_service.sync_provider(provider_code, full_sync=full_sync)
        else:
            sync_service.sync_all_providers(full_sync=full_sync)

        self.stdout.write(self.style.SUCCESS('Sync completed successfully'))
```

#### Run Command
```bash
python manage.py sync_provider_data --provider zego --full-sync
```

### 3. Debugging Common Issues

#### Database Issues
```python
# Check database connections
from django.db import connection
print(connection.queries)  # Show recent queries

# Debug slow queries
from django.conf import settings
if settings.DEBUG:
    print("Database queries:", len(connection.queries))
```

#### External API Issues
```python
# Debug API calls
import requests
import logging

logger = logging.getLogger(__name__)

def debug_api_call(url, params=None):
    try:
        response = requests.get(url, params=params, timeout=30)
        logger.info(f"API call to {url} - Status: {response.status_code}")
        return response
    except requests.RequestException as e:
        logger.error(f"API call failed: {e}")
        raise
```

#### Celery Task Issues
```python
# Debug Celery tasks
from celery import current_app

def debug_task_status(task_id):
    result = current_app.AsyncResult(task_id)
    print(f"Task {task_id} status: {result.status}")
    if result.failed():
        print(f"Error: {result.result}")
```

## Performance Guidelines

### Database Optimization

#### Query Optimization
```python
# Good: Use select_related for foreign keys
tours = Tour.objects.select_related('operator', 'category').all()

# Good: Use prefetch_related for many-to-many
tours = Tour.objects.prefetch_related('countries').all()

# Bad: N+1 queries
for tour in Tour.objects.all():
    print(tour.operator.name)  # This creates N+1 queries
```

#### Indexing Strategy
```python
# Add indexes to frequently queried fields
class Tour(models.Model):
    name = models.CharField(max_length=200, db_index=True)
    base_price = models.DecimalField(max_digits=10, decimal_places=2, db_index=True)
    country = models.ForeignKey('Country', on_delete=models.CASCADE, db_index=True)

    class Meta:
        indexes = [
            models.Index(fields=['country', 'base_price']),
            models.Index(fields=['created_at']),
        ]
```

### Caching Strategy

#### Redis Caching
```python
from django.core.cache import cache
from django.conf import settings

def get_countries_with_cache():
    cache_key = 'countries_list'
    countries = cache.get(cache_key)

    if not countries:
        countries = list(Country.objects.values('code', 'name'))
        cache.set(cache_key, countries, timeout=settings.CACHE_TTL)

    return countries
```

### Background Task Optimization

#### Celery Best Practices
```python
from celery import shared_task
from django.db import transaction

@shared_task(bind=True, max_retries=3)
def sync_provider_data(self, provider_id):
    try:
        with transaction.atomic():
            # Process data within transaction
            pass
    except Exception as exc:
        # Retry with exponential backoff
        countdown = 2 ** self.request.retries
        raise self.retry(exc=exc, countdown=countdown)
```

## Security Best Practices

### Input Validation
```python
from django.core.exceptions import ValidationError
from rest_framework import serializers

def validate_price(value):
    if value <= 0:
        raise ValidationError("Price must be positive")
    if value > Decimal('99999.99'):
        raise ValidationError("Price exceeds maximum allowed")

class TourSerializer(serializers.ModelSerializer):
    base_price = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[validate_price]
    )
```

### Secure API Design
```python
# Use authentication and permission classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.throttling import UserRateThrottle

class TourViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle]
    # ... rest of viewset
```

### Environment Security
```python
# Use environment variables for sensitive data
import os
from django.core.exceptions import ImproperlyConfigured

def get_env_variable(var_name):
    try:
        return os.environ[var_name]
    except KeyError:
        raise ImproperlyConfigured(f'Set the {var_name} environment variable')
```

## Troubleshooting Guide

### Common Issues and Solutions

#### 1. Database Connection Issues
```bash
# Check if PostgreSQL is running
docker-compose ps

# Check database logs
docker-compose logs db

# Reset database (caution: destroys data)
docker-compose down -v
docker-compose up -d db
```

#### 2. Redis/Celery Issues
```bash
# Check Redis status
docker-compose exec redis redis-cli ping

# Check Celery workers
docker-compose exec web celery -A Core worker -l info

# Clear Celery queue
docker-compose exec web celery -A Core purge
```

#### 3. External API Issues
```python
# Test external API connectivity
import requests
response = requests.get('https://external-api.com/health')
print(response.status_code)
```

#### 4. Performance Issues
```bash
# Check database query count
python manage.py shell
>>> from django.db import connection
>>> from tours.models import Tour
>>> tours = list(Tour.objects.all())
>>> print(len(connection.queries))
```

## Monitoring and Logging

### Structured Logging
```python
import logging
import json

logger = logging.getLogger(__name__)

def sync_provider(provider_code):
    logger.info("Starting sync", extra={
        'provider_code': provider_code,
        'sync_type': 'full'
    })

    try:
        # Sync logic here
        logger.info("Sync completed successfully", extra={
            'provider_code': provider_code,
            'tours_synced': 150
        })
    except Exception as e:
        logger.error("Sync failed", extra={
            'provider_code': provider_code,
            'error': str(e)
        }, exc_info=True)
```

### Health Checks
```python
# management/commands/health_check.py
from django.core.management.base import BaseCommand
from django.db import connection
from django.core.cache import cache

class Command(BaseCommand):
    help = 'Check system health'

    def handle(self, *args, **options):
        checks = {}

        # Database check
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            checks['database'] = 'OK'
        except Exception as e:
            checks['database'] = f'ERROR: {e}'

        # Cache check
        try:
            cache.set('health_check', 'OK', 60)
            cache.get('health_check')
            checks['cache'] = 'OK'
        except Exception as e:
            checks['cache'] = f'ERROR: {e}'

        # Output results
        for service, status in checks.items():
            self.stdout.write(f"{service}: {status}")
```

## Deployment Guide

### Staging Deployment
1. **Create Pull Request**: Create PR from feature to develop branch
2. **Automated Tests**: CI/CD pipeline runs all tests
3. **Manual QA**: Test on staging environment
4. **Code Review**: Team review and approval
5. **Merge**: Merge to develop branch

### Production Deployment
1. **Release Branch**: Create release branch from develop
2. **Final Testing**: Comprehensive testing on staging
3. **Production Deploy**: Deploy to production with zero downtime
4. **Monitoring**: Monitor application health and performance
5. **Rollback**: Prepared to rollback if issues arise

## Resources and References

### Internal Documentation
- [CLAUDE.md](./CLAUDE.md) - Main project documentation
- [API_DOCUMENTATION.md](./API_DOCUMENTATION.md) - API reference
- [PROVIDER_ADAPTER_GUIDE.md](./PROVIDER_ADAPTER_GUIDE.md) - Provider integration guide

### External Resources
- [Django Documentation](https://docs.djangoproject.com/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [Celery Documentation](https://docs.celeryproject.org/)
- [Redis Documentation](https://redis.io/documentation)

### Team Communication
- **Slack**: #travelapp-development channel
- **Project Management**: Jira/Asana (as configured)
- **Code Reviews**: GitHub/GitLab pull requests

## Questions and Support

### Getting Help
1. **Search Documentation**: Check existing documentation first
2. **Ask in Slack**: Post questions in the development channel
3. **Create Ticket**: Create bug report or feature request
4. **Pair Programming**: Ask for help with complex problems

### Onboarding Buddy
You'll be assigned an onboarding buddy who will:
- Help with initial setup questions
- Review your first few pull requests
- Answer questions about codebase and processes
- Guide you through team practices

Welcome aboard! We're excited to have you join our team. Remember, we prioritize collaboration, code quality, and continuous learning. Don't hesitate to ask questions and contribute ideas!