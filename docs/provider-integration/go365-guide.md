# Go365 Travel API Integration Guide

## Overview

This guide provides comprehensive instructions for integrating Go365 Travel API into your Django TravelApp multi-provider system. Go365 offers multi-language support (Thai, English, Chinese) and standard REST endpoints for tour data.

## Quick Start

### 1. Setup Provider

```bash
# Using Docker Compose
docker-compose -f docker-compose.yml run --rm web sh -c "python manage.py sync_go365 --setup-provider YOUR_API_KEY"

# Or using Django shell
python manage.py shell
>>> from wholesale.services import ProviderRegistrationService
>>> provider = ProviderRegistrationService.register_go365_provider(
...     name='Go365 Travel',
...     code='go365',
...     api_key='your-api-key',
...     default_language='en'
... )
```

### 2. Test Connection

```bash
# Test API connection
docker-compose -f docker-compose.yml run --rm web sh -c "python manage.py sync_go365 --test-connection"

# Expected output:
# ✓ Connection to Go365 API successful
```

### 3. Fetch Data

```bash
# Fetch countries only
docker-compose -f docker-compose.yml run --rm web sh -c "python manage.py sync_go365 --countries-only"

# Fetch tours only
docker-compose -f docker-compose.yml run --rm web sh -c "python manage.py sync_go365 --tours-only"

# Search for tours
docker-compose -f docker-compose.yml run --rm web sh -c "python manage.py sync_go365 --search \"europe\" --limit 5"

# Full synchronization
docker-compose -f docker-compose.yml run --rm web sh -c "python manage.py sync_go365"
```

## Dual Authentication Support

Go365 supports two authentication methods:

### 1. Simple API Key Authentication (Default)

```python
provider = ProviderRegistrationService.register_go365_provider(
    name='Go365 Travel',
    code='go365',
    api_key='your-api-key-here'
)
```

### 2. Dual Authentication: API Key + Secret Key

For enhanced security, Go365 supports HMAC signature authentication:

```python
provider = ProviderRegistrationService.register_go365_provider(
    name='Go365 Travel',
    code='go365',
    api_key='your-api-key-here',
    secret_key='your-secret-key-here'
)
```

**When both `api_key` and `secret_key` are provided**, the system automatically uses HMAC signature authentication.

#### HMAC Authentication Details

The system adds these headers to each request:

```
x-api-key: your-api-key
x-accept-language: en
x-timestamp: 1703123456
x-nonce: a1b2c3d4e5f6g7h8
x-signature: hmac-sha256-signature
x-signature-method: HMAC-SHA256
```

**Signature Generation Process:**
1. **String to Sign**: `METHOD\nENDPOINT\nTIMESTAMP\nNONCE\n[BODY]`
2. **HMAC-SHA256**: Generated using secret key
3. **Headers**: Added to each request automatically

#### Setup Dual Authentication

```bash
# Using Django shell
python manage.py shell
>>> from wholesale.services import ProviderRegistrationService
>>> provider = ProviderRegistrationService.register_go365_provider(
...     name='Go365 Travel',
...     code='go365',
...     api_key='your-api-key',
...     secret_key='your-secret-key',
...     default_language='en'
... )
```

The system will automatically detect the presence of `secret_key` and enable HMAC authentication.

## API Configuration

### Authentication Headers

#### Simple API Key (Default)

```python
headers = {
    'x-api-key': 'your-api-key',
    'x-accept-language': 'en'  # th, en, ch supported
}
```

#### HMAC Signature (Enhanced)

When `secret_key` is configured, additional headers are added:

```python
headers = {
    'x-api-key': 'your-api-key',
    'x-accept-language': 'en',
    'x-timestamp': str(int(time.time())),
    'x-nonce': generate_nonce(),
    'x-signature': generate_hmac_signature(),
    'x-signature-method': 'HMAC-SHA256'
}
```

### Available Endpoints

Based on the API documentation:

- `GET /api/v1/tours/country` - List available countries/destinations
- `GET /api/v1/tours/list` - List tours with pagination
- `GET /api/v1/tours/detail/{tour_id}` - Get tour details
- `GET /api/v1/tours/period/{tour_id}` - Get tour departure dates
- `POST /api/v1/tours/search` - Search tours with filters

### Request Parameters

**Pagination:**
- `start_page` - Page number (default: 1)
- `limit_page` - Results per page (default: 10)

**Search Filters:**
- `search` - Text search query
- `rate_start` - Minimum price filter
- `rate_end` - Maximum price filter
- `sort` - Sort options: 'price_min', 'price_max', 'name_min', 'name_max', 'date_min', 'date_max'

## Service Implementation

### Go365APIService Class

The integration uses a specific service class `Go365APIService` that extends `BaseAPIService`:

```python
class Go365APIService(BaseAPIService):
    """
    Go365 Travel API integration service.
    Supports multi-language (Thai, English, Chinese) and standard REST endpoints.
    """

    def __init__(self, provider):
        # Language configuration setup
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
```

## Data Mapping

### Country Data Normalization

