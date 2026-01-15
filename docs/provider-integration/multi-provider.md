# Multi-Provider Integration Design

## Overview

Simple, clean design for supporting multiple tour operator providers without over-engineering. Reuses existing components and follows Django best practices.

## Current Architecture Analysis

The system already has a solid foundation:

- ✅ **BaseAPIService**: Abstract base class for all providers
- ✅ **APIServiceFactory**: Creates appropriate service instances
- ✅ **Provider Models**: Database models for provider configuration
- ✅ **Error Handling**: Structured exception hierarchy
- ✅ **Generic Service**: Configurable service for standard APIs

## Simple Multi-Provider Pattern

### 1. Provider Registration

```python
# Simple provider registration
class Provider(models.Model):
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=50, unique=True)  # 'zego', 'unique_inter'
    base_url = models.URLField()
    token = models.CharField(max_length=512, blank=True)

    # Configuration options
    auth_method = models.CharField(
        max_length=20,
        choices=[
            ('bearer', 'Bearer Token'),
            ('apikey', 'API Key Header'),
            ('basic', 'Basic Auth'),
            ('custom', 'Custom Header')
        ],
        default='bearer'
    )

    # Service type selection
    service_type = models.CharField(
        max_length=20,
        choices=[
            ('specific', 'Specific Service'),
            ('generic', 'Generic Service'),
            ('auto', 'Auto Detect')
        ],
        default='auto'
    )

    # Optional custom configuration
    extra = models.JSONField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
```

### 2. Service Factory (Enhanced)

```python
class APIServiceFactory:
    """Simple factory for creating provider services"""

    _service_registry = {
        'zego': ZegoAPIService,
        'unique_inter': UniqueInterAPIService,
        # Add new specific services here
    }

    @classmethod
    def create_service(cls, provider) -> BaseAPIService:
        """Create service based on provider configuration"""

        # 1. Check for specific service
        if provider.service_type == 'specific':
            service_class = cls._service_registry.get(provider.code.lower())
            if service_class:
                return service_class(provider)

        # 2. Use generic service
        elif provider.service_type == 'generic':
            endpoint_config = provider.extra.get('endpoints') if provider.extra else None
            return GenericAPIService(provider, endpoint_config)

        # 3. Auto-detect (default)
        else:
            # Try specific service first
            service_class = cls._service_registry.get(provider.code.lower())
            if service_class:
                return service_class(provider)

            # Fall back to generic
            logger.info(f"Using GenericAPIService for {provider.code}")
            return GenericAPIService(provider)

    @classmethod
    def register_service(cls, code: str, service_class):
        """Register a new specific service"""
        cls._service_registry[code.lower()] = service_class
```

### 3. Generic Service (Simplified)

```python
class GenericAPIService(BaseAPIService):
    """Configurable service for standard REST APIs"""

    def __init__(self, provider, endpoint_config=None):
        super().__init__(provider)

        # Default endpoint mapping
        self.endpoints = {
            'countries': 'countries',
            'tours': 'tours',
            'tour_detail': 'tours/{id}',
            'periods': 'tours/{id}/periods'
        }

        # Override with provider config
        if endpoint_config:
            self.endpoints.update(endpoint_config)

    def _setup_authentication(self):
        """Setup auth based on provider.auth_method"""
        if not self.token:
            return

        if provider.auth_method == 'bearer':
            self.session.headers.update({
                'Authorization': f'Bearer {self.token}'
            })
        elif provider.auth_method == 'apikey':
            header_name = provider.extra.get('auth_header', 'X-API-Key')
            self.session.headers.update({
                header_name: self.token
            })
        elif provider.auth_method == 'basic':
            from requests.auth import HTTPBasicAuth
            username = provider.extra.get('auth_username', '')
            self.session.auth = HTTPBasicAuth(username, self.token)

    def get_countries(self):
        return self._make_request(self.endpoints['countries'])

    def get_program_tours(self):
        return self._make_request(self.endpoints['tours'])

    def get_program_tour_details(self, tour_id):
        endpoint = self.endpoints['tour_detail'].format(id=tour_id)
        return self._make_request(endpoint)
```

## Adding a New Provider

### Option 1: Use Generic Service (Easiest)

