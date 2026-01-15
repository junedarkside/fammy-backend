# TravelApp Architecture Guide (Simplified & Accurate)

## Core System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    B2B Travel Platform                     │
└─────────────────────────┬───────────────────────────────────┘
                          │
                    ┌─────▼─────┐
                    │  Django    │
                    │  REST API  │
                    └─────┬─────┘
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
┌───────▼────────┐ ┌──────▼──────┐ ┌───────▼───────┐
│  Tours App    │ │ Wholesale   │ │  Accounts    │
│  (Internal)    │ │ (Providers) │ │ (Auth)       │
└────────────────┘ └─────────────┘ └───────────────┘
```

## Application Structure (Actual)

```
TravelApp/BackEnd/
├── Core/                 # Django project settings
│   ├── settings.py      # Environment-aware configuration
│   ├── urls.py          # Main URL routing
│   └── celery.py        # Celery configuration
├── Accounts/            # Email-based authentication
├── tours/               # Internal tour management
│   ├── models.py        # Tour, Operator, Country models
│   ├── views.py         # Tour API views
│   └── serializers.py   # Tour data serialization
├── wholesale/           # External provider integration
│   ├── models.py        # Provider, ProgramTour, Period models
│   ├── api_service.py   # Provider API clients
│   ├── data_sync_service.py # Data transformation
│   └── management/commands/ # Sync commands
└── management/          # Django management commands
```

## Key Components (Actual Implementation)

### 1. Provider Integration System

**Purpose**: Normalize different wholesale APIs into consistent data structure

**Components**:
- **Provider Model**: Stores API credentials and configuration
- **APIService Classes**: HTTP clients for each provider
- **Data Sync Service**: Transforms raw API data to models
- **Management Commands**: CLI interface for data synchronization

**Supported Providers**:
- **Zego**: Tour-centric API with separate periods
- **Unique Inter**: Departure-centric API with categories

### 2. Data Models (Core Entities)

#### Tours App (Internal Management)
```python
class Tour(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)  # Required
    operator = models.ForeignKey(Operator, ...)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.CharField(choices=Category.choices)
    tour_type = models.CharField(choices=Type.choices)
    countries = models.ManyToManyField(Country)

class TravelDate(models.Model):
    tour = models.ForeignKey(Tour, related_name="travel_dates")
    date_start = models.DateField()
    date_end = models.DateField()
    rate = models.DecimalField(max_digits=10, decimal_places=2)
    availability = models.IntegerField()
```

#### Wholesale App (Provider Integration)
```python
class Provider(models.Model):
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=50, unique=True)  # zego, unique_inter
    base_url = models.URLField()
    token = models.CharField(max_length=512, blank=True)
    extra = models.JSONField(blank=True)  # Provider-specific config

class ProgramTour(models.Model):
    provider = models.ForeignKey(Provider, ...)
    external_id = models.CharField(max_length=100)
    name = models.CharField(max_length=255)
    days = models.PositiveIntegerField(blank=True, null=True)
    nights = models.PositiveIntegerField(blank=True, null=True)
    country = models.ForeignKey(Country, null=True, blank=True)
    airline_name = models.CharField(max_length=255, blank=True)
    file_pdf = models.URLField(blank=True, null=True)

class Period(models.Model):
    provider = models.ForeignKey(Provider, ...)
    program = models.ForeignKey(ProgramTour, related_name="periods")
    external_id = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField()
    base_prices = models.JSONField(blank=True)  # {"adult": 1000, ...}
    end_prices = models.JSONField(blank=True)   # Promotional prices
    seats = models.IntegerField(blank=True, null=True)
    status = models.CharField(max_length=50, blank=True)
```

### 3. API Services (Provider Clients)

#### Base Structure
```python
class BaseAPIService(ABC):
    def __init__(self, provider):
        self.provider = provider
        self.session = requests.Session()
        self._setup_authentication()

    @abstractmethod
    def _setup_authentication(self):
        pass

    @abstractmethod
    def get_program_tours(self):
        pass
```

#### Provider Implementations
```python
class ZegoAPIService(BaseAPIService):
    def _setup_authentication(self):
        self.session.headers.update({"auth-token": self.token})

class UniqueInterAPIService(BaseAPIService):
    def __init__(self, provider):
        super().__init__(provider)
        self.user_email = provider.extra.get('user_email', '')

    def get_tour_packages_by_category(self, category_id):
        params = {'id': category_id, 'user': self.user_email}
        return self._make_request('apiweb.php', params=params)
