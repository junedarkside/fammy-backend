# Provider Integration Guide

## Quick Start

This guide shows how to integrate a new tour operator/provider with the TravelApp B2B platform.

## Current Implementation Status

The provider integration system is **under development**. The base patterns are established, but data models are being refined.

### What's Working
- `BaseAPIService` class for common API operations
- `APIServiceFactory` for service creation
- Management command structure

### What's Being Developed
- Database models for tours and periods
- Data synchronization services
- Error handling and retry logic

## Integration Steps

### 1. Register Provider

```python
# In Django admin or shell
from wholesale.models import Provider

provider = Provider.objects.create(
    name='Your Tour Operator Name',
    code='your_operator',  # unique identifier
    base_url='https://api.youroperator.com',
    token='your-api-token-here',
    is_active=True
)
```

### 2. Create API Service

Extend `BaseAPIService` for your provider:

```python
# wholesale/api_service.py

class YourOperatorAPIService(BaseAPIService):
    """
    API service for Your Tour Operator
    """

    def _setup_authentication(self):
        """Setup API authentication"""
        if self.token:
            self.session.headers.update({
                'Authorization': f'Bearer {self.token}'
            })

    def get_countries(self):
        """Fetch available countries"""
        return self._make_request('countries')

    def get_tours(self, country_code=None):
        """Fetch tour programs"""
        params = {}
        if country_code:
            params['country'] = country_code
        return self._make_request('tours', params=params)

    def get_departures(self, tour_id):
        """Fetch departure dates for a tour"""
        return self._make_request(f'tours/{tour_id}/departures')
```

### 3. Register Service

Add your service to the factory:

```python
# In APIServiceFactory.create_service()

service_map = {
    'zego': ZegoAPIService,
    'unique_inter': UniqueInterAPIService,
    'your_operator': YourOperatorAPIService,  # Add this line
}
```

### 4. Test Connection

```python
# Test in Django shell
from wholesale.models import Provider
from wholesale.api_service import APIServiceFactory

provider = Provider.objects.get(code='your_operator')
service = APIServiceFactory.create_service(provider)

# Test API connection
countries = service.get_countries()
print(f"Found {len(countries)} countries")
```

## Data Mapping

When the data models are finalized, you'll create mapping functions to convert API responses to Django models.

```python
# Example mapping (when models are ready)

def map_your_operator_tour(raw_data):
    """Convert API data to ProgramTour model fields"""
    return {
        'external_id': raw_data['tour_id'],
        'name': raw_data['tour_name'],
        'duration_days': extract_days(raw_data['duration']),
        'country': get_or_create_country(raw_data['country']),
        # ... other fields
    }

def map_your_operator_period(raw_data):
    """Convert API data to Period model fields"""
    return {
        'external_id': raw_data['departure_id'],
        'start_date': raw_data['start_date'],
        'end_date': raw_data['end_date'],
        'price': raw_data['price'],
        'available_seats': raw_data['available'],
        # ... other fields
    }
```

## Travel Industry Context

### Tour Operators vs Wholesalers
- **Tour Operators**: Create and operate tour packages
- **Wholesalers**: B2B entities selling to travel agencies
- **This Platform**: Connects both through standardized APIs

### Data Models (When Implemented)
- **ProgramTour**: Tour package information
- **Period**: Specific departure dates with pricing
- **Country**: Destination countries with normalization
- **Provider**: Tour operator information

### Pricing Structure
Travel industry typically uses:
- Adult/Child/Infant pricing
- Single supplements
- Room type adjustments
- Optional services (visas, insurance)

## Current Limitations

### Under Development
- Database models are commented out during refinement
- Data synchronization is being implemented
- Error handling needs improvement

### Recommendations
1. **Wait for Models**: Final database models are being refined
2. **Start API Service**: You can implement API service layer now
3. **Test Integration**: Use test endpoints to verify connectivity
4. **Follow Patterns**: Use existing Zego/Unique Inter as examples

## Common Patterns

### Authentication Methods
```python
# Bearer Token
self.session.headers.update({
    'Authorization': f'Bearer {self.token}'
})

# API Key
self.session.headers.update({
    'X-API-Key': self.token
})

# Basic Auth
from requests.auth import HTTPBasicAuth
self.session.auth = HTTPBasicAuth(username, self.token)
```

### Error Handling
```python
def get_data(self):
    try:
        response = self._make_request('tours')
        return response
    except requests.exceptions.Timeout:
        logger.error("API timeout")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"API error: {e}")
        return None
```

### Pagination
```python
def get_all_tours(self):
    all_tours = []
    page = 1

    while True:
        response = self._make_request('tours', params={'page': page})
        if not response.get('tours'):
            break
        all_tours.extend(response['tours'])
        page += 1

    return all_tours
```

## Getting Help

1. **Check Existing Implementations**: Review Zego and Unique Inter services
2. **Test API First**: Use curl/Postman to verify API endpoints
3. **Log Everything**: Add logging for debugging
4. **Start Simple**: Implement basic functionality first

## Next Steps

1. **Wait for Model Finalization**: Database models are being refined
2. **Implement API Service**: Create your service class
3. **Test Integration**: Verify API connectivity
4. **Prepare Data Mapping**: Plan your data transformation logic

---

**Note**: This guide reflects the current development state. As the platform evolves, this documentation will be updated with concrete implementation details.