```python
# 1. Register provider in admin
provider = Provider.objects.create(
    name='Tour Operator XYZ',
    code='xyz_tours',
    base_url='https://api.xyztours.com/v1',
    token='your-api-token',
    extra={
        'auth_method': 'bearer',
        'service_type': 'generic',
        'endpoints': {
            'countries': 'destinations',
            'tours': 'packages',
            'tour_detail': 'packages/{id}'
        }
    }
)
```

### Option 2: Create Specific Service (For Complex APIs)

**Example: Go365 Travel Integration**

```python
# 1. Create service class in wholesale/api_service.py
class Go365APIService(BaseAPIService):
    """
    Go365 Travel API integration service.
    Supports multi-language (Thai, English, Chinese) and standard REST endpoints.
    """

    def __init__(self, provider):
        # Set language config before parent init
        self.default_language = 'en'
        if hasattr(provider, 'extra') and provider.extra:
            self.default_language = provider.extra.get('default_language', 'en')

        super().__init__(provider)

    def _setup_authentication(self):
        """Setup Go365 API authentication with x-api-key header"""
        if self.token:
            self.session.headers.update({
                'x-api-key': self.token,
                'x-accept-language': self.default_language
            })

    def get_countries(self) -> Optional[List[Dict]]:
        """Fetch available countries/destinations from Go365 API"""
        return self._make_request('api/v1/tours/country')

    def get_program_tours(self, page: int = 1, limit: int = 10) -> Optional[List[Dict]]:
        """Fetch tour list with pagination support"""
        params = {'start_page': page, 'limit_page': limit}
        return self._make_request('api/v1/tours/list', params=params)

    def get_program_tour_details(self, tour_id: str) -> Optional[Dict]:
        """Fetch detailed information for a specific tour"""
        return self._make_request(f'api/v1/tours/detail/{tour_id}')

    def search_tours(self, search_query: str = None, **filters) -> Optional[List[Dict]]:
        """Search tours with multiple filters"""
        data = {'search': search_query, **filters}
        return self._make_request('api/v1/tours/search', method='POST', data=data)

    def set_language(self, language: str):
        """Change API response language"""
        supported_languages = ['th', 'en', 'ch']
        if language in supported_languages:
            self.session.headers.update({'x-accept-language': language})

# 2. Register service in APIServiceFactory
class APIServiceFactory:
    @staticmethod
    def create_service(provider) -> BaseAPIService:
        provider_code = provider.code.lower()

        if provider_code == 'go365':
            return Go365APIService(provider)
        # ... other providers

# 3. Register provider using convenience method
from wholesale.services import ProviderRegistrationService

provider = ProviderRegistrationService.register_go365_provider(
    name='Go365 Travel',
    code='go365',
    base_url='https://www.go365travel.com',
    api_key='your-api-key',
    default_language='en'
)

# 4. Create management command
# See: wholesale/management/commands/sync_go365.py

# 5. Usage examples
# Setup provider:
python manage.py sync_go365 --setup-provider your-api-key

# Test connection:
python manage.py sync_go365 --test-connection

# Fetch countries:
python manage.py sync_go365 --countries-only

# Search tours:
python manage.py sync_go365 --search "europe" --limit 5

# Full sync:
python manage.py sync_go365
```

## Synchronization Service

### Simple Multi-Provider Sync

```python
class MultiProviderSyncService:
    """Simple service to sync multiple providers"""

    def __init__(self):
        self.factory = APIServiceFactory()

    def sync_all_providers(self):
        """Sync all active providers"""
        providers = Provider.objects.filter(is_active=True)

        results = {}
        for provider in providers:
            try:
                result = self.sync_provider(provider)
                results[provider.code] = result
            except Exception as e:
                logger.error(f"Failed to sync {provider.code}: {e}")
                results[provider.code] = {'error': str(e)}

        return results

    def sync_provider(self, provider):
        """Sync a single provider"""
        service = self.factory.create_service(provider)

        # Test connection
        if not service.test_connection():
            raise ConnectionError(f"Cannot connect to {provider.name}")

        # Sync countries
        countries = service.get_countries()
        # Process countries...

        # Sync tours
        tours = service.get_program_tours()
        # Process tours...

        return {
            'countries': len(countries) if countries else 0,
            'tours': len(tours) if tours else 0,
            'status': 'success'
        }
```

