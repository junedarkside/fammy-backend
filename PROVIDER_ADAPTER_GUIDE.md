# Provider Adapter Implementation Guide

**Version:** 1.0
**Last Updated:** 2025-01-03
**Target Audience:** Backend developers integrating new wholesale travel providers

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Quick Start Checklist](#quick-start-checklist)
4. [Step 1: Register Provider](#step-1-register-provider)
5. [Step 2: Create API Service](#step-2-create-api-service)
6. [Step 3: Create Data Mappers](#step-3-create-data-mappers)
7. [Step 4: Create Management Command](#step-4-create-management-command)
8. [Step 5: Test Your Adapter](#step-5-test-your-adapter)
9. [Standardization Rules](#standardization-rules)
10. [Troubleshooting](#troubleshooting)
11. [Real-World Examples](#real-world-examples)

---

## Overview

### What is a Provider Adapter?

A **Provider Adapter** is a set of components that translate external API data from a wholesale travel provider into our standardized database schema. Each provider has unique API structures, field names, and data formats - the adapter normalizes this into a common format.

### Why Use Adapters?

✅ **Separation of Concerns:** Provider-specific logic is isolated
✅ **Reusable Schema:** All providers use the same `ProgramTour` and `Period` models
✅ **Easy Maintenance:** Changes to one provider don't affect others
✅ **Consistent Frontend:** API consumers don't need to know about provider differences

### Current Providers

| Provider | Code | Status | Data Source |
|----------|------|--------|-------------|
| Zego Travel | `zego` | ✅ Active | REST API |
| Unique Inter Wholesale | `unique_inter` | ✅ Active | REST API (two-stage sync) |

---

## Architecture

### Component Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    External Provider API                     │
│                  (e.g., Zego, Unique Inter)                 │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                   API Service Layer                          │
│            (wholesale/api_service.py)                        │
│  - Handles HTTP requests                                     │
│  - Provider-specific authentication                          │
│  - Returns raw JSON responses                                │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                   Data Mapper Layer                          │
│         (wholesale/data_sync_service.py)                     │
│  - Transforms raw API data                                   │
│  - Maps to ProgramTour/Period fields                         │
│  - Standardizes pricing structure                            │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                   Database Models                            │
│              (wholesale/models.py)                           │
│  - Provider (wholesaler info)                                │
│  - ProgramTour (tour programs)                               │
│  - Period (departure dates)                                  │
│  - Country, Itinerary, Flight (related data)                 │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                   Management Command                         │
│    (wholesale/management/commands/sync_*.py)                 │
│  - Orchestrates sync process                                 │
│  - Handles errors and reporting                              │
│  - Provides CLI interface                                    │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **Fetch:** Management command calls API Service
2. **Transform:** API Service returns raw JSON
3. **Map:** Data Mapper converts to model fields
4. **Store:** Django ORM saves to database

---

## Quick Start Checklist

- [ ] Register Provider in database
- [ ] Create API Service class
- [ ] Create Tour data mapper function
- [ ] Create Period data mapper function
- [ ] Create management command
- [ ] Test with sample data
- [ ] Document API field mappings

**Estimated Time:** 2-4 hours for a standard REST API provider

---

## Step 1: Register Provider

### 1.1 Create Provider Record

Open Django shell or admin panel:

```bash
python manage.py shell
```

```python
from wholesale.models import Provider

provider = Provider.objects.create(
    name='Example Travel Wholesale',
    code='example',  # Unique identifier (lowercase, no spaces)
    base_url='https://api.example.com',
    token='your-api-key-here',  # Or leave blank if using other auth
    is_active=True,
    extra={
        # Optional: Store any provider-specific config
        'api_version': 'v2',
        'user_email': 'your-email@example.com',
        'timeout': 60
    }
)
```

### 1.2 Provider Model Fields

| Field | Type | Description | Required |
|-------|------|-------------|----------|
| `name` | CharField | Display name | ✅ Yes |
| `code` | CharField | Unique identifier (slug) | ✅ Yes |
| `base_url` | URLField | API base URL | ✅ Yes |
| `token` | CharField | API token/key | ⚠️ If using token auth |
| `is_active` | BooleanField | Enable/disable sync | ✅ Yes (default True) |
| `extra` | JSONField | Custom configuration | ❌ No |

### 1.3 Verify Registration

```bash
python manage.py shell
```

```python
from wholesale.models import Provider

# Check provider exists
provider = Provider.objects.get(code='example')
print(f"Provider: {provider.name}")
print(f"Base URL: {provider.base_url}")
print(f"Active: {provider.is_active}")
```

---

## Step 2: Create API Service

### 2.1 Create API Service Class

**File:** `wholesale/api_service.py`

Add your provider's API service class:

```python
class ExampleAPIService(BaseAPIService):
    """
    API client for Example Travel Wholesale.

    Authentication: API Key in header
    Base URL: https://api.example.com
    """

    def _setup_authentication(self):
        """Setup API key authentication"""
        if self.token:
            self.session.headers.update({
                'X-API-Key': self.token,  # Adjust header name as needed
                'Authorization': f'Bearer {self.token}'  # Or use Bearer token
            })

    def get_countries(self) -> Optional[List[Dict]]:
        """
        Fetch all countries from provider.

        Returns:
            List of country dicts or None if request fails
        """
        return self._make_request('countries')

    def get_program_tours(self, country_code: Optional[str] = None) -> Optional[List[Dict]]:
        """
        Fetch all tour programs.

        Args:
            country_code: Optional filter by country

        Returns:
            List of tour program dicts or None if request fails
        """
        params = {}
        if country_code:
            params['country'] = country_code

        return self._make_request('tours', params=params)

    def get_program_tour_details(self, tour_id: str) -> Optional[Dict]:
        """
        Fetch detailed information for a specific tour.

        Args:
            tour_id: External tour ID from provider

        Returns:
            Tour detail dict or None if request fails
        """
        return self._make_request(f'tours/{tour_id}')

    def get_departures(self, tour_id: str) -> Optional[List[Dict]]:
        """
        Fetch departure dates (periods) for a tour.

        Args:
            tour_id: External tour ID from provider

        Returns:
            List of departure dicts or None if request fails
        """
        return self._make_request(f'tours/{tour_id}/departures')
```

### 2.2 Register in APIServiceFactory

Find the `APIServiceFactory.create_service()` method in `api_service.py` and add your provider:

```python
class APIServiceFactory:
    @staticmethod
    def create_service(provider) -> Optional[BaseAPIService]:
        """Factory method to create appropriate API service based on provider code"""
        service_map = {
            'zego': ZegoAPIService,
            'unique_inter': UniqueInterAPIService,
            'example': ExampleAPIService,  # Add your provider here
        }

        service_class = service_map.get(provider.code)
        if service_class:
            return service_class(provider)
        else:
            logger.warning(f"No API service found for provider: {provider.code}")
            return None
```

### 2.3 Authentication Patterns

**API Key in Header:**
```python
def _setup_authentication(self):
    self.session.headers.update({
        'X-API-Key': self.token
    })
```

**Bearer Token:**
```python
def _setup_authentication(self):
    self.session.headers.update({
        'Authorization': f'Bearer {self.token}'
    })
```

**Basic Auth:**
```python
def _setup_authentication(self):
    from requests.auth import HTTPBasicAuth
    username = self.provider.extra.get('username', '')
    password = self.token
    self.session.auth = HTTPBasicAuth(username, password)
```

**Custom Auth (e.g., OAuth):**
```python
def _setup_authentication(self):
    # Implement OAuth flow
    token = self._get_oauth_token()
    self.session.headers.update({
        'Authorization': f'Bearer {token}'
    })

def _get_oauth_token(self):
    # OAuth token retrieval logic
    pass
```

---

## Step 3: Create Data Mappers

### 3.1 Create Tour Mapper Function

**File:** `wholesale/data_sync_service.py`

Add a function to map tour data:

```python
def map_example_tour_data(raw_data: Dict) -> Dict:
    """
    Map Example provider tour data to ProgramTour model fields.

    Args:
        raw_data: Raw JSON from Example API

    Returns:
        dict: Mapped data ready for ProgramTour.objects.update_or_create()

    Example raw_data structure:
    {
        "tour_id": "EX12345",
        "tour_code": "EXAMPLE-TOUR-001",
        "tour_name": "Amazing Thailand 7 Days",
        "duration": "7D6N",
        "country": "Thailand",
        "description": "Explore the wonders...",
        "image": "https://example.com/tours/thailand.jpg",
        "price_from": 50000
    }
    """
    # Extract duration (e.g., "7D6N" -> days=7, nights=6)
    duration = raw_data.get('duration', '')
    days = 0
    nights = 0

    if 'D' in duration and 'N' in duration:
        try:
            parts = duration.split('D')
            days = int(parts[0])
            nights = int(parts[1].replace('N', ''))
        except (ValueError, IndexError):
            logger.warning(f"Could not parse duration: {duration}")

    # Extract country name
    country_name = raw_data.get('country', '').strip()

    # Get or create Country object
    from wholesale.models import Country
    country_obj = None
    if country_name:
        country_obj, _ = Country.objects.get_or_create(
            provider=None,  # Will be set by caller
            name=country_name,
            defaults={
                'iso_code': '',  # Map if available
            }
        )

    return {
        'external_id': str(raw_data.get('tour_id', '')),
        'code': raw_data.get('tour_code', ''),
        'name': raw_data.get('tour_name', ''),
        'days': days,
        'nights': nights,
        'country': country_obj,
        'country_name': country_name,
        'highlight': raw_data.get('description', ''),
        'image_url': raw_data.get('image', ''),
        'airline_name': raw_data.get('airline', ''),
        'file_pdf': raw_data.get('pdf_url', ''),
        'file_word': raw_data.get('doc_url', ''),
        'last_synced': timezone.now(),
    }
```

### 3.2 Create Period Mapper Function

**CRITICAL:** Follow the standardized pricing structure!

```python
def map_example_period_data(raw_data: Dict) -> Dict:
    """
    Map Example provider departure data to Period model fields.

    Args:
        raw_data: Raw JSON from Example API

    Returns:
        dict: Mapped data ready for Period.objects.update_or_create()

    Example raw_data structure:
    {
        "departure_id": "DEP12345",
        "departure_code": "EX-2025-01-15",
        "start_date": "2025-01-15",
        "end_date": "2025-01-21",
        "airline": "Thai Airways",
        "airline_code": "TG",
        "total_seats": 30,
        "booked_seats": 15,
        "available_seats": 15,
        "status": "Available",
        "pricing": {
            "adult": 50000,
            "child_with_bed": 40000,
            "child_no_bed": 35000,
            "infant": 10000,
            "single_supplement": 8000,
            "twin_room": 5000,
            "visa_fee": 2500
        },
        "deposit": 15000,
        "commission": {
            "agent": 2500,
            "sale": 1500
        }
    }
    """
    pricing = raw_data.get('pricing', {})
    commission = raw_data.get('commission', {})

    # IMPORTANT: Use standardized pricing keys (12 keys)
    base_prices = {
        'adult': int(pricing.get('adult', 0)),
        'child': int(pricing.get('child_with_bed', 0)),
        'child_nb': int(pricing.get('child_no_bed', 0)),
        'infant': int(pricing.get('infant', 0)),
        'single_bed': int(pricing.get('single_supplement', 0)),  # Use 'single_bed', not 'single'
        'twin_bed': int(pricing.get('twin_room', 0)),
        'double_bed': int(pricing.get('double_room', 0)),
        'triple_bed': int(pricing.get('triple_room', 0)),
        'join_land': int(pricing.get('land_only', 0)),
        'single_visa': int(pricing.get('visa_fee', 0)),
        'group_visa': int(pricing.get('group_visa', 0)),
        'express_visa': int(pricing.get('express_visa', 0)),
    }

    # If provider has promotional pricing, map to end_prices
    # Otherwise, copy base_prices
    end_prices = base_prices.copy()

    # Calculate available seats
    total_seats = int(raw_data.get('total_seats', 0))
    booked = int(raw_data.get('booked_seats', 0))
    available = total_seats - booked

    # Map status
    status = raw_data.get('status', '')
    if available <= 0:
        status = 'Soldout'
    elif available <= 5:
        status = 'Waitlist'
    else:
        status = 'Book'

    return {
        'external_id': str(raw_data.get('departure_id', '')),
        'code': raw_data.get('departure_code', ''),
        'start_date': raw_data.get('start_date'),
        'end_date': raw_data.get('end_date'),
        'bus': raw_data.get('bus_type', ''),
        'country_name': raw_data.get('country', ''),
        'airline_code': raw_data.get('airline_code', ''),
        'airline_name': raw_data.get('airline', ''),
        'airport': raw_data.get('departure_airport', ''),
        'group_size': total_seats,
        'booked': booked,
        'seats': available,
        'status': status,
        'promotion': raw_data.get('promotion_code', ''),
        'base_prices': base_prices,  # Standardized structure
        'end_prices': end_prices,
        'deposit': raw_data.get('deposit', 0),
        'deposit_end': raw_data.get('deposit', 0),  # Or promotional deposit
        'com_agent': commission.get('agent', 0),
        'com_agent_end': commission.get('agent', 0),
        'com_sale': commission.get('sale', 0),
        'com_sale_end': commission.get('sale', 0),
        'update_date': timezone.now(),
    }
```

### 3.3 Helper Functions

Add utility functions for data cleaning:

```python
def clean_example_price(value: Any) -> int:
    """
    Clean price values from Example provider.

    Handles: strings, floats, None, empty values
    """
    if value is None or value == '':
        return 0

    try:
        # Remove currency symbols and commas
        if isinstance(value, str):
            value = value.replace(',', '').replace('฿', '').replace('$', '').strip()
        return int(float(value))
    except (ValueError, TypeError):
        logger.warning(f"Could not parse price value: {value}")
        return 0

def clean_example_date(value: str) -> Optional[str]:
    """
    Clean and standardize date values.

    Converts various formats to YYYY-MM-DD
    """
    if not value:
        return None

    try:
        # Try parsing common formats
        from datetime import datetime

        # Format: "15/01/2025" -> "2025-01-15"
        if '/' in value:
            dt = datetime.strptime(value, '%d/%m/%Y')
            return dt.strftime('%Y-%m-%d')

        # Format: "2025-01-15" (already correct)
        if '-' in value and len(value) == 10:
            return value

        return None
    except ValueError:
        logger.warning(f"Could not parse date: {value}")
        return None
```

---

## Step 4: Create Management Command

### 4.1 Create Command File

**File:** `wholesale/management/commands/sync_example.py`

```python
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from wholesale.models import Provider, ProgramTour, Period
from wholesale.api_service import APIServiceFactory
from wholesale.data_sync_service import (
    map_example_tour_data,
    map_example_period_data,
)
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Sync data from Example Travel Wholesale API'

    def add_arguments(self, parser):
        parser.add_argument(
            '--provider-code',
            type=str,
            default='example',
            help='Provider code (default: example)'
        )
        parser.add_argument(
            '--tours-only',
            action='store_true',
            help='Only sync tours, skip periods'
        )
        parser.add_argument(
            '--periods-only',
            action='store_true',
            help='Only sync periods for existing tours'
        )
        parser.add_argument(
            '--tour-id',
            type=str,
            help='Sync specific tour only'
        )

    def handle(self, *args, **options):
        provider_code = options['provider_code']

        # Get provider
        try:
            provider = Provider.objects.get(code=provider_code)
        except Provider.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(
                    f'Provider "{provider_code}" not found. Please create it first.'
                )
            )
            return

        if not provider.is_active:
            self.stdout.write(
                self.style.WARNING(
                    f'Provider "{provider_code}" is not active. Enable it first.'
                )
            )
            return

        # Create API service
        api_service = APIServiceFactory.create_service(provider)
        if not api_service:
            self.stdout.write(
                self.style.ERROR(f'Could not create API service for {provider_code}')
            )
            return

        # Sync tours (unless --periods-only)
        if not options['periods_only']:
            self.sync_tours(provider, api_service, options.get('tour_id'))

        # Sync periods (unless --tours-only)
        if not options['tours_only']:
            self.sync_periods(provider, api_service, options.get('tour_id'))

        self.stdout.write(
            self.style.SUCCESS(f'✓ Sync completed for {provider.name}')
        )

    @transaction.atomic
    def sync_tours(self, provider, api_service, tour_id_filter=None):
        """Sync tour programs"""
        self.stdout.write(
            self.style.WARNING('Syncing tour programs...')
        )

        # Fetch tours
        if tour_id_filter:
            raw_data = api_service.get_program_tour_details(tour_id_filter)
            raw_tours = [raw_data] if raw_data else []
        else:
            raw_tours = api_service.get_program_tours()

        if not raw_tours:
            self.stdout.write(
                self.style.WARNING('No tours found')
            )
            return

        tours_created = 0
        tours_updated = 0
        errors = 0

        for raw_tour in raw_tours:
            try:
                tour_data = map_example_tour_data(raw_tour)
                external_id = tour_data.pop('external_id')

                tour, created = ProgramTour.objects.update_or_create(
                    provider=provider,
                    external_id=external_id,
                    defaults=tour_data
                )

                if created:
                    tours_created += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'  ✓ Created: {tour.name}')
                    )
                else:
                    tours_updated += 1

            except Exception as e:
                errors += 1
                logger.error(f"Error syncing tour: {e}")
                self.stdout.write(
                    self.style.ERROR(f'  ✗ Error: {str(e)}')
                )

        self.stdout.write('')
        self.stdout.write(f'Tours created: {tours_created}')
        self.stdout.write(f'Tours updated: {tours_updated}')
        if errors > 0:
            self.stdout.write(
                self.style.ERROR(f'Errors: {errors}')
            )

    @transaction.atomic
    def sync_periods(self, provider, api_service, tour_id_filter=None):
        """Sync departure periods"""
        self.stdout.write('')
        self.stdout.write(
            self.style.WARNING('Syncing departure periods...')
        )

        # Get tours to sync periods for
        queryset = ProgramTour.objects.filter(provider=provider)
        if tour_id_filter:
            queryset = queryset.filter(external_id=tour_id_filter)

        if not queryset.exists():
            self.stdout.write(
                self.style.WARNING('No tours found to sync periods')
            )
            return

        periods_created = 0
        periods_updated = 0
        errors = 0

        for tour in queryset:
            try:
                # Fetch departures for this tour
                raw_departures = api_service.get_departures(tour.external_id)

                if not raw_departures:
                    continue

                for raw_departure in raw_departures:
                    try:
                        period_data = map_example_period_data(raw_departure)
                        external_id = period_data.pop('external_id')

                        period, created = Period.objects.update_or_create(
                            provider=provider,
                            external_id=external_id,
                            program=tour,
                            defaults=period_data
                        )

                        if created:
                            periods_created += 1
                        else:
                            periods_updated += 1

                    except Exception as e:
                        errors += 1
                        logger.error(f"Error syncing period: {e}")

            except Exception as e:
                errors += 1
                logger.error(f"Error syncing periods for tour {tour.code}: {e}")

        self.stdout.write('')
        self.stdout.write(f'Periods created: {periods_created}')
        self.stdout.write(f'Periods updated: {periods_updated}')
        if errors > 0:
            self.stdout.write(
                self.style.ERROR(f'Errors: {errors}')
            )
```

### 4.2 Command Usage Examples

```bash
# Full sync (tours + periods)
python manage.py sync_example

# Sync tours only
python manage.py sync_example --tours-only

# Sync periods only
python manage.py sync_example --periods-only

# Sync specific tour
python manage.py sync_example --tour-id EX12345

# Use custom provider code
python manage.py sync_example --provider-code example_v2
```

---

## Step 5: Test Your Adapter

### 5.1 Test API Connection

```bash
python manage.py shell
```

```python
from wholesale.models import Provider
from wholesale.api_service import APIServiceFactory

# Get provider
provider = Provider.objects.get(code='example')

# Create API service
api_service = APIServiceFactory.create_service(provider)

# Test connection
if api_service.test_connection():
    print("✓ API connection successful")
else:
    print("✗ API connection failed")

# Test data fetch
tours = api_service.get_program_tours()
print(f"Fetched {len(tours)} tours")
print(f"Sample tour: {tours[0]}")
```

### 5.2 Test Data Mapping

```python
from wholesale.data_sync_service import map_example_tour_data, map_example_period_data

# Test tour mapping
sample_tour = {
    "tour_id": "EX12345",
    "tour_code": "EXAMPLE-001",
    "tour_name": "Test Tour",
    "duration": "7D6N",
    "country": "Thailand"
}

mapped_tour = map_example_tour_data(sample_tour)
print("Mapped tour data:")
print(mapped_tour)

# Test period mapping
sample_period = {
    "departure_id": "DEP001",
    "start_date": "2025-01-15",
    "end_date": "2025-01-21",
    "pricing": {"adult": 50000, "single_supplement": 8000}
}

mapped_period = map_example_period_data(sample_period)
print("Mapped period data:")
print(mapped_period['base_prices'])
```

### 5.3 Test Full Sync

```bash
# Dry run: Check what would be synced
python manage.py sync_example --tour-id EX12345

# Check database
python manage.py shell
```

```python
from wholesale.models import ProgramTour, Period

# Verify tour was created
tour = ProgramTour.objects.get(code='EXAMPLE-001')
print(f"Tour: {tour.name}")
print(f"Days: {tour.days}, Nights: {tour.nights}")

# Verify periods
periods = Period.objects.filter(program=tour)
print(f"Periods: {periods.count()}")

# Check pricing structure
if periods.exists():
    period = periods.first()
    print(f"Base prices: {period.base_prices}")
    print(f"Has standard keys: {'single_bed' in period.base_prices}")
```

### 5.4 Validation Checklist

- [ ] API service connects successfully
- [ ] Tours are created/updated correctly
- [ ] Periods are linked to correct tours
- [ ] Pricing JSON has all 12 standardized keys
- [ ] Dates are in YYYY-MM-DD format
- [ ] Available seats calculated correctly
- [ ] No duplicate records (check `unique_together`)
- [ ] Error handling works for invalid data

---

## Standardization Rules

### Critical: Pricing Structure

**ALL providers MUST use these 12 pricing keys:**

```python
base_prices = {
    'adult': int,           # Adult price
    'child': int,           # Child with bed
    'child_nb': int,        # Child no bed
    'infant': int,          # Infant price
    'single_bed': int,      # Single room supplement (NOT 'single')
    'twin_bed': int,        # Twin room supplement
    'double_bed': int,      # Double room supplement
    'triple_bed': int,      # Triple room supplement
    'join_land': int,       # Land-only package
    'single_visa': int,     # Individual visa fee
    'group_visa': int,      # Group visa fee
    'express_visa': int,    # Express visa fee
}
```

**If your provider doesn't have a field, set it to `0`**

❌ **WRONG:**
```python
base_prices = {
    'adult': 50000,
    'single': 8000,  # Wrong key name
}
```

✅ **CORRECT:**
```python
base_prices = {
    'adult': 50000,
    'child': 0,
    'child_nb': 0,
    'infant': 0,
    'single_bed': 8000,  # Correct key name
    'twin_bed': 0,
    'double_bed': 0,
    'triple_bed': 0,
    'join_land': 0,
    'single_visa': 0,
    'group_visa': 0,
    'express_visa': 0,
}
```

### Date Format

**Always use:** `YYYY-MM-DD` (ISO 8601)

```python
'start_date': '2025-01-15',  # ✅ Correct
'start_date': '15/01/2025',  # ❌ Wrong
'start_date': '01-15-2025',  # ❌ Wrong
```

### External IDs

**Must be unique per provider:**

```python
# Good: Use provider's unique identifier
'external_id': 'EX12345'

# Bad: Using non-unique field
'external_id': 'Thailand Tour'  # Multiple tours could have same name
```

### Nullable Fields

**Set to empty string or 0 if not provided:**

```python
'airline_code': raw_data.get('airline_code', ''),  # Empty string for missing text
'bus': '',  # Empty if not provided
'airport': '',
'group_size': int(raw_data.get('seats', 0)),  # 0 for missing numbers
```

### Country Handling

**Prefer Country FK over country_name:**

```python
# Good: Create Country object
country_obj, _ = Country.objects.get_or_create(
    provider=provider,
    name=country_name,
    defaults={'iso_code': 'THA'}
)
tour_data['country'] = country_obj

# Acceptable: Store name only if Country not available
tour_data['country'] = None
tour_data['country_name'] = country_name
```

---

## Troubleshooting

### Issue: "Provider not found"

**Cause:** Provider not registered in database

**Solution:**
```python
from wholesale.models import Provider
Provider.objects.create(
    name='Example Travel',
    code='example',
    base_url='https://api.example.com',
    token='your-token'
)
```

### Issue: "No API service found for provider"

**Cause:** API service class not registered in `APIServiceFactory`

**Solution:** Add your service class to the factory's `service_map` dictionary in `wholesale/api_service.py`

### Issue: "UNIQUE constraint failed"

**Cause:** Trying to create duplicate record with same `provider + external_id`

**Solution:**
- Verify `external_id` is truly unique in provider's API
- Use `update_or_create()` instead of `create()`
- Check for duplicate data in API response

### Issue: "KeyError: 'single_bed'"

**Cause:** Frontend/API expecting standardized pricing keys

**Solution:** Ensure your mapper includes all 12 pricing keys (set missing ones to 0)

### Issue: "Invalid date format"

**Cause:** Date not in YYYY-MM-DD format

**Solution:** Add date cleaning function:
```python
def clean_example_date(value: str) -> str:
    from datetime import datetime
    if '/' in value:
        dt = datetime.strptime(value, '%d/%m/%Y')
        return dt.strftime('%Y-%m-%d')
    return value
```

### Issue: "Request timeout"

**Cause:** API is slow or unresponsive

**Solution:**
- Increase timeout in `_make_request()` call
- Add retry logic
- Check provider's API status
- Use pagination if API supports it

### Issue: "Authentication failed"

**Cause:** Invalid token or wrong auth method

**Solution:**
- Verify token in Provider model
- Check `_setup_authentication()` method
- Test API with curl/Postman first
- Check API documentation for correct auth headers

---

## Real-World Examples

### Example 1: Zego Provider (Standard REST API)

**API Structure:** Straightforward REST endpoints

**Authentication:** API token in header

**Key Features:**
- Separate endpoints for tours and periods
- Rich pricing structure (12 price types)
- Well-structured JSON responses

**Implementation:**
- **API Service:** `ZegoAPIService` in `api_service.py`
- **Mappers:** `transform_pricing_data()`, `_sync_periods()` in `data_sync_service.py`
- **Command:** `sync_zego_data` management command

**Usage:**
```bash
python manage.py sync_zego_data
python manage.py sync_zego_data --wholesaler "Zego Travel"
python manage.py sync_zego_data --tours-only
```

### Example 2: Unique Inter Provider (Two-Stage Sync)

**API Structure:** Departure-centric (not tour-centric)

**Authentication:** Email-based API key

**Key Features:**
- Categories (destinations) instead of countries
- Each API record = one departure date
- Raw data stored before processing (two-stage)

**Implementation:**
- **API Service:** `UniqueInterAPIService` in `api_service.py`
- **Raw Storage:** `RawVendorData` model for preserving original API responses
- **Mappers:** `map_unique_inter_tour_data()`, `map_unique_inter_period_data()` in `data_sync_service.py`
- **Commands:**
  - `sync_unique_inter_categories` - Discover available categories
  - `sync_unique_inter` - Two-stage sync (fetch → process)

**Usage:**
```bash
# First time setup
python manage.py sync_unique_inter_categories

# Full sync
python manage.py sync_unique_inter

# Fetch only (store raw data)
python manage.py sync_unique_inter --fetch-only

# Process only (map existing raw data)
python manage.py sync_unique_inter --process-only

# Sync specific category
python manage.py sync_unique_inter --category 64
```

**When to use two-stage sync:**
- API responses are complex/nested
- Need to preserve original data for debugging
- Data cleaning logic may need refinement
- Provider data format changes frequently

---

## Advanced Topics

### Custom Category Management

If your provider uses categories/regions:

```python
from wholesale.models import ProviderCategory

# Create categories
ProviderCategory.objects.create(
    provider=provider,
    category_id='asia',
    name='Asia Tours',
    is_active=True,
    priority=1
)

# In your command
def handle(self, *args, **options):
    categories = ProviderCategory.objects.filter(
        provider=provider,
        is_active=True
    ).order_by('-priority')

    for category in categories:
        tours = api_service.get_tours(category=category.category_id)
        # ... sync tours
```

### Incremental Sync

Only sync updated records:

```python
def sync_tours(self, provider, api_service):
    # Get last sync time
    last_sync = provider.last_synced or timezone.now() - timedelta(days=30)

    # Fetch only updated tours
    raw_tours = api_service.get_program_tours(updated_since=last_sync)

    # ... sync process

    # Update last sync time
    provider.last_synced = timezone.now()
    provider.save()
```

### Error Recovery

Store failed records for retry:

```python
from wholesale.models import RawVendorData

def sync_with_error_recovery(self, provider, raw_data):
    try:
        # Attempt to process
        tour_data = map_example_tour_data(raw_data)
        tour, _ = ProgramTour.objects.update_or_create(...)

    except Exception as e:
        # Store for later retry
        RawVendorData.objects.create(
            provider=provider,
            external_id=raw_data.get('tour_id'),
            raw_json=raw_data,
            processed=False,
            error_message=str(e)
        )
        logger.error(f"Failed to sync: {e}")
```

---

## Appendix: Model Reference

### ProgramTour Model Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `external_id` | CharField | ✅ | Provider's tour ID (unique per provider) |
| `code` | CharField | ✅ | Tour code/SKU |
| `name` | CharField | ✅ | Tour name |
| `days` | IntegerField | ❌ | Duration in days |
| `nights` | IntegerField | ❌ | Duration in nights |
| `country` | ForeignKey | ❌ | Country object (preferred) |
| `country_name` | CharField | ❌ | Country name string (fallback) |
| `highlight` | TextField | ❌ | Tour highlights/description |
| `image_url` | URLField | ❌ | Main tour image |
| `airline_name` | CharField | ❌ | Default airline |
| `file_pdf` | URLField | ❌ | PDF itinerary URL |
| `file_word` | URLField | ❌ | Word document URL |
| `last_synced` | DateTimeField | ✅ | Last sync timestamp |

### Period Model Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `external_id` | CharField | ✅ | Provider's departure ID (unique per provider) |
| `program` | ForeignKey | ✅ | Related ProgramTour |
| `code` | CharField | ✅ | Period code |
| `start_date` | DateField | ✅ | Departure date |
| `end_date` | DateField | ✅ | Return date |
| `airline_name` | CharField | ❌ | Airline for this departure |
| `airline_code` | CharField | ❌ | Airline code |
| `group_size` | IntegerField | ❌ | Total group capacity |
| `booked` | IntegerField | ❌ | Number of bookings |
| `seats` | IntegerField | ❌ | Available seats |
| `status` | CharField | ❌ | Booking status (Book/Waitlist/Soldout) |
| `base_prices` | JSONField | ✅ | Base pricing (12 keys) |
| `end_prices` | JSONField | ✅ | Promotional pricing (12 keys) |
| `deposit` | DecimalField | ❌ | Deposit amount |
| `com_agent` | DecimalField | ❌ | Agent commission |
| `com_sale` | DecimalField | ❌ | Sales commission |

---

## Summary Checklist

When creating a new provider adapter, ensure you have:

- [ ] Registered Provider in database with correct credentials
- [ ] Created API Service class extending `BaseAPIService`
- [ ] Implemented authentication in `_setup_authentication()`
- [ ] Registered API service in `APIServiceFactory`
- [ ] Created tour data mapper with all required fields
- [ ] Created period data mapper with **standardized 12-key pricing**
- [ ] Created management command with proper error handling
- [ ] Tested API connection and data mapping
- [ ] Documented API field mappings in code comments
- [ ] Verified no duplicate records are created
- [ ] Confirmed dates are in YYYY-MM-DD format
- [ ] Tested full sync with real API data

**Estimated Development Time:** 2-4 hours for standard REST API

**Need Help?** Review the Zego and Unique Inter implementations as reference examples.

---

**Document Version:** 1.0
**Last Updated:** 2025-01-03
**Maintainer:** Backend Development Team