```

### 4. Data Synchronization Patterns

#### Direct Sync (Zego)
1. Fetch tours from API
2. Transform and save to ProgramTour model
3. Fetch periods for each tour
4. Save to Period model

#### Two-Stage Sync (Unique Inter)
1. **Fetch Stage**: Store raw API responses in RawVendorData
2. **Process Stage**: Clean, validate, and map to ProgramTour/Period models

**Benefits**:
- Preserve original data for debugging
- Allow reprocessing without API calls
- Handle complex data transformations

### 5. Management Commands (CLI Interface)

#### Available Commands
```bash
# Zego provider
python manage.py sync_zego_data

# Unique Inter provider
python manage.py sync_unique_inter_categories  # Discover categories
python manage.py sync_unique_inter            # Full sync
python manage.py sync_unique_inter --fetch-only    # Store raw data
python manage.py sync_unique_inter --process-only  # Process existing data

# Quality assurance
python manage.py audit_tour_countries        # Check country data quality
```

## Database Configuration

### Environment-Aware Settings
```python
# settings.py
IS_DOCKER = config('DOCKER', default=False, cast=bool)

if IS_DOCKER:
    DATABASES = {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASS'),
        'HOST': config('DB_HOST', default='db'),
        'PORT': config('DB_PORT', default='5432'),
    }
else:
    DATABASES = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
```

## Celery Configuration

### Background Tasks
```python
# celery.py (in Core/)
from celery import Celery

app = Celery('Core')
app.config_from_object('django.conf:settings', namespace='CELERY')

# Redis configuration
CELERY_BROKER_URL = config('CELERY_BROKER_URL', default='redis://127.0.0.1:6379/0')
CELERY_RESULT_BACKEND = 'django-db'
```

## Key Business Logic

### Pricing Structure (Standardized)
All providers use this 12-key structure:
```python
base_prices = {
    'adult': int,        # Adult price
    'child': int,        # Child with bed
    'child_nb': int,     # Child no bed
    'infant': int,       # Infant price
    'single_bed': int,   # Single supplement
    'twin_bed': int,     # Twin supplement
    'double_bed': int,   # Double supplement
    'triple_bed': int,   # Triple supplement
    'join_land': int,    # Land-only
    'single_visa': int,  # Single visa
    'group_visa': int,   # Group visa
    'express_visa': int, # Express visa
}
```

### Country Normalization
- Extract country names from tour titles
- Map to ISO codes using comprehensive dictionary
- Handle provider-specific variations
- Store both raw name and normalized version

### Error Handling Strategy
- Custom exception hierarchy for API errors
- Graceful degradation for external API failures
- Detailed logging for debugging
- Transaction atomicity for data consistency

## Performance Optimizations

### Database Operations
- **Bulk Operations**: Use bulk_create/bulk_update for large datasets
- **Query Optimization**: select_related/prefetch_related for related data
- **Batch Processing**: Process data in configurable batch sizes

### Caching Strategy
- **Redis Backend**: For frequently accessed data
- **Country Mappings**: Cached in memory for normalization
- **API Responses**: Cached where appropriate

### Background Processing
- **Celery Tasks**: For long-running sync operations
- **Task Queues**: Prioritized by operation type
- **Error Recovery**: Retry with exponential backoff

## Security Considerations

### API Security
- Environment variables for sensitive data
- Request timeout handling
- Input validation and sanitization
- SQL injection prevention (Django ORM)

### Data Protection
- Provider token encryption
- Database connection security
- Audit logging for data changes

## Development Workflow

### Local Development
```bash
# Setup
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Database
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser

# Development server
python manage.py runserver
```

### Docker Development
```bash
# Start services
docker-compose -f docker-compose.yml up

# View logs
docker-compose -f docker-compose.yml logs -f

# Run commands
docker-compose -f docker-compose.yml run --rm web python manage.py sync_zego_data
```

### Testing
```bash
# Run all tests
python manage.py test

# Run with coverage
coverage run --source='.' manage.py test
coverage report
```

## Common Patterns

### Adding New Provider
1. Create Provider record in database
2. Implement APIService class
3. Add data mapping functions
4. Create management command
5. Test with sample data

### Data Quality Management
1. Audit country data regularly
2. Monitor sync error rates
3. Validate pricing structures
4. Check data consistency

### Performance Monitoring
1. Track sync completion times
2. Monitor database query performance
3. Check API response times
4. Review error rates

## Important Notes

### Architecture Decisions
- **Provider-First Design**: External providers drive data structure
- **Two-Stage Sync**: For complex data formats (Unique Inter)
- **Standardized Pricing**: Unified structure across providers
- **Graceful Degradation**: System continues with partial data

### Limitations
- Flight schedules only available in PDFs
- Detailed itineraries not in API responses
- Country name extraction may be imperfect
- Provider API rate limits

### Future Improvements
- Real-time API updates
- Enhanced error recovery
- Better caching strategies
- Performance monitoring dashboard