## Configuration Examples

### Standard REST API Provider

```python
Provider.objects.create(
    name='Standard Tours API',
    code='standard_tours',
    base_url='https://api.standardtours.com',
    token='your-api-key',
    auth_method='apikey',
    service_type='generic',
    extra={
        'auth_header': 'X-Standard-API-Key',
        'endpoints': {
            'countries': 'countries/available',
            'tours': 'tours/available',
            'tour_detail': 'tours/details/{id}'
        }
    }
)
```

### Bearer Token Authentication

```python
Provider.objects.create(
    name='Bearer Auth Tours',
    code='bearer_tours',
    base_url='https://api.bearertours.com',
    token='your-jwt-token',
    auth_method='bearer',
    service_type='generic'
)
```

### Basic Authentication

```python
Provider.objects.create(
    name='Basic Auth Tours',
    code='basic_tours',
    base_url='https://api.basictours.com',
    token='password-here',
    auth_method='basic',
    service_type='generic',
    extra={
        'auth_username': 'api-user'
    }
)
```

## Management Command

```python
# management/commands/sync_providers.py
from django.core.management.base import BaseCommand
from wholesale.services import MultiProviderSyncService

class Command(BaseCommand):
    help = 'Sync all active providers'

    def add_arguments(self, parser):
        parser.add_argument('--provider', type=str, help='Sync specific provider only')
        parser.add_argument('--list', action='store_true', help='List available providers')

    def handle(self, *args, **options):
        sync_service = MultiProviderSyncService()

        if options['list']:
            providers = Provider.objects.filter(is_active=True)
            for provider in providers:
                self.stdout.write(f"- {provider.code}: {provider.name}")
            return

        if options['provider']:
            provider = Provider.objects.get(code=options['provider'])
            result = sync_service.sync_provider(provider)
            self.stdout.write(f"Synced {provider.code}: {result}")
        else:
            results = sync_service.sync_all_providers()
            for code, result in results.items():
                self.stdout.write(f"{code}: {result}")
```

## Best Practices

### 1. Keep It Simple
- Use GenericAPIService for standard REST APIs
- Only create specific services for complex integrations
- Follow Django conventions

### 2. Reuse Components
- BaseAPIService handles all HTTP requests
- APIServiceFactory manages service creation
- Error handling is centralized

### 3. Configuration-Driven
- Store API-specific config in `extra` field
- Use service_type to control behavior
- Keep auth method configurable

### 4. Error Handling
- All services inherit error handling from BaseAPIService
- Log errors with provider context
- Don't fail entire sync for one provider

### 5. Testing
- Test connection before syncing
- Validate provider configuration
- Mock API responses for testing

## Usage Examples

### Sync All Providers

```python
from wholesale.services import MultiProviderSyncService

sync_service = MultiProviderSyncService()
results = sync_service.sync_all_providers()

print(results)
# {'zego': {'countries': 50, 'tours': 200, 'status': 'success'},
#  'unique_inter': {'countries': 6, 'tours': 150, 'status': 'success'}}
```

### Sync Specific Provider

```python
provider = Provider.objects.get(code='zego')
service = APIServiceFactory.create_service(provider)
tours = service.get_program_tours()
```

### Add New Provider Programmatically

```python
# Register new provider
provider = Provider.objects.create(
    name='New Tour Operator',
    code='new_operator',
    base_url='https://api.newoperator.com',
    token='your-token',
    service_type='generic'
)

# Sync immediately
sync_service = MultiProviderSyncService()
result = sync_service.sync_provider(provider)
```

## Summary

This design provides:

✅ **Simplicity**: Uses existing components, minimal new code
✅ **Flexibility**: Handles different auth methods and API patterns
✅ **Reusability**: GenericAPIService works for most REST APIs
✅ **Maintainability**: Clear separation of concerns
✅ **No Over-Engineering**: Focus on practical solutions
✅ **No Monolithic Code**: Modular, testable components
✅ **No Spaghetti Patterns**: Clean inheritance and composition

The system can handle any number of providers by either using the configurable GenericAPIService or creating specific services when needed.