```python
# Go365 specific mapping
normalized_country = {
    'provider_code': 'go365',
    'name': country.get('name', ''),
    'code': country.get('code', country.get('id', '')),
    'content': country.get('description', ''),
    'locations': country.get('cities', [])
}
```

### Tour Data Normalization

```python
# Go365 specific mapping
normalized_tour = {
    'provider_code': 'go365',
    'external_id': str(tour.get('tour_id', tour.get('id', ''))),
    'code': tour.get('tour_id', tour.get('id', '')),
    'name': tour.get('name', tour.get('title', '')),
    'description': tour.get('description', ''),
    'duration_days': tour.get('days', 0),
    'duration_nights': tour.get('nights', 0),
    'country_name': tour.get('country', ''),
    'airline_name': tour.get('airline', ''),
    'image_url': tour.get('image_url', tour.get('jpg', '')),
    'file_pdf': tour.get('pdf', ''),
    'file_word': tour.get('word', ''),
    'price': tour.get('price', tour.get('adult', 0)),
    'currency': tour.get('currency', 'USD')
}
```

## Management Command Options

The `sync_go365` management command provides comprehensive options:

```bash
# Provider Setup
--setup-provider API_KEY    # Setup Go365 provider with API key

# Testing
--test-connection           # Test API connection

# Data Syncing
--countries-only           # Sync only countries data
--tours-only              # Sync only tours data
--language {th,en,ch}      # Set API response language (default: en)

# Search Functionality
--search QUERY             # Search tours with specific query
--page PAGE               # Page number for pagination (default: 1)
--limit LIMIT             # Results per page (default: 10)
```

## Multi-Language Support

Go365 supports three languages:

- **Thai** (`th`) - For Thai market
- **English** (`en`) - Default/International
- **Chinese** (`ch`) - For Chinese market

```python
# Change language dynamically
api_service.set_language('th')

# Or set default during provider setup
ProviderRegistrationService.register_go365_provider(
    name='Go365 Travel Thailand',
    code='go365_th',
    default_language='th'
)
```

## Integration with Multi-Provider System

The Go365 integration works seamlessly with the existing multi-provider infrastructure:

### Health Monitoring

```python
from wholesale.services import ProviderHealthChecker

checker = ProviderHealthChecker()
health_status = checker.check_provider_health(go365_provider)
print(f"Go365 Health: {health_status['status']}")
```

### Synchronization

```python
from wholesale.services import MultiProviderSyncService

sync_service = MultiProviderSyncService()
result = sync_service.sync_provider(go365_provider)
print(f"Synced {result['countries']} countries, {result['trours']} tours")
```

### Data Processing

```python
from wholesale.services import ProviderDataProcessor

# Normalize Go365 data
processor = ProviderDataProcessor()
normalized_tours = processor.normalize_tours(raw_tours, 'go365')
```

## Error Handling

The integration includes comprehensive error handling:

- **Connection Errors**: Network timeouts and connection failures
- **HTTP Errors**: 404, 500, and other HTTP status codes
- **Authentication Errors**: Invalid API keys
- **Data Validation**: Malformed API responses

```python
try:
    service = Go365APIService(provider)
    tours = service.get_program_tours()
except APIConnectionError:
    logger.error("Cannot connect to Go365 API")
except APIHTTPError as e:
    logger.error(f"HTTP error: {e.status_code}")
except APIResponseError:
    logger.error("Invalid API response format")
```

## Production Considerations

### Rate Limiting

Monitor API usage to avoid rate limits. Consider implementing:

- Request throttling
- Retry mechanisms with exponential backoff
- Cache frequently accessed data

### Error Recovery

- Implement circuit breakers for repeated failures
- Log detailed error information for debugging
- Set up alerts for provider downtime

### Data Consistency

- Validate data integrity before processing
- Handle partial API failures gracefully
- Implement data reconciliation processes

## Troubleshooting

### Common Issues

1. **404 Errors on Endpoints**
   - Check if API documentation is current
   - Verify API key permissions
   - Contact Go365 support for endpoint status

2. **Authentication Failures**
   - Verify API key is valid
   - Check header format (`x-api-key`)
   - Ensure provider is active

3. **Connection Timeouts**
   - Increase timeout values
   - Check network connectivity
   - Verify base URL is correct

### Debug Mode

Enable detailed logging:

```python
import logging
logging.getLogger('wholesale.api_service').setLevel(logging.DEBUG)
```

## Next Steps

1. **API Key Acquisition**: Contact Go365 Travel for production API access
2. **Endpoint Validation**: Test all documented endpoints with real API key
3. **Data Mapping**: Refine field mappings based on actual API responses
4. **Performance Testing**: Load test with realistic data volumes
5. **Monitoring Setup**: Implement health checks and alerting

## Support

For issues related to:
- **Go365 API**: Contact Go365 Travel support
- **Integration Code**: Check Django logs and error messages
- **Multi-Provider System**: Refer to MULTI_PROVIDER_INTEGRATION.md

---

**Note**: This integration follows the same patterns as other providers in the system, ensuring consistency and maintainability across the multi-provider architecture.